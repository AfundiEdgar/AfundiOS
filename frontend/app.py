"""
AfundiOS Frontend - Streamlit-based UI for Personal AI OS

Features:
- Resilient API client with automatic retry and fallback
- Graceful error handling when backend is unavailable
- Offline-friendly UI with cached content support
- User-friendly error messages and recovery suggestions
"""

import os
import logging
import streamlit as st
from datetime import datetime

from resilient_client import ResilientClient, RetryConfig, APIResponse
from error_handlers import UIErrorHandler, BackendHealthCheck, FallbackContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
RETRY_CONFIG = RetryConfig(
    max_retries=int(os.getenv("MAX_RETRIES", "3")),
    backoff_factor=float(os.getenv("BACKOFF_FACTOR", "0.5")),
    timeout=float(os.getenv("REQUEST_TIMEOUT", "10.0")),
)

# Initialize Streamlit page config
st.set_page_config(
    page_title="AfundiOS",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "client" not in st.session_state:
    st.session_state.client = ResilientClient(config=RETRY_CONFIG, cache_enabled=ENABLE_CACHE)

if "health_check" not in st.session_state:
    st.session_state.health_check = BackendHealthCheck(
        st.session_state.client, BACKEND_URL
    )

# Title and status
st.title("AfundiOS — Personal AI OS")
st.caption("Intelligent Retrieval-Augmented Generation with graceful fallback support")

# Sidebar with backend status and settings
with st.sidebar:
    st.header("System Status")

    # Backend health indicator
    with st.spinner("Checking backend status..."):
        is_backend_available = st.session_state.health_check.check_health()

    if is_backend_available:
        st.success("✅ Backend Online")
    else:
        st.error("❌ Backend Offline")
        st.warning("""
        **Limited functionality:**
        - Query: View cached results only
        - Ingest: Queue for later processing
        - Stats: Cached data only
        """)

    # Settings section
    st.divider()
    st.subheader("⚙️ Settings")

    col1, col2 = st.columns(2)
    with col1:
        enable_cache = st.checkbox("Enable Caching", value=ENABLE_CACHE)
    with col2:
        if st.button("Clear Cache"):
            st.session_state.client.clear_cache()
            st.success("Cache cleared")

    # Backend URL display
    st.divider()
    st.subheader("Configuration")
    st.caption(f"Backend URL: `{BACKEND_URL}`")
    st.caption(f"Retry attempts: {RETRY_CONFIG.max_retries}")
    st.caption(f"Request timeout: {RETRY_CONFIG.timeout}s")


# Main tabs
tab_chat, tab_ingest, tab_stats = st.tabs(["💬 Chat", "📥 Ingest", "📊 Stats"])

# ============================================================================
# CHAT TAB
# ============================================================================
with tab_chat:
    st.subheader("Ask your knowledge base")

    if not is_backend_available:
        st.warning("⚠️ Backend is offline - showing cached results only")

    query = st.text_area(
        "Your question",
        placeholder="Ask me anything about your knowledge base...",
        height=100,
    )

    col1, col2 = st.columns([0.2, 0.8])
    with col1:
        ask_button = st.button("Ask", type="primary", use_container_width=True)
    with col2:
        st.empty()

    if ask_button and query.strip():
        try:
            with st.spinner("Thinking..."):
                payload = {"query": query, "top_k": 5}
                response = st.session_state.client.post(
                    f"{BACKEND_URL}/query", json=payload
                )

            if response.success:
                data = response.data or {}

                st.markdown("### Answer")
                st.info(data.get("answer", "No answer generated"))

                sources = data.get("sources", [])
                if sources:
                    st.markdown("### Sources")
                    for idx, src in enumerate(sources, 1):
                        with st.expander(f"Source {idx}: {src.get('id', 'Unknown')}"):
                            st.write(src.get("text", "No content"))
                            if src.get("metadata"):
                                st.json(src.get("metadata"))
                else:
                    st.info("No sources found for this query")

                if response.is_cached:
                    st.caption("📦 This result is from cache")

            else:
                UIErrorHandler.show_error(response, "Query")
                if not is_backend_available:
                    FallbackContent.show_query_offline_mode()

        except Exception as e:
            logger.exception("Query failed with exception")
            st.error(f"❌ Query failed: {str(e)}")

# ============================================================================
# INGEST TAB
# ============================================================================
with tab_ingest:
    st.subheader("Ingest content")

    if not is_backend_available:
        st.warning("⚠️ Backend is offline - ingestion is temporarily unavailable")
        FallbackContent.show_ingest_offline_mode()
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**From URL:**")
            source_url = st.text_input(
                "Enter a URL",
                placeholder="https://example.com or YouTube link",
                label_visibility="collapsed",
            )

        with col2:
            st.markdown("**From File:**")
            file = st.file_uploader(
                "Upload a file",
                type=["txt", "md", "pdf"],
                label_visibility="collapsed",
            )

        st.divider()

        if st.button("📤 Ingest", type="primary", use_container_width=True):
            if not source_url and not file:
                st.warning("Please provide either a URL or upload a file")
            else:
                try:
                    with st.spinner("Ingesting content..."):
                        files = None
                        data = {"source_url": source_url or None}

                        if file is not None:
                            files = {"file": (file.name, file.getvalue())}
                            logger.info(f"Ingesting file: {file.name}")
                        else:
                            logger.info(f"Ingesting URL: {source_url}")

                        response = st.session_state.client.post(
                            f"{BACKEND_URL}/ingest", data=data, files=files
                        )

                    if response.success:
                        result = response.data or {}
                        UIErrorHandler.show_success(
                            "✅ Content ingested successfully",
                            f"Processed {result.get('chunks_created', 0)} chunks",
                        )
                        st.json(result)
                    else:
                        UIErrorHandler.show_error(response, "Ingestion")

                except Exception as e:
                    logger.exception("Ingestion failed with exception")
                    st.error(f"❌ Ingestion failed: {str(e)}")

# ============================================================================
# STATS TAB
# ============================================================================
with tab_stats:
    st.subheader("Knowledge Base Statistics")

    if not is_backend_available:
        st.warning("⚠️ Backend is offline - showing cached statistics")
        FallbackContent.show_stats_offline_mode()

    try:
        with st.spinner("Loading statistics..."):
            response = st.session_state.client.get(f"{BACKEND_URL}/stats")

        if response.success:
            stats = response.data or {}

            # Display stats in columns
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Documents",
                    stats.get("total_documents", 0),
                    delta=stats.get("documents_this_week", 0),
                )

            with col2:
                st.metric(
                    "Total Chunks",
                    stats.get("total_chunks", 0),
                )

            with col3:
                st.metric(
                    "Average Chunk Size",
                    f"{stats.get('avg_chunk_size', 0):.0f} tokens",
                )

            with col4:
                st.metric(
                    "Last Updated",
                    stats.get("last_updated", "Never"),
                )

            # Full stats JSON
            st.divider()
            st.markdown("### Detailed Statistics")
            st.json(stats)

            if response.is_cached:
                st.caption("📦 Statistics are from cache - may be outdated")

        else:
            UIErrorHandler.show_error(response, "Statistics fetch")

    except Exception as e:
        logger.exception("Stats fetch failed with exception")
        st.error(f"❌ Failed to fetch statistics: {str(e)}")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
with st.container():
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption(f"🕐 Last refresh: {datetime.now().strftime('%H:%M:%S')}")

    with col2:
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.session_state.health_check.check_health(force=True)
            st.rerun()

    with col3:
        if st.button("🧹 Clear All Cache", use_container_width=True):
            st.session_state.client.clear_cache()
            st.success("Cache cleared!")
