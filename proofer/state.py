from typing import TypedDict


class AgentState(TypedDict):
    path: str
    original_text: str
    llm_response: str
    corrected_text: str
    diff_lines: list[str]
    approved: bool
    auto_approve: bool
    has_corrections: bool
