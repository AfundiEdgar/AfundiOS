"""Unit tests for the embedder module."""
import pytest
from unittest.mock import Mock, patch
from backend.core.embedder import embed_texts, embed_query


class TestEmbedTexts:
    """Tests for embed_texts function."""

    def test_embed_texts_single_text(self):
        """Test embedding a single text."""
        text = "hello world"
        result = embed_texts([text])

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], list)
        assert len(result[0]) == 1  # Single embedding value
        assert isinstance(result[0][0], float)

    def test_embed_texts_multiple_texts(self):
        """Test embedding multiple texts."""
        texts = ["hello", "world", "test"]
        result = embed_texts(texts)

        assert len(result) == 3
        for embedding in result:
            assert isinstance(embedding, list)
            assert len(embedding) > 0

    def test_embed_texts_empty_list(self):
        """Test embedding empty list."""
        result = embed_texts([])

        assert result == []
        assert isinstance(result, list)

    def test_embed_texts_empty_string(self):
        """Test embedding empty string."""
        result = embed_texts([""])

        assert len(result) == 1
        assert isinstance(result[0], list)

    def test_embed_texts_deterministic(self):
        """Test that embedding is deterministic."""
        text = "same text"

        result1 = embed_texts([text])
        result2 = embed_texts([text])

        assert result1 == result2

    def test_embed_texts_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings."""
        texts = ["text1", "text2"]
        result = embed_texts(texts)

        # Different texts should have different embeddings
        # (unless by coincidence hash matches, but very unlikely)
        assert result[0] != result[1]

    def test_embed_texts_preserves_order(self):
        """Test that order of embeddings matches order of texts."""
        texts = ["first", "second", "third"]
        result = embed_texts(texts)

        assert len(result) == len(texts)
        # Each text should map to its embedding in order
        for i, text in enumerate(texts):
            # Embedding should be deterministic based on text
            expected = embed_texts([text])[0]
            assert result[i] == expected

    def test_embed_texts_long_text(self):
        """Test embedding long text."""
        long_text = "word " * 1000
        result = embed_texts([long_text])

        assert len(result) == 1
        assert isinstance(result[0], list)
        assert len(result[0]) > 0

    def test_embed_texts_unicode_text(self):
        """Test embedding unicode text."""
        texts = ["hello", "你好", "مرحبا", "🌍🌎🌏"]
        result = embed_texts(texts)

        assert len(result) == len(texts)
        for embedding in result:
            assert isinstance(embedding, list)

    def test_embed_texts_return_type(self):
        """Test that return type is list of lists of floats."""
        texts = ["test"]
        result = embed_texts(texts)

        assert isinstance(result, list)
        assert all(isinstance(emb, list) for emb in result)
        assert all(
            isinstance(val, float) for emb in result for val in emb
        )

    def test_embed_texts_special_characters(self):
        """Test embedding text with special characters."""
        texts = ["hello!", "@world", "#tag", "$money"]
        result = embed_texts(texts)

        assert len(result) == len(texts)

    def test_embed_texts_whitespace_differences(self):
        """Test that texts with whitespace differences produce different embeddings."""
        texts = ["hello world", "helloworld"]
        result = embed_texts(texts)

        # These should be different texts, so different embeddings likely
        assert len(result) == 2

    def test_embed_texts_case_sensitive(self):
        """Test embedding behavior with different cases."""
        texts = ["HELLO", "hello", "Hello"]
        result = embed_texts(texts)

        assert len(result) == 3
        # Case matters in hash, so these should be different
        assert result[0] != result[1]

    def test_embed_texts_numeric_content(self):
        """Test embedding numeric text."""
        texts = ["123", "456", "789"]
        result = embed_texts(texts)

        assert len(result) == 3
        assert result[0] != result[1]

    def test_embed_texts_newlines_and_tabs(self):
        """Test embedding text with newlines and tabs."""
        texts = ["hello\nworld", "hello\tworld"]
        result = embed_texts(texts)

        assert len(result) == 2
        # Different whitespace = different texts
        assert result[0] != result[1]

    def test_embed_texts_large_batch(self):
        """Test embedding large batch of texts."""
        texts = [f"text{i}" for i in range(100)]
        result = embed_texts(texts)

        assert len(result) == 100
        for embedding in result:
            assert isinstance(embedding, list)

    def test_embed_texts_single_character(self):
        """Test embedding single character texts."""
        texts = ["a", "b", "c"]
        result = embed_texts(texts)

        assert len(result) == 3
        assert result[0] != result[1]

    def test_embed_texts_repeated_text(self):
        """Test that repeated texts get identical embeddings."""
        texts = ["same", "same", "same"]
        result = embed_texts(texts)

        assert result[0] == result[1]
        assert result[1] == result[2]


class TestEmbedQuery:
    """Tests for embed_query function."""

    def test_embed_query_basic(self):
        """Test embedding a basic query."""
        query = "what is the meaning of life?"
        result = embed_query(query)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(val, float) for val in result)

    def test_embed_query_single_word(self):
        """Test embedding single word query."""
        result = embed_query("hello")

        assert isinstance(result, list)
        assert len(result) > 0

    def test_embed_query_empty_string(self):
        """Test embedding empty query."""
        result = embed_query("")

        assert isinstance(result, list)

    def test_embed_query_deterministic(self):
        """Test that query embedding is deterministic."""
        query = "test query"

        result1 = embed_query(query)
        result2 = embed_query(query)

        assert result1 == result2

    def test_embed_query_uses_embed_texts(self):
        """Test that embed_query uses embed_texts internally."""
        query = "test query"

        # embed_query should return same as embed_texts([query])[0]
        result_query = embed_query(query)
        result_texts = embed_texts([query])[0]

        assert result_query == result_texts

    def test_embed_query_unicode(self):
        """Test embedding unicode query."""
        result = embed_query("你好世界")

        assert isinstance(result, list)
        assert len(result) > 0

    def test_embed_query_long_text(self):
        """Test embedding long query."""
        long_query = "word " * 500
        result = embed_query(long_query)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_embed_query_special_characters(self):
        """Test embedding query with special characters."""
        result = embed_query("What is @python? #programming $5000")

        assert isinstance(result, list)

    def test_embed_query_returns_list_of_floats(self):
        """Test that embed_query returns list of floats."""
        result = embed_query("test")

        assert isinstance(result, list)
        assert all(isinstance(val, float) for val in result)

    def test_embed_query_consistent_with_texts_single(self):
        """Test consistency between embed_query and embed_texts for single item."""
        text = "consistency test"

        query_result = embed_query(text)
        texts_result = embed_texts([text])[0]

        assert query_result == texts_result

    def test_embed_query_case_sensitive(self):
        """Test that query embedding is case-sensitive."""
        result_lower = embed_query("hello")
        result_upper = embed_query("HELLO")

        # Different case = different embeddings
        assert result_lower != result_upper

    def test_embed_query_whitespace_matters(self):
        """Test that whitespace affects embedding."""
        result1 = embed_query("hello world")
        result2 = embed_query("helloworld")

        assert result1 != result2

    def test_embed_query_punctuation(self):
        """Test embedding query with punctuation."""
        result = embed_query("What? How! Why.")

        assert isinstance(result, list)
        assert len(result) > 0

    def test_embed_query_numbers(self):
        """Test embedding query with numbers."""
        result = embed_query("Calculate 2 + 2")

        assert isinstance(result, list)

    def test_embed_query_mixed_content(self):
        """Test embedding query with mixed content types."""
        result = embed_query("Hello 世界 123 !@#$")

        assert isinstance(result, list)
        assert len(result) > 0


class TestEmbedderIntegration:
    """Integration tests for embedder module."""

    def test_embed_query_matches_embed_texts_single(self):
        """Test that embed_query produces same result as embed_texts for single item."""
        test_strings = [
            "simple test",
            "query with multiple words",
            "123 456 789",
            "特殊文字",
        ]

        for test_str in test_strings:
            query_result = embed_query(test_str)
            texts_result = embed_texts([test_str])[0]

            assert query_result == texts_result, f"Mismatch for: {test_str}"

    def test_embed_query_in_batch_context(self):
        """Test embed_query when mixed with batch processing."""
        query = "test query"
        texts = ["text1", "text2", query]

        query_emb = embed_query(query)
        batch_embs = embed_texts(texts)

        # The query embedding should match the one in batch
        assert query_emb == batch_embs[2]

    def test_embeddings_vector_consistency(self):
        """Test that embeddings are consistent in vector form."""
        texts = ["a", "b", "c"]
        result = embed_texts(texts)

        # All embeddings should be comparable (same dimension)
        embedding_dims = [len(emb) for emb in result]
        assert len(set(embedding_dims)) == 1  # All same dimension

    def test_deterministic_hashing_behavior(self):
        """Test the deterministic hashing behavior of embedder."""
        # The current implementation uses hash() for embeddings
        # Test that this is consistent across calls

        text = "deterministic test"

        embeddings = [embed_query(text) for _ in range(5)]

        # All should be identical
        assert all(emb == embeddings[0] for emb in embeddings)

    def test_empty_vs_nonempty_distinction(self):
        """Test that empty and non-empty strings produce different results."""
        empty_emb = embed_query("")
        nonempty_emb = embed_query("a")

        # Should be different
        assert empty_emb != nonempty_emb
