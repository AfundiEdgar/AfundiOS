from pydantic import BaseModel
from typing import List, Dict, Any


class IngestResponse(BaseModel):
    status: str


class SourceChunk(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = {}


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]


class StatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    docs: List[Dict[str, Any]]
