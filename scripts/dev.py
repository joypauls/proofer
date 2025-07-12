import click
import difflib
from pathlib import Path
from typing import TypedDict
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Confirm
from openai import OpenAI
import langgraph
from langgraph.graph import StateGraph

client = OpenAI()
console = Console()


class AgentState(TypedDict, total=False):
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
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful markdown proofreader. Your ONLY task is to fix spelling errors. "
                    "IMPORTANT: Do not make any formatting changes, do not add or remove whitespace, "
                    "do not change line breaks, and do not change punctuation. "
                    "Only fix misspelled words by replacing them with the correct spelling. "
                    "Preserve the exact original formatting, spacing, and structure. "
                    "Return the corrected text only if there are actual spelling errors to fix. "
                    "Return nothing (empty response) if there are no spelling errors."
                ),
            },
            {"role": "user", "content": state["original_text"]},
        ],
        temperature=0,
    )
    suggestions = response.choices[0].message.content
    original_text = state["original_text"]

    def extract_words(text):
        if not text:
            return []

        import re

        words = re.findall(r"\b\w+\b", text.lower())
        return words

    def has_spelling_corrections(original, suggested):
        if not suggested or not suggested.strip():
            return False

        original_words = extract_words(original)
        suggested_words = extract_words(suggested)

        print(f"Original words: {original_words}")
        print(f"Suggested words: {suggested_words}")

        # Must have same number of words
        if len(original_words) != len(suggested_words):
            print(
                f"Word count mismatch: {len(original_words)} vs {len(suggested_words)}"
            )
            return False

        has_diffs = any(
            orig != sugg for orig, sugg in zip(original_words, suggested_words)
        )
        print(f"Has spelling differences: {has_diffs}")
        return has_diffs

    has_corrections = has_spelling_corrections(original_text, suggestions)

    if has_corrections and suggestions:
        corrected_text = original_text
        original_words = extract_words(original_text)
        suggested_words = extract_words(suggestions)

        corrections = {}
        for orig_word, sugg_word in zip(original_words, suggested_words):
            if orig_word != sugg_word:
                corrections[orig_word] = sugg_word

        import re

        for orig_word, corrected_word in corrections.items():
            pattern = r"\b" + re.escape(orig_word) + r"\b"
            corrected_text = re.sub(
                pattern, corrected_word, corrected_text, flags=re.IGNORECASE
            )

        suggestions = corrected_text

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
    diff_text = "".join(state["diff_lines"])
    syntax = Syntax(diff_text, "diff", theme="ansi_dark", line_numbers=False)
    console.print(Panel(syntax, title="[bold green]Markdown Diff[/]"))
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


def build_graph():
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
    # main()

    test_file = "./test_with_errors.mdx"
    auto_approve = False

    graph = build_graph()
    state = {"path": test_file, "auto_approve": auto_approve}
    graph.invoke(state)
