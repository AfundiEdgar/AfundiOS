from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from core.llm import clear_conversation_memory, list_sessions

router = APIRouter()


class ConversationSession(BaseModel):
    session_id: str


class SessionList(BaseModel):
    sessions: List[str]


@router.get("/sessions", response_model=SessionList)
async def get_sessions():
    """List all active conversation sessions with memory."""
    return SessionList(sessions=list_sessions())


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear the conversation memory for a specific session."""
    clear_conversation_memory(session_id)
    return {"status": "cleared", "session_id": session_id}


@router.post("/sessions/clear-all")
async def clear_all_sessions():
    """Clear all conversation memory."""
    sessions = list_sessions()
    for session_id in sessions:
        clear_conversation_memory(session_id)
    return {"status": "cleared", "count": len(sessions)}
