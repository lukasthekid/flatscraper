# FlatScraper

Flat search automation for WG-Gesucht. Automatically finds new listings, generates personalized messages with AI, and sends contact requests.

## Supported platforms

| Platform    | Status |
|------------|--------|
| WG-Gesucht | Ready  |

## Setup

```powershell
# Create virtual environment and install (uv recommended)
uv sync

# Or with pip
pip install -e .

# Interaktiver Setup-Assistent (empfohlen)
uv run setup
# oder: uv run flatscraper setup

# Install Playwright browser
playwright install chromium
```

### Setup-Assistent

Der Setup-Assistent (`uv run setup` oder `flatscraper setup`) führt dich durch die Einrichtung:

1. **Anmeldedaten** – WG-Gesucht E-Mail/Passwort, Groq API-Schlüssel
2. **Google Drive** – Link zu deinen Bewerbungsunterlagen
3. **Dein Profil** – Alter, Stadt, Beruf, Persönlichkeit, Hobbys (für personalisierte Anschreiben)
4. **KI-Optimierung** – Optional: Die KI formuliert dein Profil für bessere Nachrichten
5. **Modell** – Groq-Modell wählen
6. **Such-URLs** – WG-Gesucht Such-URLs hinzufügen

Die Konfiguration wird in `.env` und `user_profile.json` gespeichert.

### Manuelle Konfiguration

Alternativ: `.env.example` nach `.env` kopieren und Werte eintragen:

| Variable | Required | Description |
|----------|----------|-------------|
| `FLATSCRAPER_EMAIL` | Yes | WG-Gesucht login email |
| `FLATSCRAPER_PASSWORD` | Yes | WG-Gesucht login password |
| `GROQ_API_KEY` | Yes | Groq API key from [console.groq.com](https://console.groq.com) |
| `GOOGLE_DRIVE_LINK` | Yes | Google Drive folder with your documents |
| `GROQ_MODEL` | No | LLM model (default: `llama-3.1-8b-instant`) |
| `RUN_INTERVAL_MINUTES` | No | Schedule interval (default: `30`) |
| `AUTO_RUN_ENABLED` | No | Enable auto-schedule (default: `false`) |

**Never commit `.env` or `user_profile.json`** — they contain personal data. Both are in `.gitignore`.

## Usage

```powershell
# FlatScraper starten (einmal durchlaufen)
uv run flatscraper

# Optionen
flatscraper --no-send    # Nachrichten generieren, aber nicht senden
flatscraper --visible    # Browser sichtbar (Standard: unsichtbar/headless)
flatscraper --debug      # Alle Anzeigen (ohne Altersfilter)
flatscraper --schedule   # In Intervallen (für später)
flatscraper setup        # Setup-Assistent
```

### Tests

```powershell
uv sync --extra dev
uv run pytest tests/ -v
```

### Standalone login test

```powershell
python login.py
```

## Project structure

```
flatscraper/
├── models.py          # Pydantic models (type-safe)
├── config.py          # Pydantic Settings + user_profile
├── setup_wizard.py    # Interaktiver Setup-Assistent
├── groq_client.py    # LLM client for Anschreiben generation
├── run.py             # Main entry point
├── login.py           # Standalone login test
├── .env.example       # Template for environment variables
└── platforms/
    ├── base.py       # Abstract base for platforms (Platform ABC)
    ├── __init__.py   # Platform registry (PLATFORMS dict)
    └── wggesucht/    # WG-Gesucht.de
        ├── config.py
        ├── platform.py
        ├── search.py
        ├── extractor.py
        ├── login.py
        └── messenger.py
```

## Configuration

- **Setup-Assistent**: `flatscraper setup` – interaktive Einrichtung
- **Secrets**: `.env` (E-Mail, Passwort, API-Schlüssel)
- **Profil**: `user_profile.json` (Persona, Such-URLs) – wird vom Setup erstellt
- **LLM-Prompts**: Persona aus Profil, Rest in `config.py`

## Pushing to GitHub

1. Create a new repository on [GitHub](https://github.com/new). Do not initialize with a README.
2. Ensure `.env` is in `.gitignore` (it is). Never commit secrets.
3. Add the remote and push:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/flatscraper.git
git branch -M main
git push -u origin main
```

4. After pushing, add your `.env` file locally (it stays on your machine only).

## Adding new platforms

To add support for another flat search website:

1. Create `platforms/<name>/` with config, login, search, extractor, messenger as needed.
2. Implement the `Platform` ABC from `platforms/base.py` in `platforms/<name>/platform.py`:
   - `name` (property)
   - `login(page)`
   - `run_search(page, include_all)` → `list[Listing]`
   - `extract_details(page, url)` → `ListingDetails | None`
   - `send_message(page, listing_url, message_text)` → `bool`
3. Register in `platforms/__init__.py`: `PLATFORMS["<name>"] = NewPlatform()`

The main run loop in `run.py` is generic—valid platforms are read from the registry, so no further changes are needed.
