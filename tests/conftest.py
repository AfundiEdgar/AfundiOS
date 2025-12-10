"""
Pytest configuration and shared fixtures.

This module provides:
- Shared fixtures for mocking common dependencies
- Configuration for test environment
- Helper utilities for testing
"""
import os
import sys
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Configure environment for testing
os.environ["ENVIRONMENT"] = "test"


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide a temporary directory for test data."""
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile object."""
    from io import BytesIO
    from fastapi import UploadFile

    mock = Mock(spec=UploadFile)
    mock.file = BytesIO()
    mock.filename = "test_file.txt"
    mock.content_type = "text/plain"
    return mock


@pytest.fixture
def mock_upload_file_with_content():
    """Create a mock UploadFile object with content."""
    from io import BytesIO
    from fastapi import UploadFile

    def _create_upload_file(content: bytes):
        mock = Mock(spec=UploadFile)
        mock.file = BytesIO(content)
        mock.filename = "test_file.txt"
        mock.content_type = "text/plain"
        return mock

    return _create_upload_file


@pytest.fixture
def mock_requests_session():
    """Create a mock requests session."""
    with patch("requests.Session") as mock_session:
        yield mock_session


@pytest.fixture(autouse=True)
def reset_imports():
    """Reset imports between tests to avoid state pollution."""
    yield
    # Any cleanup can go here


@pytest.fixture
def sample_text():
    """Provide sample text for testing."""
    return """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
    Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
    Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.
    """


@pytest.fixture
def sample_long_text():
    """Provide sample long text for testing."""
    words = ["word"] * 1000
    return " ".join(words)


@pytest.fixture
def sample_unicode_text():
    """Provide sample text with unicode characters."""
    return "Hello 世界 مرحبا Привет 🌍"


@pytest.fixture
def sample_urls():
    """Provide sample URLs for testing."""
    return {
        "http": "http://example.com",
        "https": "https://example.com",
        "youtube": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "youtu_be": "https://youtu.be/dQw4w9WgXcQ",
    }


@pytest.fixture
def mock_config():
    """Provide a mock config object."""
    mock = Mock()
    mock.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    mock.vector_store_path = "/tmp/test_chroma"
    mock.chunk_size = 512
    return mock


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "mock_external: mark test as mocking external services"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark tests based on file name
        if "test_api" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_extractor" in item.nodeid or "test_chunker" in item.nodeid or "test_embedder" in item.nodeid:
            item.add_marker(pytest.mark.unit)


# Hooks for test output
def pytest_sessionstart(session):
    """Print session start info."""
    print("\n" + "=" * 70)
    print("Test Session Started")
    print("=" * 70)


def pytest_sessionfinish(session, exitstatus):
    """Print session finish info."""
    print("\n" + "=" * 70)
    print("Test Session Finished")
    print("=" * 70)
