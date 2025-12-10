"""Unit tests for frontend error handling and resilience."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from frontend.resilient_client import (
    ResilientClient,
    RetryConfig,
    APIResponse,
    ErrorType,
)
from frontend.error_handlers import UIErrorHandler, BackendHealthCheck, FallbackContent
from frontend.monitoring import (
    ErrorMetrics,
    ErrorMonitor,
    ErrorTracer,
    StructuredLogger,
)


class TestAPIResponse:
    """Tests for APIResponse data structure."""

    def test_success_response(self):
        """Test successful API response."""
        response = APIResponse(success=True, data={"key": "value"})
        assert response.success
        assert response.data == {"key": "value"}
        assert bool(response) is True

    def test_error_response(self):
        """Test error API response."""
        response = APIResponse(
            success=False,
            error="Connection refused",
            error_type=ErrorType.CONNECTION_ERROR,
        )
        assert not response.success
        assert response.error == "Connection refused"
        assert response.error_type == ErrorType.CONNECTION_ERROR
        assert bool(response) is False

    def test_cached_response(self):
        """Test cached response indicator."""
        response = APIResponse(success=True, data={"cached": True}, is_cached=True)
        assert response.is_cached is True

    def test_retry_count(self):
        """Test retry count tracking."""
        response = APIResponse(success=False, error="Timeout", retry_count=3)
        assert response.retry_count == 3


class TestRetryConfig:
    """Tests for retry configuration."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.backoff_factor == 0.5
        assert config.timeout == 10.0
        assert 502 in config.retry_on_status_codes

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_retries=5,
            backoff_factor=0.2,
            timeout=20.0,
        )
        assert config.max_retries == 5
        assert config.backoff_factor == 0.2
        assert config.timeout == 20.0

    def test_custom_retry_codes(self):
        """Test custom retry status codes."""
        config = RetryConfig(retry_on_status_codes=[500, 502, 503])
        assert 500 in config.retry_on_status_codes
        assert 502 in config.retry_on_status_codes


