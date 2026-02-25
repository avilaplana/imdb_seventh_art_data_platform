from langgraph.graph import StateGraph, END
from .state import RunnerState
from .nodes import clean_sql_node, generate_node, execute_node, repair_node

MAX_RETRIES = 2

def build_graph():
    graph = StateGraph(RunnerState)
    graph.add_node("generate", generate_node)
    graph.add_node("clean", clean_sql_node)
    graph.add_node("execute", execute_node)
    graph.add_node("repair", repair_node)

    graph.set_entry_point("generate")
    graph.add_edge("generate", "clean")
    graph.add_edge("clean", "execute")
    
    graph.add_conditional_edges(
        "execute",
        lambda s: "repair" if s.get("error") and s["retry_count"] < MAX_RETRIES else END,
    )

    graph.add_edge("repair", "generate")

    return graph.compile()