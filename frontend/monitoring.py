"""
Error logging and monitoring utilities for frontend.

Provides structured logging, error tracking, and monitoring capabilities
for debugging and production support.
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from enum import Enum

from frontend.resilient_client import ErrorType


class LogLevel(Enum):
    """Application log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """Logger with structured output for better debugging and monitoring."""

    def __init__(self, name: str, log_level: str = "INFO"):
        """
        Initialize structured logger.

        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level))

        # Console handler with formatting
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_api_call(
        self,
        method: str,
        url: str,
        success: bool,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        """Log API call with structured data."""
        log_data = {
            "event": "api_call",
            "method": method,
            "url": url,
            "success": success,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }

        if success:
            self.logger.info(f"API Call: {method} {url} [{status_code}]")
        else:
            self.logger.error(
                f"API Call Failed: {method} {url} [{status_code}] - {error}"
            )

    def log_error(
        self,
        error_type: ErrorType,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log error with type and context."""
        log_data = {
            "event": "error",
            "error_type": error_type.value,
            "message": message,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.error(f"{error_type.value}: {message}")
        if context:
            self.logger.debug(f"Context: {json.dumps(context, indent=2)}")

    def log_retry(
        self,
        attempt: int,
        max_attempts: int,
        reason: str,
        wait_time_ms: Optional[float] = None,
    ) -> None:
        """Log retry attempt."""
        log_data = {
            "event": "retry",
            "attempt": attempt,
            "max_attempts": max_attempts,
            "reason": reason,
            "wait_time_ms": wait_time_ms,
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.warning(
            f"Retry {attempt}/{max_attempts}: {reason} "
            f"(wait: {wait_time_ms}ms)"
        )

    def log_cache_hit(self, key: str, age_seconds: Optional[float] = None) -> None:
        """Log cache hit."""
        self.logger.debug(f"Cache hit: {key} (age: {age_seconds}s)")

    def log_cache_miss(self, key: str) -> None:
        """Log cache miss."""
        self.logger.debug(f"Cache miss: {key}")

    def log_backend_status(self, available: bool, message: str = "") -> None:
        """Log backend availability status."""
        status = "online" if available else "offline"
        self.logger.info(f"Backend status: {status} {message}")


class ErrorMetrics:
    """Track and report error metrics."""

    def __init__(self):
        """Initialize error metrics tracker."""
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.errors_by_type: Dict[ErrorType, int] = {}
        self.total_retries = 0
        self.total_timeouts = 0
        self.total_connection_errors = 0

    def record_call(self, success: bool, error_type: Optional[ErrorType] = None) -> None:
        """Record API call."""
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            if error_type:
                self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

    def record_retry(self) -> None:
        """Record retry attempt."""
        self.total_retries += 1

    def record_timeout(self) -> None:
        """Record timeout."""
        self.total_timeouts += 1

    def record_connection_error(self) -> None:
        """Record connection error."""
        self.total_connection_errors += 1

    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate_percent": round(self.get_success_rate(), 2),
            "total_retries": self.total_retries,
            "total_timeouts": self.total_timeouts,
            "total_connection_errors": self.total_connection_errors,
            "errors_by_type": {
                k.value: v for k, v in self.errors_by_type.items()
            },
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.errors_by_type = {}
        self.total_retries = 0
        self.total_timeouts = 0
        self.total_connection_errors = 0


class ErrorMonitor:
    """Monitor and track errors for alerting and debugging."""

    def __init__(self, alert_threshold: int = 5):
        """
        Initialize error monitor.

        Args:
            alert_threshold: Number of consecutive errors before alerting
        """
        self.alert_threshold = alert_threshold
        self.consecutive_errors = 0
        self.last_error: Optional[str] = None
        self.last_error_time: Optional[datetime] = None
        self.is_alerting = False

    def record_success(self) -> None:
        """Record successful operation."""
        self.consecutive_errors = 0
        self.is_alerting = False

    def record_error(self, error: str) -> bool:
        """
        Record error and check if alert should trigger.

        Returns:
            True if alert threshold reached, False otherwise
        """
        self.consecutive_errors += 1
        self.last_error = error
        self.last_error_time = datetime.now()

        if self.consecutive_errors >= self.alert_threshold and not self.is_alerting:
            self.is_alerting = True
            return True

        return False

    def get_status(self) -> Dict[str, Any]:
        """Get current monitor status."""
        return {
            "consecutive_errors": self.consecutive_errors,
            "is_alerting": self.is_alerting,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "alert_threshold": self.alert_threshold,
        }

    def reset(self) -> None:
        """Reset monitor state."""
        self.consecutive_errors = 0
        self.last_error = None
        self.last_error_time = None
        self.is_alerting = False


class ErrorTracer:
    """Trace error patterns and provide debugging information."""

    def __init__(self, max_history: int = 100):
        """
        Initialize error tracer.

        Args:
            max_history: Maximum number of errors to keep in history
        """
        self.max_history = max_history
        self.error_history: list = []

    def add_error(
        self,
        error_type: ErrorType,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add error to history."""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type.value,
            "message": message,
            "context": context or {},
        }

        self.error_history.append(error_entry)

        # Keep history size bounded
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)

    def get_recent_errors(self, count: int = 10) -> list:
        """Get recent errors."""
        return self.error_history[-count:]

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error patterns."""
        if not self.error_history:
            return {"message": "No errors recorded"}

        error_types = {}
        for error in self.error_history:
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "total_errors": len(self.error_history),
            "error_types": error_types,
            "most_recent": self.error_history[-1] if self.error_history else None,
        }

    def clear_history(self) -> None:
        """Clear error history."""
        self.error_history.clear()


# Global instances
metrics = ErrorMetrics()
monitor = ErrorMonitor()
tracer = ErrorTracer()


def get_debug_report() -> Dict[str, Any]:
    """Generate comprehensive debug report."""
    return {
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics.get_summary(),
        "monitor_status": monitor.get_status(),
        "error_summary": tracer.get_error_summary(),
        "recent_errors": tracer.get_recent_errors(5),
    }


def export_debug_report(filepath: str) -> None:
    """Export debug report to file."""
    report = get_debug_report()
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(report, f, indent=2)
