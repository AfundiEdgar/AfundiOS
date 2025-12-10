from pydantic import BaseModel
from datetime import datetime


class DocumentMetadata(BaseModel):
    doc_id: str
    source: str | None = None
    n_chunks: int
    created_at: datetime
