"""Unit tests for the extractor module."""
import pytest
import requests.exceptions
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock
from fastapi import UploadFile

from backend.core.extractor import (
    extract_from_file,
    extract_from_url,
    extract_from_youtube,
    extract_source,
)


class TestExtractFromFile:
    """Tests for extract_from_file function."""

    def test_extract_from_file_valid_utf8(self):
        """Test extracting text from a valid UTF-8 file."""
        test_content = b"This is test content"
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(test_content)

        result = extract_from_file(mock_file)

        assert result == "This is test content"

    def test_extract_from_file_utf8_with_special_chars(self):
        """Test extracting UTF-8 content with special characters."""
        test_content = "Hello, World! 你好 🌍".encode("utf-8")
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(test_content)

        result = extract_from_file(mock_file)

        assert "Hello" in result
        assert "World" in result
        assert "你好" in result

    def test_extract_from_file_invalid_encoding(self):
        """Test extracting file with invalid UTF-8 encoding."""
        # Create invalid UTF-8 sequence
        test_content = b"\x80\x81\x82\x83"
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(test_content)

        result = extract_from_file(mock_file)

        # Should not raise, but return empty or decoded string
        assert isinstance(result, str)

    def test_extract_from_file_empty_file(self):
        """Test extracting from empty file."""
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(b"")

        result = extract_from_file(mock_file)

        assert result == ""

    def test_extract_from_file_large_content(self):
        """Test extracting from large file."""
        large_content = b"A" * 100000
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(large_content)

        result = extract_from_file(mock_file)

        assert len(result) == 100000
        assert result == "A" * 100000


class TestExtractFromUrl:
    """Tests for extract_from_url function."""

    @patch("backend.core.extractor.requests.get")
    def test_extract_from_url_success(self, mock_get):
        """Test successful extraction from URL."""
        mock_response = Mock()
        mock_response.text = "<html>Test content</html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = extract_from_url("http://example.com")

        assert result == "<html>Test content</html>"
        mock_get.assert_called_once_with("http://example.com", timeout=15)
        mock_response.raise_for_status.assert_called_once()

    @patch("backend.core.extractor.requests.get")
    def test_extract_from_url_timeout(self, mock_get):
        """Test URL extraction with timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()

        with pytest.raises(requests.exceptions.Timeout):
            extract_from_url("http://example.com")

    @patch("backend.core.extractor.requests.get")
    def test_extract_from_url_connection_error(self, mock_get):
        """Test URL extraction with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(requests.exceptions.ConnectionError):
            extract_from_url("http://example.com")

    @patch("backend.core.extractor.requests.get")
    def test_extract_from_url_http_error(self, mock_get):
        """Test URL extraction with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            extract_from_url("http://example.com/notfound")

    @patch("backend.core.extractor.requests.get")
    def test_extract_from_url_respects_timeout(self, mock_get):
        """Test that timeout parameter is correctly passed."""
        mock_response = Mock()
        mock_response.text = "content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        extract_from_url("http://example.com")

        # Verify timeout is set to 15
        assert mock_get.call_args[1]["timeout"] == 15

    @patch("backend.core.extractor.requests.get")
    def test_extract_from_url_various_content_types(self, mock_get):
        """Test extraction from URLs with various content types."""
        test_cases = [
            "<html><body>Web page</body></html>",
            "Plain text content",
            '{"json": "content"}',
            "<?xml version='1.0'?>",
        ]

        for content in test_cases:
            mock_response = Mock()
            mock_response.text = content
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = extract_from_url("http://example.com")
            assert result == content


class TestExtractFromYoutube:
    """Tests for extract_from_youtube function."""

    def test_extract_from_youtube_standard_url(self):
        """Test YouTube extraction returns placeholder with correct URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = extract_from_youtube(url)

        assert "Transcript placeholder for:" in result
        assert url in result

    def test_extract_from_youtube_short_url(self):
        """Test YouTube extraction with short URL format."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        result = extract_from_youtube(url)

        assert "Transcript placeholder for:" in result
        assert url in result

    def test_extract_from_youtube_returns_string(self):
        """Test that function always returns a string."""
        result = extract_from_youtube("https://youtube.com/watch?v=test")

        assert isinstance(result, str)
        assert len(result) > 0


class TestExtractSource:
    """Tests for extract_source function - main entry point."""

    def test_extract_source_with_file(self):
        """Test extraction when file is provided."""
        test_content = b"File content"
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(test_content)

        result = extract_source(source_url=None, file=mock_file)

        assert result == "File content"

    def test_extract_source_file_takes_priority_over_url(self):
        """Test that file takes priority over URL."""
        test_content = b"File content"
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(test_content)

        with patch("backend.core.extractor.extract_from_url") as mock_extract_url:
            result = extract_source(
                source_url="http://example.com", file=mock_file
            )

            assert result == "File content"
            mock_extract_url.assert_not_called()

    def test_extract_source_none_file_none_url(self):
        """Test extraction with both file and URL as None."""
        result = extract_source(source_url=None, file=None)

        assert result == ""

    @patch("backend.core.extractor.extract_from_youtube")
    def test_extract_source_youtube_com(self, mock_youtube):
        """Test extraction recognizes youtube.com URL."""
        mock_youtube.return_value = "Transcript for YouTube"

        result = extract_source(
            source_url="https://www.youtube.com/watch?v=test", file=None
        )

        assert result == "Transcript for YouTube"
        mock_youtube.assert_called_once()

    @patch("backend.core.extractor.extract_from_youtube")
    def test_extract_source_youtu_be(self, mock_youtube):
        """Test extraction recognizes youtu.be short URL."""
        mock_youtube.return_value = "Transcript for YouTube"

        result = extract_source(source_url="https://youtu.be/test", file=None)

        assert result == "Transcript for YouTube"
        mock_youtube.assert_called_once()

    @patch("backend.core.extractor.extract_from_url")
    def test_extract_source_regular_url(self, mock_url):
        """Test extraction for regular HTTP URL."""
        mock_url.return_value = "<html>Web content</html>"

        result = extract_source(source_url="http://example.com", file=None)

        assert result == "<html>Web content</html>"
        mock_url.assert_called_once_with("http://example.com")

    @patch("backend.core.extractor.extract_from_url")
    def test_extract_source_https_url(self, mock_url):
        """Test extraction for HTTPS URL."""
        mock_url.return_value = "Secure content"

        result = extract_source(source_url="https://example.com", file=None)

        assert result == "Secure content"
        mock_url.assert_called_once()

    def test_extract_source_empty_url_string(self):
        """Test extraction with empty string URL."""
        result = extract_source(source_url="", file=None)

        assert result == ""

    @patch("backend.core.extractor.extract_from_youtube")
    @patch("backend.core.extractor.extract_from_url")
    def test_extract_source_youtube_priority(self, mock_url, mock_youtube):
        """Test that YouTube extraction is used for YouTube URLs, not generic extraction."""
        mock_youtube.return_value = "YouTube transcript"
        mock_url.return_value = "Generic extraction"

        result = extract_source(
            source_url="https://www.youtube.com/watch?v=abc123", file=None
        )

        assert result == "YouTube transcript"
        mock_youtube.assert_called_once()
        mock_url.assert_not_called()
