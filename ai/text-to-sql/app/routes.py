from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Any
from .compiler.runner import TextToSQLRunner

router = APIRouter()
runner = TextToSQLRunner()

class Response(BaseModel):
    columns: List[str]
    rows: List[List[Any]]

class QueryResponse(BaseModel):
    sql: str
    result: Response

class QueryRequest(BaseModel):
    question: str
    model: str
    version: int

@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    result = runner.run(request.question, model=request.model, version=request.version)
    return QueryResponse(sql=result["sql"], result=result["result"])