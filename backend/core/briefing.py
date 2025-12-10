from datetime import datetime, timedelta
import os
import json
import logging
from typing import Dict, Any, List

from config import settings
from backend.core.vectorstore import EncryptedVectorStore
from backend.core.agents.summarizer import SummarizerAgent, SummaryStyle, SummaryLength

logger = logging.getLogger(__name__)

BRIEFINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "briefings")
# Normalize path
BRIEFINGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "briefings"))


def _ensure_dir():
    os.makedirs(BRIEFINGS_DIR, exist_ok=True)


def _choose_summary_style(style_name: str):
    # Map simple names to SummaryStyle/Length
    try:
        style = SummaryStyle.EXECUTIVE if style_name == "executive" else SummaryStyle.BULLET_POINTS if style_name == "bullet_points" else SummaryStyle.NARRATIVE
    except Exception:
        style = SummaryStyle.EXECUTIVE
    return style


class BriefingManager:
    def __init__(self, vector_store: EncryptedVectorStore, summarizer: SummarizerAgent):
        self.vector_store = vector_store
        self.summarizer = summarizer
        _ensure_dir()

    def list_briefings(self) -> List[Dict[str, Any]]:
        files = []
        for fname in sorted(os.listdir(BRIEFINGS_DIR), reverse=True):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(BRIEFINGS_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    files.append(meta)
            except Exception:
                logger.exception("Failed to read briefing file %s", path)
        return files

    def get_briefing(self, briefing_id: str) -> Dict[str, Any] | None:
        path = os.path.join(BRIEFINGS_DIR, f"{briefing_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_briefing(self, lookback_days: int = None, style: str | None = None, max_chars: int | None = None) -> Dict[str, Any]:
        lookback_days = lookback_days if lookback_days is not None else settings.daily_briefing_lookback_days
        style = style or settings.daily_briefing_summary_style
        max_chars = max_chars or settings.daily_briefing_max_chars

        cutoff = datetime.utcnow() - timedelta(days=lookback_days)

        # List all docs and filter by metadata.created_at
        docs = self.vector_store.list_all()

        recent_texts = []
        sources = []
        for d in docs:
            meta = d.get("metadata") or {}
            ts = meta.get("created_at") or meta.get("timestamp") or meta.get("created")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                except Exception:
                    try:
                        dt = datetime.utcfromtimestamp(float(ts))
                    except Exception:
                        dt = None
                if dt and dt < cutoff:
                    continue

            # If no timestamp, include — caller can adjust
            text = d.get("text") or ""
            if text:
                recent_texts.append(text)
                sources.append({"id": d.get("id"), "metadata": meta})

        # Concatenate until max_chars
        accumulated = "\n\n".join(recent_texts)
        if len(accumulated) > max_chars:
            accumulated = accumulated[:max_chars]

        # Summarize
        summary_style = _choose_summary_style(style)
        # Use MEDIUM for daily briefings
        try:
            summary = self.summarizer.summarize(
                content=accumulated,
                style=summary_style,
                length=SummaryLength.MEDIUM,
            )
            summary_text = summary.summary_text if hasattr(summary, "summary_text") else summary.summary
        except Exception as e:
            logger.exception("Failed to summarize briefing: %s", e)
            summary_text = ""

        briefing_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        result = {
            "id": briefing_id,
            "created_at": datetime.utcnow().isoformat(),
            "lookback_days": lookback_days,
            "style": style,
            "summary": summary_text,
            "sources": sources[:50],
            "sources_count": len(sources),
        }

        # Persist
        path = os.path.join(BRIEFINGS_DIR, f"{briefing_id}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception:
            logger.exception("Failed to persist briefing %s", briefing_id)

        return result
