"""Tests for config module."""

import json
from pathlib import Path

import pytest


def test_get_persona_default_when_no_profile(monkeypatch, tmp_path):
    """When no user_profile.json exists, get_persona_block returns default."""
    import config as config_mod

    monkeypatch.setattr(config_mod, "PROFILE_PATH", tmp_path / "nonexistent.json")
    monkeypatch.setattr(config_mod, "_user_profile", None)

    # Force reload by clearing cache
    config_mod._user_profile = None

    block = config_mod.get_persona_block()
    assert "DEINE PERSONA" in block
    assert "Software Engineer" in block


def test_get_persona_from_profile(monkeypatch, tmp_path):
    """When user_profile.json exists, get_persona_block returns profile content."""
    import config as config_mod

    profile_path = tmp_path / "user_profile.json"
    profile_path.write_text(
        json.dumps({
            "persona_block": "DEINE PERSONA:\n- Alter: 99\n- Beruf: Tester",
            "persona": {"first_name": "Test"},
            "persona_name": "TestUser",
            "search_urls": [],
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(config_mod, "PROFILE_PATH", profile_path)
    monkeypatch.setattr(config_mod, "_user_profile", None)

    block = config_mod.get_persona_block()
    assert "99" in block
    assert "Tester" in block


def test_get_persona_name_default(monkeypatch, tmp_path):
    """When no profile, get_persona_name returns 'Nutzer'."""
    import config as config_mod

    monkeypatch.setattr(config_mod, "PROFILE_PATH", tmp_path / "nonexistent.json")
    monkeypatch.setattr(config_mod, "_user_profile", None)

    name = config_mod.get_persona_name()
    assert name == "Nutzer"


def test_get_persona_name_from_profile(monkeypatch, tmp_path):
    """When profile exists, get_persona_name returns persona_name."""
    import config as config_mod

    profile_path = tmp_path / "user_profile.json"
    profile_path.write_text(
        json.dumps({
            "persona_block": "x",
            "persona": {},
            "persona_name": "Anna",
            "search_urls": [],
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(config_mod, "PROFILE_PATH", profile_path)
    monkeypatch.setattr(config_mod, "_user_profile", None)

    name = config_mod.get_persona_name()
    assert name == "Anna"


def test_get_search_urls_from_profile(monkeypatch, tmp_path):
    """When profile has search_urls, they are returned."""
    import config as config_mod

    urls = ["https://wg-gesucht.de/berlin"]
    profile_path = tmp_path / "user_profile.json"
    profile_path.write_text(
        json.dumps({
            "persona_block": "x",
            "persona": {},
            "persona_name": "x",
            "search_urls": urls,
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(config_mod, "PROFILE_PATH", profile_path)
    monkeypatch.setattr(config_mod, "_user_profile", None)

    result = config_mod.get_search_urls()
    assert result == urls


def test_get_search_urls_empty_when_no_profile(monkeypatch, tmp_path):
    """When no profile, get_search_urls returns [] (used by search module with fallback)."""
    import config as config_mod

    monkeypatch.setattr(config_mod, "PROFILE_PATH", tmp_path / "nonexistent.json")
    monkeypatch.setattr(config_mod, "_user_profile", None)

    result = config_mod.get_search_urls()
    assert result == []
