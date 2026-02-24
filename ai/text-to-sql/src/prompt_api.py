import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any
from .data_agent import Agent  # relative import

app = FastAPI(title="NL2SQL Spark API", version="0.1.0")

# -----------------------------
# Request / Response Models
# -----------------------------
class Response(BaseModel):
    columns: List[str]
    rows: List[List[Any]]


class QueryResponse(BaseModel):
    sql: str
    result: Response


class QueryRequest(BaseModel):
    question: str


# -----------------------------
# Agent instance
# -----------------------------
agent = Agent()


# -----------------------------
# Endpoint
# -----------------------------
@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    try:
            start = time.time()
            latency_ms = (time.time() - start) * 1000
            result = agent.infer(request.question)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return QueryResponse(sql=result["sql"], result=result["result"], latency_ms=latency_ms)