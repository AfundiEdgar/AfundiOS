"""
LLM Synthesis Module

Provides unified interface for LLM responses using configurable providers.
Supports OpenAI, Anthropic, Cohere, and local LLMs.
"""

from typing import List, Dict, Optional, Tuple
import logging
from langchain.memory import ConversationBufferMemory
from .provider_factory import get_provider

logger = logging.getLogger(__name__)

# Global memory store for conversations (session_id -> memory)
_conversation_memory: Dict[str, ConversationBufferMemory] = {}


def _get_conversation_memory(session_id: str) -> ConversationBufferMemory:
    """Get or create a conversation memory for a session."""
    if session_id not in _conversation_memory:
        _conversation_memory[session_id] = ConversationBufferMemory(
            return_messages=True,
            human_prefix="User",
            ai_prefix="Assistant",
        )
    return _conversation_memory[session_id]


def clear_conversation_memory(session_id: str) -> None:
    """Clear the conversation memory for a session."""
    if session_id in _conversation_memory:
        del _conversation_memory[session_id]


def list_sessions() -> List[str]:
    """List all active session IDs with conversation memory."""
    return list(_conversation_memory.keys())


def _build_context_string(contexts: List[Dict], max_context_chars: int = 8000) -> str:
    """Format contexts into a readable context string."""
    parts: List[str] = []
    total = 0
    for i, c in enumerate(contexts, start=1):
        text = c.get("text", "")
        meta = c.get("metadata") or {}
        src = meta.get("source") or meta.get("doc_id") or "unknown"
        snippet = text.replace("\n", " ")
        if total + len(snippet) > max_context_chars:
            remain = max(0, max_context_chars - total)
            snippet = snippet[:remain]
            parts.append(f"[{i}] id={c.get('id')} source={src}: {snippet}")
            break
        parts.append(f"[{i}] id={c.get('id')} source={src}: {snippet}")
        total += len(snippet)
    return "\n\n".join(parts)


def synthesize_answer(
    query: str,
    contexts: List[Dict],
    session_id: Optional[str] = None,
    chat_history: Optional[List[Tuple[str, str]]] = None,
) -> str:
    """Produce an answer for `query` using `contexts` with optional conversation history.

    Args:
        query: The user's question
        contexts: Retrieved context chunks
        session_id: Optional session ID for persistent conversation memory
        chat_history: Optional list of (user_message, assistant_message) tuples

    Uses the configured LLM provider (OpenAI, Anthropic, Cohere, or local).
    Falls back to a readable stub if provider is not available.
    """
    context_str = _build_context_string(contexts)

    try:
        provider = get_provider()
        return provider.chat(query=query, context=context_str, history=chat_history)
    except Exception as e:
        logger.error(f"LLM provider error: {e}")
        # Fallback
        return _synthesize_stub(query=query, context_str=context_str)


def _synthesize_stub(query: str, context_str: str) -> str:
    """Fallback stub when LLM provider is not available."""
    return (
        "(Local stub) LLM provider is not configured or unavailable.\n\n"
        f"Question: {query}\n\n"
        f"Top contexts:\n{context_str[:1200]}"
    )
