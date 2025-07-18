import difflib
from pathlib import Path
from typing import Any
from rich.console import Console
from rich.prompt import Confirm
from openai import OpenAI
from langgraph.graph import StateGraph

from proofer.state import AgentState
from proofer.text_utils import has_spelling_corrections, normalize_line_endings
from proofer.display import (
    display_word_changes,
    display_line_diff,
)
from proofer.diff import find_word_changes

client = OpenAI()
console = Console()


def load_file_node(state: AgentState) -> AgentState:
    if state.get("input_text"):
        return {**state, "original_text": state["input_text"]}

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

    has_corrections = has_spelling_corrections(original_text, suggestions)

    if has_corrections and suggestions:
        suggestions = normalize_line_endings(suggestions, original_text.endswith("\n"))

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

    changes = find_word_changes(original_text, corrected_text)

    if not changes:
        console.print("[green]✓ No spelling errors found![/]")
        return state

    display_word_changes(console, changes)
    display_line_diff(console, original_text, corrected_text, changes)

    return state


def approve_changes_node(state: AgentState) -> AgentState:
    auto_approve = state.get("auto_approve") or state.get("input_text") is not None
    approve = auto_approve or Confirm.ask(
        "Do you want to accept and save the suggested changes?"
    )
    return {**state, "approved": approve}


def write_file_node(state: AgentState) -> AgentState:
    if state.get("approved"):
        if state.get("path"):
            path = Path(state["path"])
            backup_path = path.with_suffix(".bak.mdx")
            path.rename(backup_path)
            Path(path).write_text(state["corrected_text"], encoding="utf-8")
            console.print(
                f"[green]Updated file saved. Original backed up to {backup_path}[/]"
            )
        else:
            console.print("[green]Corrected text:[/]")
            console.print(state["corrected_text"])
    else:
        console.print("[yellow]No changes were made.[/]")
    return state


def no_corrections_node(state: AgentState) -> AgentState:
    console.print("[green]No spelling errors found. The document looks good![/]")
    return state


def route_after_llm(state: AgentState) -> str:
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
