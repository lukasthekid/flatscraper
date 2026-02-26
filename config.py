"""Shared configuration for FlatScraper. Type-safe loading from env and user_profile.json."""

import json
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from models import UserProfile

PROJECT_ROOT = Path(__file__).parent
PROFILE_PATH = PROJECT_ROOT / "user_profile.json"

# Default persona block when no profile exists (placeholder – run "flatscraper setup" to configure)
_DEFAULT_PERSONA_BLOCK = """DEINE PERSONA:
- Alter: 28 Jahre
- Herkunft: Berlin (zieht in Zielstadt)
- Beruf: Software Engineer
- Einzugstermin: Flexibel, gerne ab nächstem Monat
- Persönlichkeit: Ruhig, ordentlich, gesellig
- Hobbys: Lesen, Sport, Kochen
- Dokumente: Alle Unterlagen im Google Drive Link (bitte in .env konfigurieren)"""


class AppSettings(BaseSettings):
    """Environment-based settings (from .env or os.environ)."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    email: str = Field(default="", validation_alias="FLATSCRAPER_EMAIL")
    password: str = Field(default="", validation_alias="FLATSCRAPER_PASSWORD")
    groq_api_key: str = Field(default="", validation_alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-8b-instant", validation_alias="GROQ_MODEL")
    google_drive_link: str = Field(default="", validation_alias="GOOGLE_DRIVE_LINK")
    run_interval_minutes: int = Field(default=30, validation_alias="RUN_INTERVAL_MINUTES")
    auto_run_enabled: bool = Field(
        default=False,
        validation_alias="AUTO_RUN_ENABLED",
    )


_user_profile: UserProfile | None = None


def _load_user_profile() -> UserProfile | None:
    global _user_profile
    if _user_profile is not None:
        return _user_profile
    if PROFILE_PATH.exists():
        try:
            data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            _user_profile = UserProfile.model_validate(data)
            return _user_profile
        except Exception:
            pass
    return None


# --- Public API ---

def get_settings() -> AppSettings:
    return AppSettings()


def get_search_urls() -> list[str]:
    profile = _load_user_profile()
    if profile and profile.search_urls:
        return profile.search_urls
    return []


def get_persona_name() -> str:
    profile = _load_user_profile()
    if profile and profile.persona_name:
        return profile.persona_name
    return "Nutzer"


def get_persona_block() -> str:
    profile = _load_user_profile()
    if profile and profile.persona_block:
        return profile.persona_block
    return _DEFAULT_PERSONA_BLOCK


# Backward-compatible module-level exports (loaded at import)
_settings_instance = AppSettings()

EMAIL = _settings_instance.email
PASSWORD = _settings_instance.password
GROQ_API_KEY = _settings_instance.groq_api_key
GROQ_MODEL = _settings_instance.groq_model
GOOGLE_DRIVE_LINK = _settings_instance.google_drive_link
RUN_INTERVAL_MINUTES = _settings_instance.run_interval_minutes
AUTO_RUN_ENABLED = _settings_instance.auto_run_enabled

# Parse AUTO_RUN_ENABLED - pydantic-settings should handle "true"/"false" for bool
# Let me check - by default BaseSettings will coerce "false" to False. Good.

# LLM prompts - built from profile
_persona_block = get_persona_block()
_persona_name = get_persona_name()

LLM_SYSTEM_PROMPT = f"""Du bist ein charmanter, professioneller Assistent, der dabei hilft, ein WG-Zimmer ODER eine Wohnung zu finden. Deine Aufgabe ist es, basierend auf einer Wohnungsanzeige ein kurzes, sympathisches und persönliches Anschreiben auf Deutsch zu verfassen. Das Anschreiben passt sich dem Anzeigentyp an (WG-Zimmer vs. Wohnung).

{_persona_block}"""

# ---------------------------------------------------------------------------
# AD-TYPE INSTRUCTIONS
# ---------------------------------------------------------------------------

LLM_AD_TYPE_INSTRUCTIONS_WG = """\
ANZEIGENTYP: WG-Zimmer
- Ton: locker, herzlich, "passen wir zusammen?"-Gefühl.
- Fokus: gemeinsames WG-Leben, Interessen der Mitbewohner, Atmosphäre.
- Anrede: "Hallo [Name]," oder "Hi [Name]," – nie formell."""

LLM_AD_TYPE_INSTRUCTIONS_WOHNUNG = """\
ANZEIGENTYP: Wohnung (privat oder professionell)
- Ton: freundlich-professionell, seriös, verbindlich.
- Fokus: stabiles Einkommen, Zuverlässigkeit, Einzugstermin, vollständige Unterlagen.
- Anrede: "Hallo [Name]," oder "Sehr geehrte/r [Name]," – je nach Tonalität der Anzeige."""

# ---------------------------------------------------------------------------
# MESSAGE PROMPT
# ---------------------------------------------------------------------------

LLM_MESSAGE_PROMPT_TEMPLATE = """\
ANZEIGENDATEN (Typ: {ad_type_label}):

Titel:        {title}
Adresse:      {address}
Anbieter:     {publisher_name}
Beschreibung:
\"\"\"
{description}
\"\"\"

ANZEIGENTYP-ANWEISUNGEN:
{ad_type_instructions}

ANREDE-REGELN (Priorität 1 → 3):
1. Name unter "Anbieter" vorhanden → nutze ihn: "Hallo Marco," / "Hi Lisa,"
2. Namen im Beschreibungstext ("Wir sind Jonas und Lisa") → nutze den ersten Namen.
3. Kein Name bekannt → WG: "Hallo liebe WG," | Wohnung: "Hallo,"

AUFGABE:
Schreibe das Anschreiben für {persona_name} nach dieser Struktur:

1. Persönliche Anrede (siehe Anrede-Regeln – niemals generisch wenn ein Name bekannt ist).
2. Kurzer Icebreaker: ein konkretes Detail aus der Anzeige aufgreifen.
3. Kurzvorstellung: Beruf, Herkunft, Einzugstermin.
4. Call to Action: Verweis auf den Google Drive Link ({google_drive_link}) für alle Unterlagen + Freude auf Besichtigung.

STIL: persönlich, lebendig, kurz – kein Werbejargon, kein Fülltext.
LÄNGE: unter 150 Wörter.
FORMAT: Fließtext, kein Markdown, keine Signatur, kein Betreff.

WICHTIG: Antworte AUSSCHLIESSLICH mit dem fertigen Nachrichtentext. Keine Erklärungen, keine Gedanken, keine Meta-Kommentare (z.B. "Kurzfassung meiner Überlegungen"), keine Anleitung – nur die Nachricht selbst.\
"""