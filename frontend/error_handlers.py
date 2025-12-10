"""
UI error handlers and display utilities for Streamlit frontend.

Provides reusable components for displaying errors, loading states, and
fallback UI when backend is unavailable.
"""

import streamlit as st
import logging
from typing import Optional, Callable, Any, TypeVar
from functools import wraps
from datetime import datetime

from resilient_client import APIResponse, ErrorType

logger = logging.getLogger(__name__)

T = TypeVar("T")


class UIErrorHandler:
    """Handles error display and user feedback in Streamlit UI."""

    @staticmethod
    def show_error(response: APIResponse, context: str = "Operation") -> None:
        """
        Display error message from API response in Streamlit.

        Args:
            response: APIResponse with error information
            context: Context for error message (e.g., "Data ingestion", "Query")
        """
        if response.success:
            return

        # Log the error
        logger.error(f"{context} failed: {response.error}")

        # Show user-friendly error in Streamlit
        error_msg = response.message or response.error or "An unknown error occurred"

        with st.container():
            st.error(f"❌ {context} failed")
            st.markdown(f"**{error_msg}**")

            # Show additional details in expander
            if response.error and response.message != response.error:
                with st.expander("Technical details"):
                    st.code(response.error, language="text")

            # Show retry suggestion for transient errors
            if response.error_type in [ErrorType.TIMEOUT, ErrorType.CONNECTION_ERROR]:
                st.info("💡 Tip: Try refreshing the page or waiting a moment before retrying.")

            if response.retry_count > 0:
                st.caption(f"Attempted {response.retry_count} retries before failing.")

    @staticmethod
    def show_success(message: str = "✅ Success", details: Optional[str] = None) -> None:
        """Display success message."""
        st.success(message)
        if details:
            st.markdown(details)

    @staticmethod
    def show_warning(title: str, message: str) -> None:
        """Display warning message."""
        st.warning(f"⚠️ {title}\n{message}")

    @staticmethod
    def show_info(message: str) -> None:
        """Display informational message."""
        st.info(f"ℹ️ {message}")

    @staticmethod
    def show_loading_state(message: str = "Loading...") -> None:
        """Show loading spinner and message."""
        with st.spinner(message):
            pass  # Spinner remains visible until next interaction

    @staticmethod
    def show_backend_status(is_available: bool) -> None:
        """Display backend availability status."""
        if is_available:
            st.success("✅ Backend is online")
        else:
            st.error("❌ Backend is offline - Some features are unavailable")
            st.markdown("""
            **What you can do:**
            - Try refreshing the page
            - Check your internet connection
            - Try again in a few moments
            """)

    @staticmethod
    def show_offline_mode() -> None:
        """Display offline mode UI."""
        st.warning("📴 **Offline Mode**")
        st.markdown("""
        The backend server is currently unavailable. 
        
        **Limited functionality available:**
        - View cached results from previous queries
        - Wait for the server to come back online
        
        **Try:**
        1. Check your internet connection
        2. Refresh the page
        3. Try again in a few moments
        """)

    @staticmethod
    def show_timeout_message() -> None:
        """Display timeout-specific message."""
        st.error("⏱️ Request Timeout")
        st.markdown("""
        The server is taking longer than expected to respond.
        
        **What you can try:**
        - Wait a moment and try again
        - Refresh the page
        - Try with a simpler query
        """)

    @staticmethod
    def show_connection_error() -> None:
        """Display connection error message."""
        st.error("🔌 Connection Failed")
        st.markdown("""
        Cannot reach the backend server.
        
        **Possible causes:**
        - Server is down for maintenance
        - Network connectivity issue
        - Incorrect server address
        
        **What to try:**
        - Check your internet connection
        - Verify the server is running
        - Refresh the page
        """)


class ConditionalDisplay:
    """Context managers for conditional UI display."""

    @staticmethod
    def error_container():
        """Container for error messages."""
        return st.container()

    @staticmethod
    def loading_container():
        """Container for loading states."""
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.spinner("Processing...")


def handle_api_call(context: str = "API Call"):
    """
    Decorator for wrapping API calls with error handling and retry UI.

    Usage:
        @handle_api_call("Data Ingestion")
        def ingest_data(url):
            # Make API call
            pass
    """

    def decorator(func: Callable[..., APIResponse]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[Any]:
            try:
                # Show loading state
                with st.spinner(f"{context}..."):
                    response: APIResponse = func(*args, **kwargs)

                # Handle response
                if response.success:
                    UIErrorHandler.show_success(f"✅ {context} completed successfully")
                    return response.data
                else:
                    UIErrorHandler.show_error(response, context)
                    return None

            except Exception as e:
                logger.exception(f"{context} failed with exception")
                st.error(f"❌ {context} failed: {str(e)}")
                return None

        return wrapper

    return decorator


class BackendHealthCheck:
    """Monitor backend health and availability."""

    def __init__(self, client, backend_url: str):
        """
        Initialize health check.

        Args:
            client: ResilientClient instance
            backend_url: Backend base URL
        """
        self.client = client
        self.backend_url = backend_url
        self._last_check_time: Optional[datetime] = None
        self._is_available: bool = True

    def check_health(self, force: bool = False) -> bool:
        """
        Check if backend is available.

        Args:
            force: Force check even if recently checked

        Returns:
            True if backend is available, False otherwise
        """
        # Use cached result if recent
        if not force and self._last_check_time:
            from datetime import timedelta

            if datetime.now() - self._last_check_time < timedelta(seconds=30):
                return self._is_available

        try:
            response = self.client.get(f"{self.backend_url}/health", timeout=5)
            self._is_available = response.success
            self._last_check_time = datetime.now()
            return self._is_available

        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            self._is_available = False
            self._last_check_time = datetime.now()
            return False

    @property
    def is_available(self) -> bool:
        """Get last known availability status."""
        return self._is_available


class FallbackContent:
    """Fallback content and suggestions when backend is unavailable."""

    @staticmethod
    def show_query_offline_mode() -> None:
        """Show offline query interface."""
        st.markdown("""
        ### 💭 Query Mode (Offline)
        
        The backend is currently unavailable. You can:
        - Browse previously cached results
        - Prepare your queries for when the server is back online
        """)

    @staticmethod
    def show_ingest_offline_mode() -> None:
        """Show offline ingest interface."""
        st.markdown("""
        ### 📥 Ingest Mode (Offline)
        
        **Ingestion is currently unavailable** because the backend server is not responding.
        
        When the server comes back online:
        1. Refresh this page
        2. Try ingesting your content again
        """)

    @staticmethod
    def show_stats_offline_mode() -> None:
        """Show offline stats interface."""
        st.markdown("""
        ### 📊 Statistics (Offline)
        
        Live statistics are unavailable while the backend is offline.
        
        **Cached stats from last check:**
        - (No recent statistics available)
        """)

    @staticmethod
    def suggest_retry() -> bool:
        """Show retry suggestion and return if user wants to retry."""
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Try Again", key="retry_button"):
                st.rerun()
        with col2:
            if st.button("⟳ Refresh Page", key="refresh_button"):
                st.rerun()
        return False
