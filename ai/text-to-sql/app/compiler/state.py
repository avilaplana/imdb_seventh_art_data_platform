from typing import TypedDict, Optional, List, Dict, Any

class RunnerState(TypedDict):
    user_query: str
    model: str
    version: int
    sql: Optional[str]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    history: List[Dict[str, str]]
    retry_count: int