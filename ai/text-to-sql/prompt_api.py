from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Any
import time

app = FastAPI(
    title="NL2SQL Query API",
    version="0.1.0"
)

# ----------------
# Schemas
# ----------------

class QueryRequest(BaseModel):
    question: str

class Response(BaseModel):
    columns: List[str]
    rows: List[List[Any]]

class QueryResponse(BaseModel):
    sql: str
    result: Response    
    latency_ms: float


# ----------------
# Endpoint
# ----------------

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    start = time.time()

    latency_ms = (time.time() - start) * 1000

    return QueryResponse(
        sql="  SELECT * FROM table WHERE condition",
        result=Response(
            columns=["id", "name", "value"],
            rows=[
                [1, "Alice", 10],
                [2, "Bob", 20]
            ]
        ),
        latency_ms=latency_ms
    )