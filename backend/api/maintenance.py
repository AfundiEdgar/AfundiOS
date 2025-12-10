from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.retriever import vector_store
from config import settings

router = APIRouter()


class CompactRequest(BaseModel):
    strategy: Optional[str] = None
    keep_recent_days: Optional[int] = None
    dry_run: Optional[bool] = True


# Module-level status
_last_run_time: Optional[datetime] = None
_last_run_summary: Optional[dict] = None


@router.post("/compact", tags=["maintenance"])
def compact_vector_store(req: CompactRequest):
    """Trigger a compaction/prune of the vector store.

    Example body:
    {
      "strategy": "deduplicate_exact",  # or "age_based"
      "keep_recent_days": 365,
      "dry_run": true
    }
    """
    global _last_run_time, _last_run_summary

    strategy = req.strategy or settings.memory_compaction_strategy
    keep_days = req.keep_recent_days or settings.memory_compaction_keep_days
    dry = req.dry_run if req.dry_run is not None else True

    summary = vector_store.compact(strategy=strategy, keep_recent_days=keep_days, dry_run=dry)

    _last_run_time = datetime.utcnow()
    _last_run_summary = {"time": _last_run_time.isoformat(), "summary": summary}

    return _last_run_summary


@router.get("/status", tags=["maintenance"])
def get_compaction_status():
    """Return last compaction summary and current settings."""
    return {
        "enabled": settings.memory_compaction_enabled,
        "interval_hours": settings.memory_compaction_interval_hours,
        "last_run": _last_run_summary,
    }
