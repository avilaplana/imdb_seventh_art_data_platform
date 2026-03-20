from langgraph.graph import StateGraph, END
from .state import RunnerState
from .nodes import (
    load_prompt_configuration_node,
    sanitize_sql_node,
    generate_llm_response_node,
    execute_sql_node,
    repair_sql_node,
    validate_sql_node,
)

MAX_RETRIES = 3

def build_graph():
    graph = StateGraph(RunnerState)
    graph.add_node("load_prompt_configuration", load_prompt_configuration_node)
    graph.add_node("generate_sql", generate_llm_response_node)
    graph.add_node("sanitize_sql", sanitize_sql_node)
    graph.add_node("validate_sql", validate_sql_node)
    graph.add_node("execute_sql", execute_sql_node)
    graph.add_node("repair_sql", repair_sql_node)

    graph.set_entry_point("load_prompt_configuration")
    graph.add_edge("load_prompt_configuration", "generate_sql")
    graph.add_edge("generate_sql", "sanitize_sql")
    graph.add_edge("sanitize_sql", "validate_sql")
    graph.add_edge("validate_sql", "execute_sql")

    graph.add_conditional_edges(
        "execute_sql",
        lambda s: "repair_sql" if s.get("error") and s["retry_count"] < MAX_RETRIES else END,
    )

    graph.add_edge("repair_sql", "sanitize_sql")

    return graph.compile()