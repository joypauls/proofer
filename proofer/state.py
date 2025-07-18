from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    path: Optional[str]
    input_text: Optional[str]
    original_text: str
    llm_response: str
    corrected_text: str
    diff_lines: list[str]
    approved: bool
    auto_approve: bool
    has_corrections: bool
