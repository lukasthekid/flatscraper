#!/usr/bin/env python3
"""
FlatScraper - flat search automation (WG-Gesucht).
Run: python run.py [--platform wggesucht] [--once] [--schedule] [--no-send] [--debug]
"""

import sys
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
from config import (
    GOOGLE_DRIVE_LINK,
    RUN_INTERVAL_MINUTES,
    AUTO_RUN_ENABLED,
    GROQ_MODEL,
)
from groq_client import generate_anschreiben
from platforms import PLATFORMS


def _parse_args():
    argv = sys.argv[1:]
    platform = "wggesucht"
    for a in argv:
        if not a.startswith("-") and a.lower() in PLATFORMS:
            platform = a.lower()
            break
    for i, a in enumerate(argv):
        if a == "--platform" and i + 1 < len(argv):
            platform = argv[i + 1].lower()
            break
    return platform


def run_platform(platform, page):
    """Run crawler for the given platform."""
    debug = "--debug" in sys.argv or "-d" in sys.argv
    no_send = "--no-send" in sys.argv

    print(f"\n=== Login ({platform.name}) ===")
    platform.login(page)

    listings = platform.run_search(page, include_all=debug)
    if debug:
        print(f"Found {len(listings)} organic listings (all, DEBUG mode)")
    else:
        print(f"Found {len(listings)} organic listings < 1 hour old")

    for i, listing in enumerate(listings, 1):
        print(f"\n--- Listing {i}: {listing.url} ---")
        print(f"   ID: {listing.ad_id} | {listing.price} | {listing.size} | {listing.raw_age_text}")

        print("   Opening listing page...")
        details = platform.extract_details(page, listing.url)
        if not details:
            try:
                if page.get_by_text("Unterhaltung ansehen").first.is_visible():
                    print("   [SKIP] Already contacted (Unterhaltung ansehen)")
                else:
                    print("   [SKIP] Could not extract listing details")
            except Exception:
                print("   [SKIP] Could not extract listing details")
            continue

        print(f"   Title: {details.title[:60]}...")
        print(f"   Address: {details.address}")

        print(f"   Generating Anschreiben with {GROQ_MODEL}...")
        anschreiben = None
        try:
            listing_data = {
                "title": details.title,
                "address": details.address,
                "publisher_name": details.publisher_name or "",
                "full_description": details.full_description,
                "google_drive": GOOGLE_DRIVE_LINK,
                "ad_type": details.ad_type,
            }
            anschreiben = generate_anschreiben(listing_data)
            print("\n   === GENERATED ANSCHREIBEN (vollständig) ===\n")
            print(anschreiben)
            print("\n   === ENDE ANSCHREIBEN ===")
            print(f"   Länge: {len(anschreiben)} Zeichen, {len(anschreiben.split())} Wörter\n")
        except Exception as e:
            print(f"   [ERROR] LLM: {e}")

        if anschreiben and not no_send:
            print("   Sending message...")
            platform.send_message(page, listing.url, anschreiben)
        elif anschreiben and no_send:
            print("   [SKIP] Message not sent (--no-send)")


def main():
    platform_name = _parse_args()
    use_schedule = (
        "--schedule" in sys.argv
        or (AUTO_RUN_ENABLED and "--once" not in sys.argv)
    )

    if platform_name not in PLATFORMS:
        valid = ", ".join(PLATFORMS.keys())
        print(f"Unknown platform: {platform_name}. Use --platform {valid}")
        return

    platform = PLATFORMS[platform_name]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="de-DE",
        )
        page = context.new_page()

        if use_schedule:
            print(f"[Mode] Scheduled: every {RUN_INTERVAL_MINUTES} min (use --once for single run)")
        else:
            print("[Mode] Single run (use --schedule for repeated runs)")

        cycle = 0
        while True:
            cycle += 1
            if use_schedule and cycle > 1:
                print(f"\n=== [Cycle {cycle}] Next run in {RUN_INTERVAL_MINUTES} minutes ===")
                time.sleep(RUN_INTERVAL_MINUTES * 60)

            print(f"\n=== Search (cycle {cycle}) ===")
            run_platform(platform, page)

            if not use_schedule:
                print("\n=== Done ===")
                break

            if "--quick" in sys.argv:
                break

        if "--quick" in sys.argv:
            time.sleep(5)
            browser.close()
        else:
            try:
                input("Press Enter to close browser...")
            except EOFError:
                pass
            browser.close()


if __name__ == "__main__":
    main()
