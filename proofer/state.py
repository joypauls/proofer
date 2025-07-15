from typing import TypedDict
from rich.console import Console


class AgentState(TypedDict):
    path: str
    console: Console
    original_text: str
    llm_response: str
    corrected_text: str
    diff_lines: list[str]
    approved: bool
    auto_approve: bool
    has_corrections: bool
