from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from backend.core.briefing import BriefingManager
from backend.core.retriever import vector_store
from backend.core.agents.summarizer import SummarizerAgent

router = APIRouter()


class BriefingRequest(BaseModel):
    lookback_days: Optional[int] = None
    style: Optional[str] = None
    max_chars: Optional[int] = None


# Lazy manager
_briefing_manager: Optional[BriefingManager] = None


def _get_manager() -> BriefingManager:
    global _briefing_manager
    if _briefing_manager is None:
        _briefing_manager = BriefingManager(vector_store=vector_store, summarizer=SummarizerAgent())
    return _briefing_manager


@router.post("/generate", tags=["briefings"])
def generate_briefing(req: BriefingRequest):
    manager = _get_manager()
    result = manager.generate_briefing(lookback_days=req.lookback_days, style=req.style, max_chars=req.max_chars)
    return result


@router.get("/", tags=["briefings"])
def list_briefings():
    manager = _get_manager()
    return manager.list_briefings()




@router.get("/{briefing_id}", tags=["briefings"])
def get_briefing(briefing_id: str):
    manager = _get_manager()
    b = manager.get_briefing(briefing_id)
    if not b:
        return {"error": "not_found"}
    return b
