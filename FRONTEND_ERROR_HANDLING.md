# Frontend Error Handling & Retry Logic - Complete Implementation

## Overview

The AOSB Frontend now includes **comprehensive error handling and retry logic** for all backend API calls. This implementation provides:

✅ **Automatic Retry with Exponential Backoff** - Gracefully handles transient failures
✅ **Timeout Handling** - Configurable request timeouts with user-friendly messages
✅ **Connection Error Recovery** - Detects when backend is down and shows offline mode
✅ **Response Caching** - Serves cached results when backend is unavailable
✅ **Health Monitoring** - Continuous backend availability checks
✅ **User-Friendly Error Messages** - Clear guidance on what went wrong and what to do
✅ **Structured Logging** - Comprehensive error tracking and debugging
✅ **Error Metrics & Monitoring** - Track error patterns and system health

## Architecture

### Components

```
frontend/
├── app.py                      # Main Streamlit app (UPDATED)
├── resilient_client.py         # HTTP client with retry logic (NEW)
├── error_handlers.py           # UI error display utilities (NEW)
├── config.py                   # Frontend configuration (NEW)
├── monitoring.py               # Logging & metrics tracking (NEW)
└── components/                 # Reusable UI components

tests/
└── test_frontend_errors.py     # Error handling tests (NEW)
```

## Features

### 1. Resilient HTTP Client

**File**: `frontend/resilient_client.py`

Features:
- Automatic retry on transient failures (connection errors, timeouts)
- Exponential backoff between retry attempts
- Configurable timeout and max retries
- Response caching for offline support
- Error classification and user-friendly messages

**Usage**:
```python
from frontend.resilient_client import ResilientClient, RetryConfig

# Create client with custom retry config
config = RetryConfig(
    max_retries=3,
    backoff_factor=0.5,
    timeout=10.0,
)
client = ResilientClient(config=config, cache_enabled=True)

# Make API call - automatically retries on failure
response = client.get("http://backend:8000/health")

if response.success:
    data = response.data
else:
    print(f"Error: {response.message}")
    print(f"Type: {response.error_type}")
```

**Key Classes**:
- `ResilientClient` - Main HTTP client with retry logic
- `APIResponse` - Structured response with error information
- `RetryConfig` - Configuration for retry behavior
- `ErrorType` - Enum for error classification

### 2. Error Handlers

**File**: `frontend/error_handlers.py`

Features:
- `UIErrorHandler` - Display errors in Streamlit UI
- `BackendHealthCheck` - Monitor backend availability
- `FallbackContent` - Offline mode UI components
- `ConditionalDisplay` - Context managers for UI layout
- `@handle_api_call` - Decorator for automatic error handling

**Usage**:
```python
from frontend.error_handlers import UIErrorHandler, BackendHealthCheck

# Show error in UI
UIErrorHandler.show_error(response, "Data Ingestion")

# Check backend health
health_check = BackendHealthCheck(client, "http://localhost:8000")
if health_check.check_health():
    # Backend available
else:
    # Show offline mode
    UIErrorHandler.show_offline_mode()

# Use decorator for automatic handling
@handle_api_call("Query Processing")
def process_query(query: str) -> APIResponse:
    return client.post(f"{BACKEND_URL}/query", json={"query": query})
```

### 3. Configuration

**File**: `frontend/config.py`

Environment variables:
```bash
# Backend connection
BACKEND_URL=http://localhost:8000
REQUEST_TIMEOUT=10.0
MAX_RETRIES=3
BACKOFF_FACTOR=0.5

# Caching
ENABLE_CACHE=true
CACHE_TTL=3600

# Health checks
HEALTH_CHECK_INTERVAL=30

# UI settings
SHOW_ADVANCED_SETTINGS=false
ENABLE_OFFLINE_MODE=true

# Features
ENABLE_INGEST=true
ENABLE_QUERY=true
ENABLE_STATS=true
```

### 4. Monitoring & Logging

**File**: `frontend/monitoring.py`

Features:
- `StructuredLogger` - Structured logging for debugging
- `ErrorMetrics` - Track call success/failure rates
- `ErrorMonitor` - Detect and alert on error patterns
- `ErrorTracer` - Maintain error history for debugging

**Usage**:
```python
from frontend.monitoring import metrics, monitor, tracer

# Record API call
metrics.record_call(success=True)
metrics.record_call(success=False, error_type=ErrorType.TIMEOUT)

# Check metrics
summary = metrics.get_summary()
print(f"Success rate: {summary['success_rate_percent']}%")

# Monitor error patterns
if monitor.record_error("Connection refused"):
    # Alert threshold reached
    notify_admin("Backend appears to be down")

# Trace errors
tracer.add_error(ErrorType.TIMEOUT, "Request timeout", context={"url": url})
report = tracer.get_error_summary()
```

## Updated Frontend UI (frontend/app.py)

### New Features

1. **Backend Status Indicator**
   - Sidebar shows real-time backend availability
   - Automatic health checks at startup and periodically
   - Visual indicators (✅ Online / ❌ Offline)

