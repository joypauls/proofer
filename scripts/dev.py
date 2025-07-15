from proofer.state import AgentState
from proofer.agent import build_graph

TEST_WITHOUT_ERRORS = "./tests/files/test_without_errors.md"
TEST_WITH_ERRORS = "./tests/files/test_with_errors.md"

if __name__ == "__main__":
    graph = build_graph()
    state: AgentState = {"path": TEST_WITH_ERRORS, "auto_approve": False}
    graph.invoke(state)
