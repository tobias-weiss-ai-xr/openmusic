"""Tests for quotes module."""
import pytest

from openmusic.shorts.quotes import QUOTES, get_random_quote, get_quotes_by_author, StoicQuote


class TestQuotes:
    def test_quotes_is_list_of_stoic_quotes(self):
        assert len(QUOTES) > 0
        for q in QUOTES:
            assert isinstance(q, StoicQuote)
            assert isinstance(q.text, str) and len(q.text) > 0
            assert isinstance(q.author, str) and len(q.author) > 0

    def test_get_random_quote(self):
        q = get_random_quote()
        assert q in QUOTES

    def test_get_random_quote_with_seed(self):
        q1 = get_random_quote(seed=42)
        q2 = get_random_quote(seed=42)
        assert q1 == q2
        assert q1.text == q2.text

    def test_get_quotes_by_author(self):
        marcus = get_quotes_by_author("Marcus Aurelius")
        assert len(marcus) > 0
        assert all(q.author == "Marcus Aurelius" for q in marcus)
        marcus_lower = get_quotes_by_author("marcus aurelius")
        assert len(marcus_lower) == len(marcus)

    def test_get_quotes_by_author_unknown(self):
        assert get_quotes_by_author("Unknown Person") == []

    def test_quote_text_has_no_curly_braces(self):
        for q in QUOTES:
            assert "{" not in q.text, f"Quote contains '{{': {q.text[:50]}..."
            assert "}" not in q.text, f"Quote contains '}}': {q.text[:50]}..."
