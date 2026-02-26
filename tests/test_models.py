"""Tests for Pydantic models."""

from models import Listing, ListingData, Persona, UserProfile


class TestListing:
    def test_valid_listing(self):
        data = {
            "ad_id": "12345",
            "title": "Schönes WG-Zimmer",
            "url": "https://wg-gesucht.de/12345.html",
            "price": "650 €",
            "size": "15 m²",
            "age_minutes": 30,
            "raw_age_text": "Online: 30 Minuten",
        }
        listing = Listing.model_validate(data)
        assert listing.ad_id == "12345"
        assert listing.title == "Schönes WG-Zimmer"
        assert listing.age_minutes == 30

    def test_age_minutes_none(self):
        data = {
            "ad_id": "1",
            "title": "x",
            "url": "https://x.de/1.html",
            "price": "0",
            "size": "0",
            "age_minutes": None,
            "raw_age_text": "unbekannt",
        }
        listing = Listing.model_validate(data)
        assert listing.age_minutes is None


class TestListingData:
    def test_minimal_valid(self):
        data = {
            "title": "WG-Zimmer",
            "address": "Musterstr. 1",
            "full_description": "Beschreibung",
        }
        ld = ListingData.model_validate(data)
        assert ld.title == "WG-Zimmer"
        assert ld.publisher_name == ""
        assert ld.google_drive == ""
        assert ld.ad_type == "wg"

    def test_full_data(self):
        data = {
            "title": "Wohnung",
            "address": "Teststr. 5",
            "publisher_name": "Max",
            "full_description": "Text",
            "google_drive": "https://drive.google.com/...",
            "ad_type": "wohnung",
        }
        ld = ListingData.model_validate(data)
        assert ld.ad_type == "wohnung"


class TestPersona:
    def test_defaults(self):
        p = Persona()
        assert p.first_name == "Nutzer"
        assert p.move_in == "So schnell wie möglich"
        assert p.documents == "Alle Unterlagen im Google Drive Link"


class TestUserProfile:
    def test_valid_profile(self):
        data = {
            "persona_block": "DEINE PERSONA:\n- Alter: 28",
            "persona": {"first_name": "Max", "age": "28"},
            "persona_name": "Max",
            "search_urls": ["https://wg-gesucht.de/..."],
        }
        profile = UserProfile.model_validate(data)
        assert profile.persona_name == "Max"
        assert len(profile.search_urls) == 1

    def test_search_urls_default(self):
        data = {
            "persona_block": "x",
            "persona": {},
            "persona_name": "x",
        }
        profile = UserProfile.model_validate(data)
        assert profile.search_urls == []
