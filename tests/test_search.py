"""Tests for WG-Gesucht search parsing utilities."""

import pytest

from platforms.wggesucht.search import _extract_ad_id_from_url, _parse_online_age


class TestParseOnlineAge:
    """Tests for _parse_online_age - parses 'Online: X Minuten' etc."""

    def test_minutes(self):
        assert _parse_online_age("Online: 30 Minuten") == (30, "Online: 30 Minuten")
        assert _parse_online_age("Online: 15 Minuten") == (15, "Online: 15 Minuten")

    def test_one_hour(self):
        assert _parse_online_age("Online: 1 Stunde") == (60, "Online: 1 Stunde")

    def test_multiple_hours(self):
        assert _parse_online_age("Online: 3 Stunden") == (180, "Online: 3 Stunden")

    def test_gerade_eben(self):
        assert _parse_online_age("gerade eben online") == (0, "gerade eben online")

    def test_seconds(self):
        assert _parse_online_age("Online: 45 Sekunden") == (0, "Online: 45 Sekunden")

    def test_no_match(self):
        mins, raw = _parse_online_age("Vor 2 Tagen")
        assert mins is None
        assert raw == "Vor 2 Tagen"


class TestExtractAdIdFromUrl:
    """Tests for _extract_ad_id_from_url."""

    def test_html_endpoint(self):
        # Format: /ID.html (e.g. from listing links)
        url = "https://wg-gesucht.de/wg-zimmer/8125289.html"
        assert _extract_ad_id_from_url(url) == "8125289"

    def test_asset_id_param(self):
        url = "https://example.com/?asset_id=12314053"
        assert _extract_ad_id_from_url(url) == "12314053"

    def test_no_match(self):
        assert _extract_ad_id_from_url("https://example.com/") == ""
