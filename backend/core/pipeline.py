import uuid
from typing import Optional
from fastapi import UploadFile

from .extractor import extract_source
from .chunker import simple_chunk
from .embedder import embed_texts
from .retriever import retrieve_relevant_chunks, vector_store
from .llm import synthesize_answer
from db.metadata_store import store_document_metadata
from models.request_models import IngestRequest, QueryRequest
from models.response_models import QueryResponse, SourceChunk


def ingest_source(request: IngestRequest, file: Optional[UploadFile] = None) -> None:
    raw_text = extract_source(request.source_url, file)
    if not raw_text.strip():
        return

    chunks = simple_chunk(raw_text)
    embeddings = embed_texts(chunks)

    doc_id = str(uuid.uuid4())
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"doc_id": doc_id, "source": request.source_url or file.filename if file else None} for _ in chunks]

    vector_store.add(embeddings, chunks, metadatas, ids)
    store_document_metadata(doc_id=doc_id, source=request.source_url, n_chunks=len(chunks))


def run_query(request: QueryRequest) -> QueryResponse:
    retrieved = retrieve_relevant_chunks(
        query=request.query,
        k=request.top_k,
        enable_rerank=request.enable_rerank,
        rerank_threshold=request.rerank_threshold,
    )
    answer = synthesize_answer(
        query=request.query,
        contexts=retrieved,
        session_id=request.session_id,
        chat_history=request.chat_history,
    )
    sources = [
        SourceChunk(
            id=chunk["id"],
            text=chunk["text"],
            metadata=chunk.get("metadata") or {},
        )
        for chunk in retrieved
    ]
    return QueryResponse(answer=answer, sources=sources)
