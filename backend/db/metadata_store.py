from datetime import datetime
from typing import Dict, Any

from .schemas import DocumentMetadata

# This is intentionally super lightweight.
# Swap this with a real DB (SQLite/Postgres) when you're ready.
_DB: Dict[str, DocumentMetadata] = {}


def store_document_metadata(doc_id: str, source: str | None, n_chunks: int) -> None:
    _DB[doc_id] = DocumentMetadata(
        doc_id=doc_id,
        source=source,
        n_chunks=n_chunks,
        created_at=datetime.utcnow(),
    )


def get_stats() -> Dict[str, Any]:
    total_docs = len(_DB)
    total_chunks = sum(d.n_chunks for d in _DB.values())
    return {
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "docs": [d.model_dump() for d in _DB.values()],
    }
