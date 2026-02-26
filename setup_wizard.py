#!/usr/bin/env python3
"""
FlatScraper Setup-Assistent – interaktive Einrichtung.
Sammelt Anmeldedaten, Persona und Such-URLs. Optional: KI optimiert die Persona.
"""

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))

import questionary
from rich.console import Console
from rich.panel import Panel

from models import EnvData, Persona, UserProfile

console = Console()

PROJECT_ROOT = Path(__file__).parent
ENV_PATH = PROJECT_ROOT / ".env"
PROFILE_PATH = PROJECT_ROOT / "user_profile.json"

GOOGLE_DRIVE_EXPLANATION = """
Lade deine Bewerbungsunterlagen (Vertrag, Gehaltsnachweis, Ausweis, Steckbrief)
in einen Google Drive Ordner hoch. Teile den Ordner mit "Jeder mit dem Link kann ansehen"
und füge den Link hier ein. Vermieter können so deine Unterlagen prüfen.
""".strip()

PERSONA_REFINEMENT_PROMPT = """Basierend auf den folgenden Angaben des Nutzers, formuliere eine prägnante, professionelle Persona-Beschreibung für ein System-Prompt. 
Die Persona wird verwendet, um personalisierte WG-Anschreiben zu generieren.
Halte die Beschreibung auf Deutsch, in Stichpunkten, maximal 15 Zeilen.
Antworte NUR mit der Persona-Beschreibung, ohne Einleitung oder Erklärung.

Nutzerangaben:
{persona_raw}
"""


def _build_persona_block(persona: Persona) -> str:
    """Erstellt Persona-Block aus strukturierten Angaben."""
    lines = [
        f"- Alter: {persona.age} Jahre",
        f"- Herkunft: {persona.from_city} (zieht nach {persona.target_city})",
        f"- Beruf: {persona.job}",
        f"- Einzugstermin: {persona.move_in}",
        f"- Persönlichkeit: {persona.personality}",
        f"- Hobbys: {persona.hobbies}",
        f"- Dokumente: {persona.documents}",
    ]
    return "DEINE PERSONA:\n" + "\n".join(lines)


def _refine_persona_with_llm(persona_raw: str, api_key: str, model: str) -> str | None:
    """Ruft Groq auf, um die Persona zu optimieren."""
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        prompt = PERSONA_REFINEMENT_PROMPT.format(persona_raw=persona_raw)
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_completion_tokens=500,
        )
        content = completion.choices[0].message.content
        if content:
            return "DEINE PERSONA:\n" + content.strip()
    except Exception as e:
        console.print(f"[yellow]KI-Optimierung fehlgeschlagen: {e}[/yellow]")
    return None


def _write_env(data: EnvData) -> None:
    """Schreibt .env Datei."""
    lines = [
        f"FLATSCRAPER_EMAIL={data.email}",
        f"FLATSCRAPER_PASSWORD={data.password}",
        f"GROQ_API_KEY={data.groq_api_key}",
        f"GOOGLE_DRIVE_LINK={data.google_drive_link}",
        f"GROQ_MODEL={data.groq_model}",
        "RUN_INTERVAL_MINUTES=30",
        "AUTO_RUN_ENABLED=false",
    ]
    ENV_PATH.write_text("\n".join(lines), encoding="utf-8")


