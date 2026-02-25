from .graph import build_graph
from .state import RunnerState

class TextToSQLRunner:
    def __init__(self):
        self.graph = build_graph()

    def run(self, question: str) -> dict:
        state: RunnerState = {
            "user_query": question,
            "sql": None,
            "result": None,
            "error": None,
            "history": [],
            "retry_count": 0,
        }

        final_state = self.graph.invoke(state)

        if final_state.get("error"):
            raise RuntimeError(final_state["error"])

        return {"sql": final_state["sql"], "result": final_state["result"]}