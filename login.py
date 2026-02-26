#!/usr/bin/env python3
"""
Standalone login test. Opens WG-Gesucht and logs in.
Usage: python login.py [--platform wggesucht]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
from platforms.wggesucht import login_wggesucht
from platforms.wggesucht.config import BASE_URL


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="de-DE",
        )
        page = context.new_page()
        print("Navigating to WG-Gesucht.de...")
        page.goto(BASE_URL, wait_until="domcontentloaded")
        login_wggesucht(page)
        input("\nPress Enter to close the browser...")
        browser.close()


if __name__ == "__main__":
    main()
