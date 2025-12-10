"""
Resilient HTTP client with retry logic, timeout handling, and error recovery.

This module provides a robust wrapper around requests for backend API calls
with automatic retry on transient failures, exponential backoff, and detailed
error information.
"""

import time
import logging
import requests
from typing import Optional, Dict, Any, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry as URLRetry
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of API error types."""
    CONNECTION_ERROR = "connection_error"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    UNKNOWN = "unknown"


@dataclass
class APIResponse:
    """Structured response from API calls."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    status_code: Optional[int] = None
    retry_count: int = 0
    is_cached: bool = False
    message: Optional[str] = None  # User-friendly message

    def __bool__(self):
        """Allow truthiness check: `if response:`"""
        return self.success


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        timeout: float = 10.0,
        retry_on_status_codes: Optional[list] = None,
    ):
        """
        Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff multiplier
            timeout: Request timeout in seconds
            retry_on_status_codes: HTTP status codes to retry on (e.g., [502, 503, 504])
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.retry_on_status_codes = retry_on_status_codes or [502, 503, 504, 408]


class ResilientClient:
    """HTTP client with retry logic and error handling."""

    def __init__(self, config: Optional[RetryConfig] = None, cache_enabled: bool = True):
        """
        Initialize resilient client.

        Args:
            config: RetryConfig instance for retry behavior
            cache_enabled: Enable caching of successful responses
        """
        self.config = config or RetryConfig()
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy."""
        session = requests.Session()

        # Configure retry strategy for transient failures
        retry_strategy = URLRetry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=self.config.retry_on_status_codes,
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_cache_key(self, method: str, url: str) -> str:
        """Generate cache key for request."""
        return f"{method}:{url}"

    def _classify_error(
        self, exception: Exception, status_code: Optional[int] = None
    ) -> ErrorType:
        """Classify error type for better error handling."""
        if isinstance(exception, requests.ConnectionError):
            return ErrorType.CONNECTION_ERROR
        if isinstance(exception, requests.Timeout):
            return ErrorType.TIMEOUT
        if status_code and 500 <= status_code < 600:
            return ErrorType.SERVER_ERROR
        if status_code and 400 <= status_code < 500:
            return ErrorType.CLIENT_ERROR
        return ErrorType.UNKNOWN

    def _should_retry(
        self, exception: Exception, status_code: Optional[int] = None, attempt: int = 0
    ) -> bool:
        """Determine if request should be retried."""
        if attempt >= self.config.max_retries:
            return False

        # Retry on connection errors and timeouts
        if isinstance(exception, (requests.ConnectionError, requests.Timeout)):
            return True

        # Retry on specific status codes
        if status_code and status_code in self.config.retry_on_status_codes:
            return True

        return False

    def _make_request(
        self,
        method: str,
        url: str,
        attempt: int = 0,
        **kwargs,
    ) -> APIResponse:
        """Make HTTP request with retry logic."""
        cache_key = self._get_cache_key(method, url)

        try:
            # Check cache for GET requests
            if self.cache_enabled and method.upper() == "GET" and cache_key in self._cache:
                logger.debug(f"Cache hit for {method} {url}")
                cached = self._cache[cache_key]
                return APIResponse(
                    success=True,
                    data=cached,
                    is_cached=True,
                    retry_count=attempt,
                )

            # Make request with timeout
            timeout = kwargs.pop("timeout", self.config.timeout)
            response = self.session.request(
                method,
                url,
                timeout=timeout,
                **kwargs,
            )

            # Check for HTTP errors
            if response.status_code >= 400:
                error_type = self._classify_error(None, response.status_code)
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"

                # Retry on specific status codes
                if self._should_retry(None, response.status_code, attempt):
                    logger.warning(
                        f"Attempt {attempt + 1}: {error_msg}, retrying..."
                    )
                    time.sleep(self.config.backoff_factor ** attempt)
                    return self._make_request(method, url, attempt + 1, **kwargs)

                logger.error(f"API error: {error_msg}")
                return APIResponse(
                    success=False,
                    error=error_msg,
                    error_type=error_type,
                    status_code=response.status_code,
                    retry_count=attempt,
                    message=self._get_user_friendly_message(error_type, response.status_code),
                )

            # Success
            data = response.json() if response.text else {}

            # Cache successful GET requests
            if self.cache_enabled and method.upper() == "GET":
                self._cache[cache_key] = data

            return APIResponse(
                success=True,
                data=data,
                status_code=response.status_code,
                retry_count=attempt,
            )

        except requests.Timeout as e:
            logger.warning(f"Attempt {attempt + 1}: Timeout - {str(e)}")

            if self._should_retry(e, None, attempt):
                time.sleep(self.config.backoff_factor ** attempt)
                return self._make_request(method, url, attempt + 1, **kwargs)

            logger.error(f"Request timeout after {attempt + 1} attempts")
            return APIResponse(
                success=False,
                error=f"Request timeout after {attempt + 1} attempts",
                error_type=ErrorType.TIMEOUT,
                retry_count=attempt,
                message="The server is taking too long to respond. Please try again.",
            )

        except requests.ConnectionError as e:
            logger.warning(f"Attempt {attempt + 1}: Connection error - {str(e)}")

            if self._should_retry(e, None, attempt):
                time.sleep(self.config.backoff_factor ** attempt)
                return self._make_request(method, url, attempt + 1, **kwargs)

            logger.error(f"Connection failed after {attempt + 1} attempts")
            return APIResponse(
                success=False,
                error=f"Cannot reach backend server: {str(e)}",
                error_type=ErrorType.CONNECTION_ERROR,
                retry_count=attempt,
                message="Cannot reach the server. Please check your connection and try again.",
            )

        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return APIResponse(
                success=False,
                error=str(e),
                error_type=ErrorType.UNKNOWN,
                retry_count=attempt,
                message="An unexpected error occurred. Please try again.",
            )

        except ValueError as e:
            logger.error(f"Invalid JSON response: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Invalid server response: {str(e)}",
                error_type=ErrorType.SERVER_ERROR,
                retry_count=attempt,
                message="The server returned an invalid response. Please try again.",
            )

    def get(self, url: str, **kwargs) -> APIResponse:
        """Make GET request with retry logic."""
        return self._make_request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> APIResponse:
        """Make POST request with retry logic."""
        return self._make_request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> APIResponse:
        """Make PUT request with retry logic."""
        return self._make_request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> APIResponse:
        """Make DELETE request with retry logic."""
        return self._make_request("DELETE", url, **kwargs)

    def clear_cache(self) -> None:
        """Clear response cache."""
        self._cache.clear()
        logger.info("Response cache cleared")

    def _get_user_friendly_message(self, error_type: ErrorType, status_code: Optional[int] = None) -> str:
        """Generate user-friendly error message based on error type."""
        messages = {
            ErrorType.CONNECTION_ERROR: "Cannot reach the server. Please check your internet connection.",
            ErrorType.TIMEOUT: "The server is taking too long to respond. Please try again.",
            ErrorType.SERVER_ERROR: "The server is experiencing issues. Please try again later.",
            ErrorType.CLIENT_ERROR: "Invalid request. Please check your input.",
            ErrorType.UNKNOWN: "An unexpected error occurred. Please try again.",
        }
        return messages.get(error_type, "An unexpected error occurred.")
