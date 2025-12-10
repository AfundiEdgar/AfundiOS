"""Unit tests for the chunker module."""
import pytest
from backend.core.chunker import simple_chunk


class TestSimpleChunk:
    """Tests for simple_chunk function."""

    def test_simple_chunk_basic(self):
        """Test basic chunking with default max_tokens."""
        text = "word1 word2 word3 word4 word5"
        result = simple_chunk(text, max_tokens=2)

        assert len(result) == 3
        assert result[0] == "word1 word2"
        assert result[1] == "word3 word4"
        assert result[2] == "word5"

    def test_simple_chunk_empty_string(self):
        """Test chunking empty string."""
        result = simple_chunk("", max_tokens=512)

        assert result == []

    def test_simple_chunk_single_word(self):
        """Test chunking single word."""
        result = simple_chunk("hello", max_tokens=512)

        assert len(result) == 1
        assert result[0] == "hello"

    def test_simple_chunk_exact_boundary(self):
        """Test chunking where text is exactly max_tokens."""
        text = "word1 word2 word3"
        result = simple_chunk(text, max_tokens=3)

        assert len(result) == 1
        assert result[0] == "word1 word2 word3"

    def test_simple_chunk_whitespace_handling(self):
        """Test that multiple whitespaces are handled correctly."""
        text = "word1  word2   word3"  # Multiple spaces
        result = simple_chunk(text, max_tokens=2)

        # split() handles multiple spaces naturally
        assert len(result) >= 1
        assert "word1" in result[0]
        assert "word2" in result[0]

    def test_simple_chunk_large_text_small_max_tokens(self):
        """Test chunking large text with small max_tokens."""
        text = " ".join([f"word{i}" for i in range(100)])
        result = simple_chunk(text, max_tokens=10)

        # Should have 10 chunks (100 words / 10 tokens per chunk)
        assert len(result) == 10
        for chunk in result:
            word_count = len(chunk.split())
            assert word_count == 10

    def test_simple_chunk_default_max_tokens(self):
        """Test chunking with default max_tokens (512)."""
        text = " ".join([f"word{i}" for i in range(600)])
        result = simple_chunk(text)

        # First chunk should have 512 words, second should have remaining 88
        assert len(result) == 2
        assert len(result[0].split()) == 512
        assert len(result[1].split()) == 88

    def test_simple_chunk_preserves_word_order(self):
        """Test that word order is preserved."""
        text = "alpha beta gamma delta epsilon"
        result = simple_chunk(text, max_tokens=2)

        words = []
        for chunk in result:
            words.extend(chunk.split())

        assert words == ["alpha", "beta", "gamma", "delta", "epsilon"]

    def test_simple_chunk_max_tokens_one(self):
        """Test chunking with max_tokens=1 (one word per chunk)."""
        text = "one two three four"
        result = simple_chunk(text, max_tokens=1)

        assert len(result) == 4
        assert result == ["one", "two", "three", "four"]

    def test_simple_chunk_chunk_content_format(self):
        """Test that chunks maintain word format."""
        text = "word1 word2 word3 word4"
        result = simple_chunk(text, max_tokens=2)

        # Each chunk should be space-separated words
        for chunk in result:
            assert isinstance(chunk, str)
            assert " " in chunk or len(chunk.split()) == 1

    def test_simple_chunk_no_trailing_spaces(self):
        """Test that chunks don't have leading/trailing spaces."""
        text = "word1 word2 word3 word4"
        result = simple_chunk(text, max_tokens=2)

        for chunk in result:
            assert chunk == chunk.strip()

    def test_simple_chunk_unicode_words(self):
        """Test chunking with unicode characters."""
        text = "你好 世界 hello 世界"
        result = simple_chunk(text, max_tokens=2)

        assert len(result) == 2
        assert "你好" in result[0]
        assert "世界" in result[1]

    def test_simple_chunk_special_characters(self):
        """Test chunking with special characters."""
        text = "hello! @world #test $money %percent"
        result = simple_chunk(text, max_tokens=2)

        assert len(result) == 3
        assert "hello!" in result[0]
        assert "@world" in result[0]

    def test_simple_chunk_newlines_treated_as_spaces(self):
        """Test that newlines are treated as whitespace."""
        text = "word1\nword2\nword3\nword4"
        result = simple_chunk(text, max_tokens=2)

        # split() treats \n as whitespace
        assert len(result) == 2
        assert "word1" in result[0]
        assert "word4" in result[1]

    def test_simple_chunk_tabs_treated_as_spaces(self):
        """Test that tabs are treated as whitespace."""
        text = "word1\tword2\tword3\tword4"
        result = simple_chunk(text, max_tokens=2)

        assert len(result) == 2
        words_in_first = result[0].split()
        assert len(words_in_first) == 2

    def test_simple_chunk_returns_list(self):
        """Test that function returns a list."""
        result = simple_chunk("test")

        assert isinstance(result, list)
        assert len(result) == 1

    def test_simple_chunk_chunk_types(self):
        """Test that all chunks are strings."""
        text = "word1 word2 word3 word4"
        result = simple_chunk(text, max_tokens=2)

        for chunk in result:
            assert isinstance(chunk, str)

    def test_simple_chunk_large_max_tokens(self):
        """Test chunking with very large max_tokens."""
        text = "word1 word2 word3"
        result = simple_chunk(text, max_tokens=10000)

        # All text in one chunk
        assert len(result) == 1
        assert result[0] == text

    def test_simple_chunk_last_chunk_handling(self):
        """Test that incomplete final chunk is included."""
        text = "a b c d e"
        result = simple_chunk(text, max_tokens=2)

        # Should have 3 chunks: [a,b] [c,d] [e]
        assert len(result) == 3
        assert result[-1] == "e"

    def test_simple_chunk_many_small_words(self):
        """Test chunking many small words."""
        text = "a b c d e f g h i j"
        result = simple_chunk(text, max_tokens=3)

        assert len(result) == 4
        assert result[0] == "a b c"
        assert result[1] == "d e f"
        assert result[2] == "g h i"
        assert result[3] == "j"

    def test_simple_chunk_sentence_like_text(self):
        """Test chunking with sentence-like text."""
        text = "This is a test sentence. It has multiple words. And more content."
        result = simple_chunk(text, max_tokens=5)

        # Verify chunks contain expected segments
        full_text = " ".join(result)
        assert "test" in full_text
        assert "sentence" in full_text

    def test_simple_chunk_deterministic(self):
        """Test that chunking is deterministic (same input = same output)."""
        text = "word1 word2 word3 word4 word5"

        result1 = simple_chunk(text, max_tokens=2)
        result2 = simple_chunk(text, max_tokens=2)

        assert result1 == result2
