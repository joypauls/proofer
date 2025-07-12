import click
import difflib
import re
from pathlib import Path
from typing import TypedDict, Any
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text
from openai import OpenAI
import langgraph
from langgraph.graph import StateGraph

TEST_WITHOUT_ERRORS = "./tests/files/test_without_errors.md"
TEST_WITH_ERRORS = "./tests/files/test_with_errors.md"

client = OpenAI()
console = Console()


class AgentState(TypedDict):
    path: str
    original_text: str
    llm_response: str
    corrected_text: str
    diff_lines: list[str]
    approved: bool
    auto_approve: bool
    has_corrections: bool


def load_file_node(state: AgentState) -> AgentState:
    path = state["path"]
    text = Path(path).read_text(encoding="utf-8")
    return {**state, "original_text": text}


def call_openai_node(state: AgentState) -> AgentState:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful markdown proofreader. Your task is to fix spelling errors in the text. "
                    "IMPORTANT RULES: "
                    "1. Always return the COMPLETE original text with spelling corrections applied "
                    "2. Do not make any formatting changes, do not add or remove whitespace "
                    "3. Do not change line breaks, punctuation, or structure "
                    "4. Only fix misspelled words by replacing them with correct spelling "
                    "5. If there are no spelling errors, return the original text exactly as provided "
                    "6. Never return partial text or summaries - always return the full document"
                ),
            },
            {"role": "user", "content": state["original_text"]},
        ],
        temperature=0,
    )
    suggestions = response.choices[0].message.content
    original_text = state["original_text"]

    def extract_words(text: str) -> list[str]:
        if not text:
            return []

        words = re.findall(r"\b\w+\b", text.lower())
        return words

    def has_spelling_corrections(original: str, suggested: str) -> bool:
        if not suggested or not suggested.strip():
            return False

        original_words = extract_words(original)
        suggested_words = extract_words(suggested)

        print(f"Original words: {original_words}")
        print(f"Suggested words: {suggested_words}")

        # Since we're now getting the full text back, word counts should match
        if len(original_words) != len(suggested_words):
            print(
                f"Word count mismatch: {len(original_words)} vs {len(suggested_words)}"
            )
            return False

        # Check if any words are actually different
        has_diffs = any(
            orig != sugg for orig, sugg in zip(original_words, suggested_words)
        )
        print(f"Has spelling differences: {has_diffs}")
        return has_diffs

    has_corrections = has_spelling_corrections(original_text, suggestions)

    if has_corrections and suggestions:
        # remove trailing whitespace from each line to prevent formatting artifacts
        corrected_lines = []
        for line in suggestions.splitlines():
            corrected_lines.append(line.rstrip())

        if original_text.endswith("\n"):
            suggestions = "\n".join(corrected_lines) + "\n"
        else:
            suggestions = "\n".join(corrected_lines)

    if not has_corrections:
        suggestions = ""

    return {**state, "llm_response": suggestions, "has_corrections": has_corrections}


def compute_diff_node(state: AgentState) -> AgentState:
    original = state["original_text"].splitlines(keepends=True)
    corrected = state["llm_response"].splitlines(keepends=True)
    diff = list(
        difflib.unified_diff(
            original, corrected, fromfile="original", tofile="suggested"
        )
    )
    return {**state, "corrected_text": "".join(corrected), "diff_lines": diff}