2. **Offline Mode**
   - When backend is down, UI gracefully degraded
   - Shows cached results from previous queries
   - Suggests retry options
   - Queue ingestion for later

3. **Error Messages**
   - User-friendly error messages
   - Technical details in expandable section
   - Helpful recovery suggestions
   - Retry hints for transient errors

4. **Cache Management**
   - Clear cache button in sidebar
   - Cache status shown on results ("📦 From cache")
   - Configurable TTL

5. **System Status**
   - Show backend URL and configuration
   - Display request timeout and retry settings
   - Last refresh timestamp

### UI Tabs

#### 💬 Chat Tab
- Ask questions against knowledge base
- Shows results or graceful error message
- Indicates if result is cached
- Retry suggestions

#### 📥 Ingest Tab
- URL or file upload
- Only available when backend online
- Clear success/error messages
- Shows processed chunk count

#### 📊 Stats Tab
- Displays metrics in card format
- Shows cached stats when offline
- Full JSON for advanced users
- Last updated timestamp

## Error Handling Flow

```
API Call Request
    ↓
[ResilientClient]
    ↓
    ├─ Check cache (if enabled)
    │   ├─ Cache hit → Return cached response
    │   └─ Cache miss → Continue to API
    ↓
[Make HTTP Request]
    ↓
    ├─ Success (200-299) → Cache & return
    │
    ├─ Transient Error (408, 502-504, timeout, connection)
    │   → Retry with exponential backoff
    │   → If max retries exceeded → Return error
    │
    └─ Client Error (400-499, except 408) → Return error immediately

[APIResponse]
    ↓
[Streamlit UI]
    ├─ Success → Show data
    ├─ Cached result → Show data + "📦 From cache"
    ├─ Transient error → Show friendly message + retry button
    ├─ Connection error → Show offline mode UI
    └─ Server error → Show error details + suggestions
```

## Configuration Examples

### Development Configuration

```python
from frontend.config import FrontendConfig

config = FrontendConfig.for_development()
# Enables debug logging, shows advanced settings, offline mode enabled
```

### Production Configuration

```python
config = FrontendConfig.for_production()
# Warning level logging, hides advanced settings, offline mode disabled
```

### Custom Configuration

```python
from frontend.resilient_client import RetryConfig

retry_config = RetryConfig(
    max_retries=5,              # More aggressive retry
    backoff_factor=1.0,         # Longer backoff
    timeout=30.0,               # Longer timeout
    retry_on_status_codes=[408, 429, 500, 502, 503, 504],
)
```

## Testing

### Run Frontend Error Tests

```bash
# All frontend error tests
pytest tests/test_frontend_errors.py -v

# Specific test class
pytest tests/test_frontend_errors.py::TestResilientClient -v

# Specific test
pytest tests/test_frontend_errors.py::TestResilientClient::test_successful_get_request -v

# With coverage
pytest tests/test_frontend_errors.py --cov=frontend --cov-report=html
```

### Test Coverage

The test suite includes:
- ✅ APIResponse structure validation
- ✅ RetryConfig validation
- ✅ Successful API calls
- ✅ Timeout handling with retry
- ✅ Connection error handling
- ✅ HTTP error codes (4xx, 5xx)
- ✅ Response caching
- ✅ Invalid JSON handling
- ✅ Error metrics tracking
- ✅ Error monitoring and alerting
- ✅ Error tracing and history
- ✅ Health check monitoring
- ✅ Error classification

**Total Tests**: 40+ test cases

## Environment Variables

### Connection Settings

```bash
BACKEND_URL=http://localhost:8000        # Backend URL
REQUEST_TIMEOUT=10.0                     # Timeout in seconds
MAX_RETRIES=3                            # Number of retry attempts
BACKOFF_FACTOR=0.5                       # Exponential backoff multiplier
```

### Caching Settings

```bash
ENABLE_CACHE=true                        # Enable response caching
CACHE_TTL=3600                           # Cache time-to-live in seconds
```

### Health Check Settings

```bash
HEALTH_CHECK_INTERVAL=30                 # Health check interval in seconds
```

### UI Settings

```bash
SHOW_ADVANCED_SETTINGS=false             # Show/hide advanced settings
ENABLE_OFFLINE_MODE=true                 # Enable graceful offline mode
```

### Feature Flags

```bash
ENABLE_INGEST=true                       # Enable ingestion tab
ENABLE_QUERY=true                        # Enable query tab
ENABLE_STATS=true                        # Enable stats tab
```

## Error Recovery Strategies

### Scenario 1: Backend Temporarily Down

1. User clicks "Ask" button
2. ResilientClient detects connection error
3. Automatically retries with exponential backoff (3 attempts)
4. If all retries fail:
   - Shows "Cannot reach server" message
   - Suggests checking internet connection
   - Offers "Try Again" button
   - Shows "Refresh" option
5. If cached results available, they're shown with "📦 From cache" label

### Scenario 2: Slow Backend Response

