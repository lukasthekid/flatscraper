#!/usr/bin/env python3
"""
FlatScraper - flat search automation (WG-Gesucht).
CLI: flatscraper | flatscraper --no-send | flatscraper --visible | flatscraper setup
"""

import sys
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.table import Table

from config import (
    AUTO_RUN_ENABLED,
    GOOGLE_DRIVE_LINK,
    GROQ_MODEL,
    RUN_INTERVAL_MINUTES,
)
from groq_client import generate_anschreiben
from models import ListingData
from platforms import PLATFORMS

console = Console()


def run_platform(platform, page) -> None:
    """Run crawler for the given platform."""
    debug = "--debug" in sys.argv or "-d" in sys.argv
    no_send = "--no-send" in sys.argv

    # Login
    console.print()
    console.print(Rule("[bold]Anmeldung[/bold]", style="blue"))
    platform.login(page)

    # Search
    console.print()
    console.print(Rule("[bold]Suche[/bold]", style="blue"))
    with console.status("[bold green]Durchsuche WG-Gesucht...[/bold green]", spinner="dots"):
        listings = platform.run_search(page, include_all=debug)

    if not listings:
        console.print("[yellow]Keine neuen Anzeigen gefunden.[/yellow]")
        return

    age_info = "alle Anzeigen (Debug)" if debug else "unter 1 Stunde alt"
    console.print(f"[green]Gefunden: {len(listings)} Anzeigen[/green] ({age_info})")
    console.print()

    # Process each listing
    for i, listing in enumerate(listings, 1):
        console.print(Panel.fit(
            f"[bold]{listing.title[:70]}{'...' if len(listing.title) > 70 else ''}[/bold]\n"
            f"ID: {listing.ad_id}  |  {listing.price}  |  {listing.size}  |  {listing.raw_age_text}\n"
            f"[dim]{listing.url}[/dim]",
            title=f"Anzeige {i}/{len(listings)}",
            border_style="cyan",
        ))

        with console.status("[dim]Öffne Anzeige...[/dim]", spinner="dots"):
            details = platform.extract_details(page, listing.url)

        if not details:
            try:
                if page.get_by_text("Unterhaltung ansehen").first.is_visible():
                    console.print("  [yellow]→ Bereits kontaktiert, übersprungen[/yellow]")
                else:
                    console.print("  [yellow]→ Details konnten nicht extrahiert werden[/yellow]")
            except Exception:
                console.print("  [yellow]→ Details konnten nicht extrahiert werden[/yellow]")
            console.print()
            continue

        # Listing info
        table = Table(show_header=False)
        table.add_column("", style="dim", width=12)
        table.add_column("")
        table.add_row("Titel", details.title[:80] + ("..." if len(details.title) > 80 else ""))
        table.add_row("Adresse", details.address)
        table.add_row("Typ", "WG-Zimmer" if details.ad_type == "wg" else "Wohnung")
        console.print(table)

        # Generate Anschreiben
        def on_rate_limit(wait_sec: float, attempt: int) -> None:
            console.print(f"  [yellow]Rate limit – warte {wait_sec:.0f}s (Versuch {attempt + 1}/4)...[/yellow]")

        with console.status(f"[dim]Generiere Anschreiben mit {GROQ_MODEL}...[/dim]", spinner="dots"):
            anschreiben = None
            try:
                data = ListingData(
                    title=details.title,
                    address=details.address,
                    publisher_name=details.publisher_name or "",
                    full_description=details.full_description,
                    google_drive=GOOGLE_DRIVE_LINK,
                    ad_type=details.ad_type,
                )
                anschreiben = generate_anschreiben(data, on_retry=on_rate_limit)
            except Exception as e:
                console.print(f"  [red]Fehler bei KI-Generierung: {e}[/red]")

        if anschreiben:
            console.print()
            console.print(Panel(
                anschreiben,
                title="[bold]Generiertes Anschreiben[/bold]",
                subtitle=f"{len(anschreiben)} Zeichen, {len(anschreiben.split())} Wörter",
                border_style="green",
            ))

            if no_send:
                console.print("  [yellow]→ Nicht gesendet (--no-send)[/yellow]")
            else:
                with console.status("[dim]Sende Nachricht...[/dim]", spinner="dots"):
                    success = platform.send_message(page, listing.url, anschreiben)
                if success:
                    console.print("  [green]✓ Nachricht gesendet[/green]")
                else:
                    console.print("  [red]✗ Senden fehlgeschlagen[/red]")

        console.print()


def main() -> None:
    # Setup-Assistent
    if len(sys.argv) >= 2 and sys.argv[1].lower() == "setup":
        from setup_wizard import run_setup
        run_setup()
        return

    # Banner
    console.print()
    console.print(Panel.fit(
        "[bold]FlatScraper[/bold]\n"
        "WG-Gesucht Automatisierung – sucht Anzeigen, generiert Anschreiben, sendet Nachrichten.",
        border_style="green",
    ))

    platform = PLATFORMS["wggesucht"]
    use_schedule = "--schedule" in sys.argv or AUTO_RUN_ENABLED

    if use_schedule:
        console.print(f"[dim]Modus: Alle {RUN_INTERVAL_MINUTES} Min.[/dim]")
    else:
        console.print("[dim]Modus: Einmal durchlaufen[/dim]")

    if "--no-send" in sys.argv:
        console.print("[yellow]Hinweis: Nachrichten werden nicht gesendet (--no-send)[/yellow]")

    show_browser = "--visible" in sys.argv or "-v" in sys.argv
    if show_browser:
        console.print("[dim]Browser sichtbar (--visible)[/dim]")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not show_browser)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="de-DE",
        )
        page = context.new_page()

        cycle = 0
        while True:
            cycle += 1
            if use_schedule and cycle > 1:
                console.print()
                console.print(f"[dim]Nächster Lauf in {RUN_INTERVAL_MINUTES} Minuten...[/dim]")
                time.sleep(RUN_INTERVAL_MINUTES * 60)

            run_platform(platform, page)

            if not use_schedule:
                break
            if "--quick" in sys.argv:
                break

        # Abschluss
        console.print()
        console.print(Rule("[bold green]Fertig[/bold green]", style="green"))
        if not use_schedule:
            console.print("FlatScraper wurde einmal durchlaufen.")

        if "--quick" in sys.argv:
            time.sleep(5)
            browser.close()
        else:
            try:
                console.print()
                input("Enter drücken zum Beenden...")
            except EOFError:
                pass
            browser.close()


if __name__ == "__main__":
    main()
