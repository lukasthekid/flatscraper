"""Tests for groq_client module."""

import pytest

from groq_client import _extract_message_only, _parse_retry_after


class TestExtractMessageOnly:
    """Tests for _extract_message_only - strips LLM meta-commentary."""

    def test_plain_message_unchanged(self):
        msg = "Hallo Marco,\n\nich bin Max aus Berlin und interessiere mich für das Zimmer."
        assert _extract_message_only(msg) == msg

    def test_strips_meta_before_dash_separator(self):
        raw = """**Kurzfassung meiner Überlegungen**
Ich habe die Anrede-Regel beachtet und den Namen verwendet.

---

Hallo Bardia,

dein Hinweis hat mich begeistert. Ich bin Lukas, 26, Software Engineer."""
        result = _extract_message_only(raw)
        assert "Kurzfassung" not in result
        assert "Überlegungen" not in result
        assert result.strip().startswith("Hallo Bardia,")

    def test_strips_meta_without_separator(self):
        raw = """**Kurzfassung meiner Überlegungen**
Ich habe die Anrede-Regel beachtet.

Hallo Lisa,

ich freue mich auf deine Antwort."""
        result = _extract_message_only(raw)
        assert "Kurzfassung" not in result
        assert result.strip().startswith("Hallo Lisa,")

    def test_hi_greeting(self):
        raw = """Gedanken: Icebreaker einbauen.

Hi Sarah,

das Zimmer klingt super."""
        result = _extract_message_only(raw)
        assert "Gedanken" not in result
        assert result.strip().startswith("Hi Sarah,")

    def test_sehr_geehrte_greeting(self):
        raw = """Kurzfassung: Anrede-Regel befolgt.

Sehr geehrte Damen und Herren,

hiermit bewerbe ich mich."""
        result = _extract_message_only(raw)
        assert "Kurzfassung" not in result
        assert "Sehr geehrte" in result

    def test_fallback_when_extraction_too_short(self):
        raw = "Hallo"  # Very short, no real message
        result = _extract_message_only(raw)
        assert result == "Hallo"

    def test_fallback_keeps_original_if_extraction_fails(self):
        raw = "Some weird output without greeting that is longer than 50 chars"
        result = _extract_message_only(raw)
        assert result == raw


class TestParseRetryAfter:
    """Tests for _parse_retry_after - extracts wait time from rate limit errors."""

    def test_parses_seconds(self):
        err = "Rate limit. Please try again in 4.1175s"
        assert _parse_retry_after(Exception(err)) == 4.1175

    def test_parses_integer_seconds(self):
        err = "try again in 10s"
        assert _parse_retry_after(Exception(err)) == 10.0

    def test_returns_none_when_no_match(self):
        err = "Some other error"
        assert _parse_retry_after(Exception(err)) is None

    def test_case_insensitive(self):
        err = "Please Try Again In 5.5S"
        assert _parse_retry_after(Exception(err)) == 5.5
