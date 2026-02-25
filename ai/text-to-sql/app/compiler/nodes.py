from .state import RunnerState
from . import capabilities

def generate_node(state: RunnerState) -> dict:
    sql = capabilities.generate_sql(state["user_query"])
    return {"sql": sql, "error": None}

def execute_node(state: RunnerState) -> dict:
    try:
        result = capabilities.execute_sql(state["sql"])
        return {"result": result, "error": None}
    except Exception as e:
        return {"error": str(e)}

def repair_node(state: RunnerState) -> dict:
    history = state["history"] + [{"sql": state["sql"], "error": state["error"]}]
    sql = capabilities.retry_sql(state["user_query"], history)
    return {
        "sql": sql,
        "history": history,
        "retry_count": state["retry_count"] + 1,
        "error": None,
    }

def clean_sql_node(state: RunnerState) -> dict:
    """
    Strip ```sql blocks, leading/trailing whitespace, etc.
    """
    sql = state.get("sql", "")
    
    # Remove ```sql ... ``` fences
    if sql.startswith("```sql"):
        sql = "\n".join(sql.splitlines()[1:-1])
    
    sql = sql.strip()
    
    return {"sql": sql, "error": None}