def print_diff_node(state: AgentState) -> AgentState:
    original_text = state["original_text"]
    corrected_text = state["llm_response"]

    def find_word_changes(original: str, corrected: str) -> list[dict[str, str]]:
        # extract words with their positions
        original_words = re.findall(r"\b\w+\b", original.lower())
        corrected_words = re.findall(r"\b\w+\b", corrected.lower())

        # find differences using difflib
        changes = []
        matcher = difflib.SequenceMatcher(None, original_words, corrected_words)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                for k in range(i2 - i1):
                    if i1 + k < len(original_words) and j1 + k < len(corrected_words):
                        orig_word = original_words[i1 + k]
                        corr_word = corrected_words[j1 + k]
                        if orig_word != corr_word:
                            changes.append(
                                {"original": orig_word, "corrected": corr_word}
                            )

        return changes

    changes = find_word_changes(original_text, corrected_text)

    if not changes:
        console.print("[green]✓ No spelling errors found![/]")
        return state

    # print header
    console.print(f"\n[bold yellow]📝 Found {len(changes)} spelling correction(s):[/]")
    console.print()

    # print each change with highlighting
    for i, change in enumerate(changes, 1):
        console.print(
            f"  {i}. [red bold]{change['original']}[/] → [green bold]{change['corrected']}[/]"
        )

    console.print()

    # print the diff with better formatting
    original_lines = original_text.splitlines()
    corrected_lines = corrected_text.splitlines()

    console.print("[bold blue]📄 Preview of changes:[/]")
    console.print()

    # show only the lines that changed with context
    for i, (orig_line, corr_line) in enumerate(zip(original_lines, corrected_lines), 1):
        if orig_line.strip() != corr_line.strip():
            # show line number and context
            console.print(f"[dim]Line {i}:[/]")

            # create highlighted versions using Rich Text objects
            orig_text = Text(orig_line)
            corr_text = Text(corr_line)

            # apply highlighting by finding word positions
            for change in changes:
                # find all occurrences of the word in the line (case-insensitive)
                orig_pattern = re.compile(
                    r"\b" + re.escape(change["original"]) + r"\b", re.IGNORECASE
                )
                corr_pattern = re.compile(
                    r"\b" + re.escape(change["corrected"]) + r"\b", re.IGNORECASE
                )

                # find matches in original line
                for match in orig_pattern.finditer(orig_line):
                    start, end = match.span()
                    orig_text.stylize("red bold", start, end)

                # find matches in corrected line
                for match in corr_pattern.finditer(corr_line):
                    start, end = match.span()
                    corr_text.stylize("green bold", start, end)

            console.print("  [red]−[/] ", end="")
            console.print(orig_text)
            console.print("  [green]+[/] ", end="")
            console.print(corr_text)
            console.print()

    return state


def approve_changes_node(state: AgentState) -> AgentState:
    approve = state.get("auto_approve") or Confirm.ask(
        "Do you want to accept and save the suggested changes?"
    )
    return {**state, "approved": approve}


def write_file_node(state: AgentState) -> AgentState:
    if state.get("approved"):
        path = Path(state["path"])
        backup_path = path.with_suffix(".bak.mdx")
        path.rename(backup_path)
        Path(path).write_text(state["corrected_text"], encoding="utf-8")
        console.print(
            f"[green]Updated file saved. Original backed up to {backup_path}[/]"
        )
    else:
        console.print("[yellow]No changes were made.[/]")
    return state


def no_corrections_node(state: AgentState) -> AgentState:
    console.print("[green]No spelling errors found. The document looks good![/]")
    return state


def route_after_llm(state: AgentState) -> str:
    """Route to diff processing if corrections exist, otherwise to no_corrections"""
    if state.get("has_corrections", False):
        return "diff"
    else:
        return "no_corrections"


def build_graph() -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("load_file", load_file_node)
    graph.add_node("call_llm", call_openai_node)
    graph.add_node("diff", compute_diff_node)
    graph.add_node("print", print_diff_node)
    graph.add_node("approve", approve_changes_node)
    graph.add_node("write", write_file_node)
    graph.add_node("no_corrections", no_corrections_node)

    graph.set_entry_point("load_file")
    graph.add_edge("load_file", "call_llm")
    graph.add_conditional_edges("call_llm", route_after_llm)
    graph.add_edge("diff", "print")
    graph.add_edge("print", "approve")
    graph.add_edge("approve", "write")
    return graph.compile()


# @click.command()
# @click.argument("file_path", type=click.Path(exists=True))
# @click.option("--yes", is_flag=True, help="Automatically approve and apply suggested changes.")
# def main(file_path, yes):
#     graph = build_graph()
#     initial_state: ProofreaderState = {"path": str(file_path), "auto_approve": yes}
#     graph.invoke(initial_state)

if __name__ == "__main__":
    graph = build_graph()
    state: AgentState = {"path": TEST_WITHOUT_ERRORS, "auto_approve": False}
    graph.invoke(state)
