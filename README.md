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

# Copy environment template and fill in your values
copy .env.example .env

# Install Playwright browser
playwright install chromium
```

### Environment variables

Copy `.env.example` to `.env` and set your values:

| Variable | Required | Description |
|----------|----------|-------------|
| `FLATSCRAPER_EMAIL` | Yes | WG-Gesucht login email |
| `FLATSCRAPER_PASSWORD` | Yes | WG-Gesucht login password |
| `GROQ_API_KEY` | Yes | Groq API key from [console.groq.com](https://console.groq.com) |
| `GOOGLE_DRIVE_LINK` | Yes | Google Drive folder with your documents |
| `GROQ_MODEL` | No | LLM model (default: `llama-3.1-8b-instant`) |
| `RUN_INTERVAL_MINUTES` | No | Schedule interval (default: `30`) |
| `AUTO_RUN_ENABLED` | No | Enable auto-schedule (default: `false`) |

**Never commit `.env`** — it contains secrets. `.env` is in `.gitignore`.

## Usage

```powershell
# Run WG-Gesucht (the main command)
uv run run wggesucht
# or: run wggesucht

# Or with Python
python run.py wggesucht
python run.py --platform wggesucht

# Options
run wggesucht --once                 # Single run (no schedule)
run wggesucht --schedule             # Run every N minutes
run wggesucht --no-send              # Generate messages but don't send
run wggesucht --debug                # Include all listings (ignore age filter)
```

### Standalone login test

```powershell
python login.py
```

## Project structure

```
flatscraper/
├── config.py          # Loads config from environment
├── groq_client.py    # LLM client for Anschreiben generation
├── run.py            # Main entry point
├── login.py          # Standalone login test
├── .env.example      # Template for environment variables
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

Secrets and API keys are loaded from environment variables (see `.env.example`).  
LLM prompts can be customized in `config.py`.  
Platform-specific settings: `platforms/wggesucht/config.py`.

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