class TestResilientClient:
    """Tests for resilient HTTP client."""

    def test_client_initialization(self):
        """Test client initialization."""
        config = RetryConfig(max_retries=2)
        client = ResilientClient(config=config)
        assert client.config.max_retries == 2
        assert client.cache_enabled is True

    def test_client_without_cache(self):
        """Test client with cache disabled."""
        client = ResilientClient(cache_enabled=False)
        assert client.cache_enabled is False

    @patch("frontend.resilient_client.requests.Session.request")
    def test_successful_get_request(self, mock_request):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response

        client = ResilientClient()
        response = client.get("http://example.com/api")

        assert response.success
        assert response.data == {"result": "success"}
        assert response.status_code == 200

    @patch("frontend.resilient_client.requests.Session.request")
    def test_timeout_with_retry(self, mock_request):
        """Test timeout handling with automatic retry."""
        import requests

        mock_request.side_effect = requests.Timeout()

        client = ResilientClient(config=RetryConfig(max_retries=1))
        response = client.get("http://example.com/api")

        assert not response.success
        assert response.error_type == ErrorType.TIMEOUT
        assert response.retry_count == 1

    @patch("frontend.resilient_client.requests.Session.request")
    def test_connection_error_with_retry(self, mock_request):
        """Test connection error with automatic retry."""
        import requests

        mock_request.side_effect = requests.ConnectionError("Connection refused")

        client = ResilientClient(config=RetryConfig(max_retries=1))
        response = client.get("http://example.com/api")

        assert not response.success
        assert response.error_type == ErrorType.CONNECTION_ERROR
        assert "Connection refused" in response.error

    @patch("frontend.resilient_client.requests.Session.request")
    def test_server_error_502(self, mock_request):
        """Test 502 Bad Gateway error handling."""
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.text = "Bad Gateway"
        mock_request.return_value = mock_response

        client = ResilientClient(config=RetryConfig(max_retries=1))
        response = client.get("http://example.com/api")

        assert not response.success
        assert response.status_code == 502

    @patch("frontend.resilient_client.requests.Session.request")
    def test_client_error_400(self, mock_request):
        """Test 400 Bad Request error handling."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_request.return_value = mock_response

        client = ResilientClient()
        response = client.get("http://example.com/api")

        assert not response.success
        assert response.status_code == 400
        assert response.error_type == ErrorType.CLIENT_ERROR

    @patch("frontend.resilient_client.requests.Session.request")
    def test_cache_hit_on_get(self, mock_request):
        """Test caching of GET requests."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"cached": "data"}'
        mock_response.json.return_value = {"cached": "data"}
        mock_request.return_value = mock_response

        client = ResilientClient(cache_enabled=True)

        # First request hits API
        response1 = client.get("http://example.com/cached")
        assert response1.success
        assert not response1.is_cached
        assert mock_request.call_count == 1

        # Second request should hit cache
        response2 = client.get("http://example.com/cached")
        assert response2.success
        assert response2.is_cached
        # No additional API call made
        assert mock_request.call_count == 1

    def test_cache_clear(self):
        """Test cache clearing."""
        client = ResilientClient(cache_enabled=True)
        client._cache = {"key": "value"}
        client.clear_cache()
        assert len(client._cache) == 0

    @patch("frontend.resilient_client.requests.Session.request")
    def test_post_request(self, mock_request):
        """Test POST request."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.text = '{"id": 1}'
        mock_response.json.return_value = {"id": 1}
        mock_request.return_value = mock_response

        client = ResilientClient()
        response = client.post("http://example.com/api", json={"data": "test"})

        assert response.success
        assert response.data == {"id": 1}

    @patch("frontend.resilient_client.requests.Session.request")
    def test_invalid_json_response(self, mock_request):
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Invalid JSON"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_request.return_value = mock_response

        client = ResilientClient()
        response = client.get("http://example.com/api")

        assert not response.success
        assert "Invalid JSON" in response.error


class TestErrorMetrics:
    """Tests for error metrics tracking."""

    def test_record_successful_call(self):
        """Test recording successful API call."""
        metrics = ErrorMetrics()
        metrics.record_call(success=True)
        assert metrics.total_calls == 1
        assert metrics.successful_calls == 1
        assert metrics.failed_calls == 0

    def test_record_failed_call(self):
        """Test recording failed API call."""
        metrics = ErrorMetrics()
        metrics.record_call(success=False, error_type=ErrorType.TIMEOUT)
        assert metrics.total_calls == 1
        assert metrics.successful_calls == 0
        assert metrics.failed_calls == 1
        assert ErrorType.TIMEOUT in metrics.errors_by_type

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        metrics = ErrorMetrics()
        metrics.record_call(success=True)
        metrics.record_call(success=True)
        metrics.record_call(success=False)
        assert metrics.get_success_rate() == pytest.approx(66.67, abs=0.1)

    def test_metrics_summary(self):
        """Test metrics summary generation."""
        metrics = ErrorMetrics()
        metrics.record_call(success=True)
        metrics.record_call(success=False, error_type=ErrorType.TIMEOUT)
        metrics.record_retry()

        summary = metrics.get_summary()
        assert summary["total_calls"] == 2
        assert summary["successful_calls"] == 1
        assert summary["failed_calls"] == 1
        assert summary["total_retries"] == 1

    def test_metrics_reset(self):
        """Test metrics reset."""
        metrics = ErrorMetrics()
        metrics.record_call(success=True)
        metrics.reset()
        assert metrics.total_calls == 0
        assert metrics.successful_calls == 0


class TestErrorMonitor:
    """Tests for error monitor and alerting."""

    def test_monitor_success_resets_error_count(self):
        """Test that success resets consecutive error count."""
        monitor = ErrorMonitor(alert_threshold=3)
        monitor.record_error("Error 1")
        monitor.record_error("Error 2")
        monitor.record_success()
        assert monitor.consecutive_errors == 0

    def test_monitor_alert_threshold(self):
        """Test alert threshold detection."""
        monitor = ErrorMonitor(alert_threshold=3)
        assert monitor.record_error("Error 1") is False
        assert monitor.record_error("Error 2") is False
        assert monitor.record_error("Error 3") is True

    def test_monitor_status(self):
        """Test monitor status reporting."""
        monitor = ErrorMonitor(alert_threshold=2)
        monitor.record_error("Connection refused")
        status = monitor.get_status()

        assert status["consecutive_errors"] == 1
        assert status["last_error"] == "Connection refused"
        assert status["is_alerting"] is False

    def test_monitor_reset(self):
        """Test monitor reset."""
        monitor = ErrorMonitor()
        monitor.record_error("Error")
        monitor.reset()
        assert monitor.consecutive_errors == 0
        assert monitor.is_alerting is False


class TestErrorTracer:
    """Tests for error tracing and history."""

    def test_add_error_to_history(self):
        """Test adding error to history."""
        tracer = ErrorTracer()
        tracer.add_error(
            ErrorType.TIMEOUT,
            "Request timeout",
            context={"url": "http://example.com"},
        )
        assert len(tracer.error_history) == 1
        assert tracer.error_history[0]["error_type"] == "timeout"

    def test_max_history_limit(self):
        """Test maximum history size limit."""
        tracer = ErrorTracer(max_history=10)
        for i in range(20):
            tracer.add_error(ErrorType.TIMEOUT, f"Error {i}")
        assert len(tracer.error_history) == 10

    def test_get_recent_errors(self):
        """Test retrieving recent errors."""
        tracer = ErrorTracer()
        for i in range(5):
            tracer.add_error(ErrorType.TIMEOUT, f"Error {i}")
        recent = tracer.get_recent_errors(count=3)
        assert len(recent) == 3

    def test_error_summary(self):
        """Test error summary generation."""
        tracer = ErrorTracer()
        tracer.add_error(ErrorType.TIMEOUT, "Timeout 1")
        tracer.add_error(ErrorType.TIMEOUT, "Timeout 2")
        tracer.add_error(ErrorType.CONNECTION_ERROR, "Connection error")

        summary = tracer.get_error_summary()
        assert summary["total_errors"] == 3
        assert summary["error_types"]["timeout"] == 2
        assert summary["error_types"]["connection_error"] == 1

    def test_clear_history(self):
        """Test clearing error history."""
        tracer = ErrorTracer()
        tracer.add_error(ErrorType.TIMEOUT, "Error")
        tracer.clear_history()
        assert len(tracer.error_history) == 0


class TestBackendHealthCheck:
    """Tests for backend health monitoring."""

    @patch("frontend.error_handlers.ResilientClient.get")
    def test_health_check_success(self, mock_get):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.success = True
        mock_get.return_value = mock_response

        client = Mock()
        client.get = mock_get
        health_check = BackendHealthCheck(client, "http://localhost:8000")

        assert health_check.check_health(force=True) is True
        assert health_check.is_available is True

    @patch("frontend.error_handlers.ResilientClient.get")
    def test_health_check_failure(self, mock_get):
        """Test failed health check."""
        mock_response = Mock()
        mock_response.success = False
        mock_get.return_value = mock_response

        client = Mock()
        client.get = mock_get
        health_check = BackendHealthCheck(client, "http://localhost:8000")

        assert health_check.check_health(force=True) is False
        assert health_check.is_available is False


class TestStructuredLogger:
    """Tests for structured logging."""

    def test_logger_creation(self):
        """Test logger creation."""
        logger = StructuredLogger("test_logger", log_level="DEBUG")
        assert logger.logger.name == "test_logger"

    def test_log_api_call(self):
        """Test logging API calls."""
        logger = StructuredLogger("test_logger")
        # Should not raise exception
        logger.log_api_call(
            method="GET",
            url="http://example.com",
            success=True,
            status_code=200,
            duration_ms=100,
        )

    def test_log_error(self):
        """Test logging errors."""
        logger = StructuredLogger("test_logger")
        # Should not raise exception
        logger.log_error(
            error_type=ErrorType.TIMEOUT,
            message="Request timeout",
            context={"url": "http://example.com"},
        )


class TestErrorTypeClassification:
    """Tests for error type classification."""

    def test_classify_timeout_error(self):
        """Test timeout error classification."""
        client = ResilientClient()
        import requests

        error_type = client._classify_error(requests.Timeout())
        assert error_type == ErrorType.TIMEOUT

    def test_classify_connection_error(self):
        """Test connection error classification."""
        client = ResilientClient()
        import requests

        error_type = client._classify_error(requests.ConnectionError())
        assert error_type == ErrorType.CONNECTION_ERROR

    def test_classify_server_error_by_status(self):
        """Test server error classification by status code."""
        client = ResilientClient()
        error_type = client._classify_error(None, status_code=502)
        assert error_type == ErrorType.SERVER_ERROR

    def test_classify_client_error_by_status(self):
        """Test client error classification by status code."""
        client = ResilientClient()
        error_type = client._classify_error(None, status_code=400)
        assert error_type == ErrorType.CLIENT_ERROR