1. Request timeout occurs (10s default)
2. ResilientClient detects timeout
3. Automatically retries with backoff
4. If timeout persists:
   - Shows "Server is taking too long" message
   - Suggests trying again or with simpler query
   - Offers retry with longer timeout

### Scenario 3: Server Error (502 Bad Gateway)

1. Backend returns 502 status
2. ResilientClient recognizes as retryable
3. Retries with backoff
4. If persists after retries:
   - Shows error message
   - Suggests waiting for maintenance to complete
   - Offers to try again

### Scenario 4: Invalid Input (400 Bad Request)

1. User sends malformed request
2. Backend returns 400 status
3. No retry attempted (client error)
4. Shows error message explaining what's wrong
5. Suggests checking input

## Monitoring & Debugging

### Check Metrics

```python
from frontend.monitoring import metrics

summary = metrics.get_summary()
print(f"Total calls: {summary['total_calls']}")
print(f"Success rate: {summary['success_rate_percent']}%")
print(f"Errors by type: {summary['errors_by_type']}")
```

### View Error History

```python
from frontend.monitoring import tracer

recent_errors = tracer.get_recent_errors(count=10)
for error in recent_errors:
    print(f"{error['timestamp']}: {error['error_type']} - {error['message']}")
```

### Generate Debug Report

```python
from frontend.monitoring import get_debug_report, export_debug_report

report = get_debug_report()
print(report)

# Export to file
export_debug_report("debug_report.json")
```

### Check Alert Status

```python
from frontend.monitoring import monitor

if monitor.is_alerting:
    print(f"Alert! {monitor.consecutive_errors} consecutive errors")
    print(f"Last error: {monitor.last_error}")
```

## Performance Tuning

### Increase Cache TTL for Better Offline Support

```bash
CACHE_TTL=7200  # 2 hours instead of 1 hour
```

### Reduce Retry Attempts for Faster Failure Feedback

```bash
MAX_RETRIES=1   # Fail fast after 1 retry
BACKOFF_FACTOR=0.1  # Shorter wait between retries
```

### Longer Timeout for Slow Networks

```bash
REQUEST_TIMEOUT=30.0  # 30 seconds instead of 10
```

### More Aggressive Retry for Unreliable Networks

```bash
MAX_RETRIES=5
BACKOFF_FACTOR=1.0  # Exponential: 1s, 2s, 4s, 8s, 16s
```

## Best Practices

1. **Always check `response.success`** before accessing `response.data`
2. **Use the decorator** `@handle_api_call()` for consistent error handling
3. **Enable caching** for better offline experience
4. **Monitor health** regularly with `BackendHealthCheck`
5. **Log errors** with structured logger for debugging
6. **Track metrics** to understand system health
7. **Review error history** to spot patterns
8. **Test with backend down** to verify graceful degradation

## Migration Guide

### From Old Code

```python
# Old approach - crashes on connection error
import requests
resp = requests.post(f"{BACKEND_URL}/query", json=payload)
data = resp.json()
```

### To New Approach

```python
# New approach - handles errors gracefully
from frontend.resilient_client import ResilientClient

client = ResilientClient()
response = client.post(f"{BACKEND_URL}/query", json=payload)

if response.success:
    data = response.data
    # Use data
else:
    # Handle error gracefully
    UIErrorHandler.show_error(response, "Query")
```

## Troubleshooting

### "Connection refused" errors still appear

**Solution**: 
- Check `BACKEND_URL` environment variable
- Verify backend is running: `curl http://localhost:8000/health`
- Check network connectivity

### Retry not working

**Solution**:
- Verify `MAX_RETRIES` > 0
- Check `BACKOFF_FACTOR` > 0
- Review logs for retry attempts

### Cache not working

**Solution**:
- Verify `ENABLE_CACHE=true`
- Check cache size: `len(client._cache)`
- Clear cache if needed: `client.clear_cache()`

### Offline mode not shown

**Solution**:
- Verify `ENABLE_OFFLINE_MODE=true`
- Check backend health: `health_check.is_available`
- Force health check: `health_check.check_health(force=True)`

## Future Enhancements

- [ ] Circuit breaker pattern for repeated failures
- [ ] Request rate limiting and backpressure
- [ ] Persistent cache (SQLite/Redis)
- [ ] Advanced retry policies (jitter, max backoff)
- [ ] Request prioritization queue
- [ ] Telemetry export (Prometheus, CloudWatch)
- [ ] User-facing status page
- [ ] Batch request optimization

## Summary

The updated frontend now provides **enterprise-grade error handling** with:

✅ Automatic retry with exponential backoff
✅ Graceful fallback when backend is unavailable
✅ Caching for offline support
✅ Health monitoring
✅ User-friendly error messages
✅ Comprehensive logging and metrics
✅ 40+ test cases for reliability

This significantly **improves user experience** when the backend is temporarily unavailable or experiencing issues.

---

**Implementation Date**: 2025-12-08
**Status**: ✅ Complete and Production-Ready
