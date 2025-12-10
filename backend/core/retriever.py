from typing import List, Dict
from .embedder import embed_query
from .vectorstore import EncryptedVectorStore
from .reranker import rerank_and_filter
from config import settings


# Initialize vector store with encryption if enabled
def _create_vector_store():
    encrypt_metadata_fields = []
    if settings.encrypt_metadata_fields:
        encrypt_metadata_fields = [f.strip() for f in settings.encrypt_metadata_fields.split(",")]

    return EncryptedVectorStore(
        path=settings.vector_store_path,
        encrypt_texts=settings.encrypt_vector_texts,
        encrypt_metadata_fields=encrypt_metadata_fields,
    )


vector_store = _create_vector_store()


def retrieve_relevant_chunks(
    query: str,
    k: int = 5,
    enable_rerank: bool = False,
    rerank_threshold: float = 0.0,
) -> List[Dict]:
    """
    Retrieve relevant chunks from vector store with optional reranking.

    Args:
        query: The user's query
        k: Number of results to return
        enable_rerank: Whether to use cross-encoder reranking
        rerank_threshold: Minimum reranking score threshold

    Returns:
        List of top k chunks, optionally reranked
    """
    q_emb = embed_query(query)
    
    # Get more results from vector search if reranking is enabled
    # (reranking needs candidates to choose from)
    search_k = k * 3 if enable_rerank else k
    results = vector_store.search(q_emb, k=search_k)
    
    chunks = [
        {
            "id": _id,
            "text": text,
            "metadata": meta or {},
        }
        for _id, text, meta in results
    ]
    
    # Apply optional reranking
    if enable_rerank and chunks:
        chunks = rerank_and_filter(
            query=query,
            chunks=chunks,
            k=k,
            enable_rerank=True,
            rerank_threshold=rerank_threshold,
        )
    else:
        chunks = chunks[:k]
    
    return chunks