def _write_profile(profile: UserProfile) -> None:
    """Schreibt user_profile.json."""
    data = profile.model_dump(mode="json")
    PROFILE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def run_setup() -> None:
    """Führt den Setup-Assistenten aus."""
    console.print(Panel.fit(
        "[bold]FlatScraper Setup-Assistent[/bold]\n\n"
        "Willkommen! Wir richten dein Profil ein.",
        border_style="green",
    ))
    console.print()

    # 1. Anmeldedaten
    console.print("[bold]Schritt 1: Anmeldedaten[/bold]\n")
    email = questionary.text(
        "WG-Gesucht E-Mail:",
        default="",
        validate=lambda x: True if x.strip() else "Bitte E-Mail eingeben.",
    ).ask()
    if email is None:
        console.print("[red]Abgebrochen.[/red]")
        return
    email = email.strip()

    password = questionary.password("WG-Gesucht Passwort:").ask()
    if password is None:
        console.print("[red]Abgebrochen.[/red]")
        return

    groq_key = questionary.password(
        "Groq API-Schlüssel (https://console.groq.com):"
    ).ask()
    if groq_key is None:
        console.print("[red]Abgebrochen.[/red]")
        return

    # 2. Google Drive
    console.print("\n[bold]Schritt 2: Google Drive[/bold]\n")
    console.print(GOOGLE_DRIVE_EXPLANATION)
    console.print()
    google_drive = questionary.text(
        "Google Drive Ordner-Link (mit deinen Unterlagen):",
        default="",
    ).ask()
    if google_drive is None:
        console.print("[red]Abgebrochen.[/red]")
        return
    google_drive = google_drive.strip()

    # 3. Persona
    console.print("\n[bold]Schritt 3: Dein Profil für Anschreiben[/bold]\n")
    console.print("Diese Angaben helfen der KI, persönliche Nachrichten zu schreiben.\n")

    first_name = questionary.text("Dein Vorname (für Anschreiben):", default="").ask()
    if first_name is None:
        return
    first_name = first_name.strip() or "Nutzer"

    age = questionary.text("Dein Alter:", default="26").ask()
    if age is None:
        return
    age = age.strip() or "26"

    from_city = questionary.text(
        "Woher kommst du? (z.B. Wien, Berlin):",
        default="",
    ).ask()
    if from_city is None:
        return
    from_city = from_city.strip()

    target_city = questionary.text(
        "Wohin ziehst du? (z.B. München):",
        default="",
    ).ask()
    if target_city is None:
        return
    target_city = target_city.strip()

    looking_for = questionary.select(
        "Was suchst du?",
        choices=["WG-Zimmer", "Wohnung", "Beides"],
    ).ask()
    if looking_for is None:
        return

    job = questionary.text(
        "Beruf / Tätigkeit (z.B. AI Engineer bei BCG):",
        default="",
    ).ask()
    if job is None:
        return
    job = job.strip()

    move_in = questionary.text(
        "Einzugstermin (z.B. So schnell wie möglich, Anfang März):",
        default="So schnell wie möglich",
    ).ask()
    if move_in is None:
        return
    move_in = move_in.strip() or "So schnell wie möglich"

    personality = questionary.text(
        "Kurze Beschreibung deiner Persönlichkeit (z.B. ordentlich, kommunikativ, Wiener Schmäh):",
        default="",
    ).ask()
    if personality is None:
        return
    personality = personality.strip()

    hobbies = questionary.text(
        "Hobbys (z.B. Fitness, Boxen, Wintersport, gutes Essen):",
        default="",
    ).ask()
    if hobbies is None:
        return
    hobbies = hobbies.strip()

    documents = questionary.text(
        "Status deiner Unterlagen (z.B. Alle in Google Drive, Schufa beantragt):",
        default="Alle Unterlagen im Google Drive Link",
    ).ask()
    if documents is None:
        return
    documents = documents.strip() or "Alle Unterlagen im Google Drive Link"

    persona = Persona(
        first_name=first_name,
        age=age,
        from_city=from_city,
        target_city=target_city,
        looking_for=looking_for,
        job=job,
        move_in=move_in,
        personality=personality,
        hobbies=hobbies,
        documents=documents,
    )

    persona_raw = "\n".join(f"- {k}: {v}" for k, v in persona.model_dump().items() if v)
    persona_block = _build_persona_block(persona)

    # 4. Optional: KI-Optimierung
    console.print("\n[bold]Schritt 4: Persona optimieren[/bold]\n")
    refine = questionary.confirm(
        "Soll die KI dein Profil für bessere Anschreiben optimieren? (nutzt Groq API)",
        default=True,
    ).ask()
    if refine is None:
        return
    if refine and groq_key:
        console.print("[dim]Optimiere Persona...[/dim]")
        refined = _refine_persona_with_llm(persona_raw, groq_key, "llama-3.1-8b-instant")
        if refined:
            persona_block = refined
            console.print("[green]Persona optimiert.[/green]")

    # 5. Modell
    console.print("\n[bold]Schritt 5: KI-Modell[/bold]\n")
    groq_model = questionary.select(
        "Welches Groq-Modell soll verwendet werden?",
        choices=[
            "groq/compound",           # 70K TPM – höchster Durchsatz, viele Nachrichten/min
            "groq/compound-mini",      # 70K TPM – schnell, gut für hohe Frequenz
            "llama-3.3-70b-versatile", # 12K TPM – beste Textqualität (70B)
            "meta-llama/llama-4-scout-17b-16e-instruct",  # 30K TPM – guter Kompromiss
        ],
        default="groq/compound",
    ).ask()
    if groq_model is None:
        return

    # 6. Such-URLs
    console.print("\n[bold]Schritt 6: Such-URLs[/bold]\n")
    console.print(
        "Die Such-URL muss eine [bold]WG-Gesucht-Such-URL[/bold] sein.\n"
        "Öffne wg-gesucht.de, stelle deine Filter ein (Stadt, Miete, Größe, etc.) und "
        "kopiere die URL aus der Adresszeile.\n"
    )
    console.print("[bold]Wichtig:[/bold]")
    console.print("  • Sortiere nach [bold]Aktualität[/bold] (neueste zuerst), damit der Scraper alle 10 Min. die neuesten Anzeigen findet.")
    console.print("  • Bereits kontaktierte Anzeigen werden automatisch übersprungen.")
    console.print()
    console.print("[bold]Beispiel-URL[/bold] (WG-Zimmer München, sortiert nach Aktualität):")
    example_url = "https://www.wg-gesucht.de/wg-zimmer-in-Muenchen.90.0.1.0.html?csrf_token=80a8431a6e7f318413cb50cc0a34f66d93f3091c&offer_filter=1&city_id=90&sort_order=0&noDeact=1&categories%5B%5D=0&sMin=20&rMax=1200&ot%5B%5D=2118&radDis=3000&wgMxT=2"
    console.print(f"  [link={example_url}]{example_url}[/link]")
    console.print()

    search_urls: list[str] = []
    default_urls = [
        example_url,
        "https://www.wg-gesucht.de/1-zimmer-wohnungen-und-wohnungen-in-Muenchen.90.1+2.1.0.html",
    ]
    add_more = True
    first = True
    while add_more:
        if first:
            url = questionary.text(
                "Erste Such-URL (WG-Gesucht-Suche, sortiert nach Aktualität):",
                default=default_urls[0] if default_urls else "",
            ).ask()
            first = False
        else:
            url = questionary.text("Weitere URL (oder Enter zum Beenden):").ask()
        if url is None:
            break
        url = url.strip()
        if url and url not in search_urls:
            search_urls.append(url)
            console.print(f"[green]Hinzugefügt ({len(search_urls)} URLs)[/green]")
        if not url or not questionary.confirm("Noch eine URL hinzufügen?", default=False).ask():
            add_more = False

    if not search_urls and default_urls:
        use_defaults = questionary.confirm(
            "Standard-URLs für München verwenden?",
            default=True,
        ).ask()
        if use_defaults:
            search_urls = default_urls

    if not search_urls:
        search_urls = default_urls

    # 7. Speichern
    profile = UserProfile(
        persona_block=persona_block,
        persona=persona,
        persona_name=first_name,
        search_urls=search_urls,
    )

    env_data = EnvData(
        email=email,
        password=password,
        groq_api_key=groq_key,
        google_drive_link=google_drive,
        groq_model=groq_model,
    )
    _write_env(env_data)
    _write_profile(profile)

    console.print()
    console.print(Panel.fit(
        "[bold green]Setup abgeschlossen![/bold green]\n\n"
        "Deine Konfiguration wurde gespeichert:\n"
        f"  • .env (Anmeldedaten)\n"
        f"  • user_profile.json (Profil & Such-URLs)\n\n"
        "Starte FlatScraper mit:\n"
        "  [cyan]flatscraper --no-send[/cyan]  (Test ohne Senden)\n"
        "  [cyan]flatscraper[/cyan]  (Mit Senden)",
        border_style="green",
    ))


if __name__ == "__main__":
    run_setup()
