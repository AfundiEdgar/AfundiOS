from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from config import settings
import threading
import time
import logging

from backend.core.retriever import vector_store

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AfundiOS API",
    version="0.1.0",
    description="RAG backend for AfundiOS personal AI OS",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["root"])
def read_root():
    return {"name": "AfundiOS", "version": app.version, "env": settings.environment}


def _compaction_worker():
    """Background loop that runs compaction periodically when enabled."""
    interval = max(1, settings.memory_compaction_interval_hours) * 3600
    strategy = settings.memory_compaction_strategy
    keep_days = settings.memory_compaction_keep_days
    logger.info("Starting vector-store compaction loop (strategy=%s, interval_hours=%s)", strategy, settings.memory_compaction_interval_hours)
    while True:
        try:
            logger.info("Running scheduled vector-store compaction (strategy=%s)", strategy)
            # run without dry-run when scheduled
            summary = vector_store.compact(strategy=strategy, keep_recent_days=keep_days, dry_run=False)
            logger.info("Compaction summary: %s", summary)
        except Exception as e:
            logger.exception("Error while running compaction: %s", e)

        time.sleep(interval)


@app.on_event("startup")
def _maybe_start_compaction_thread():
    if settings.memory_compaction_enabled:
        t = threading.Thread(target=_compaction_worker, name="vectorstore-compactor", daemon=True)
        t.start()
        logger.info("Vector-store compaction thread started")


def _daily_briefing_worker():
    from backend.core.agents.orchestrator import AgentOrchestrator
    from backend.core.agents.summarizer import SummarizerAgent
    from backend.core.briefing import BriefingManager

    interval = max(1, settings.daily_briefing_interval_hours) * 3600
    logger.info("Starting daily briefing loop (interval_hours=%s)", settings.daily_briefing_interval_hours)
    manager = BriefingManager(vector_store=vector_store, summarizer=SummarizerAgent())

    while True:
        try:
            logger.info("Generating scheduled daily briefing")
            mgr_res = manager.generate_briefing(lookback_days=settings.daily_briefing_lookback_days, style=settings.daily_briefing_summary_style)
            logger.info("Daily briefing generated: %s", {"id": mgr_res.get("id"), "sources": mgr_res.get("sources_count")})
        except Exception as e:
            logger.exception("Error while generating daily briefing: %s", e)

        time.sleep(interval)


@app.on_event("startup")
def _maybe_start_daily_briefing_thread():
    if settings.daily_briefing_enabled:
        t = threading.Thread(target=_daily_briefing_worker, name="daily-briefing", daemon=True)
        t.start()
        logger.info("Daily briefing thread started")
