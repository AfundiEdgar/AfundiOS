from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Tuple


class IngestRequest(BaseModel):
    source_url: Optional[HttpUrl] = None
    tags: Optional[List[str]] = None


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    session_id: Optional[str] = None
    chat_history: Optional[List[Tuple[str, str]]] = None
    enable_rerank: bool = False
    rerank_threshold: float = 0.0

