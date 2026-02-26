#!/usr/bin/env python3
"""
WG-Gesucht login.
"""

import time

from playwright.sync_api import Page

from config import EMAIL, PASSWORD
from platforms.wggesucht.config import BASE_URL


def accept_cookie_banner(page: Page) -> bool:
    """Dismiss cookie consent banner if present."""
    cookie_selectors = [
        'button:has-text("Alle akzeptieren")',
        'button:has-text("Akzeptieren")',
        'a:has-text("Alle akzeptieren")',
        '[class*="accept"]',
        '[id*="accept"]',
        '[class*="cmp"] button',
        '[class*="consent"] button',
    ]
    for selector in cookie_selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=1000):
                btn.click()
                print("Cookie banner accepted.")
                time.sleep(0.5)
                return True
        except Exception:
            continue
    return False


def login_wggesucht(page: Page) -> None:
    """Log in to WG-Gesucht."""
    page.goto(BASE_URL, wait_until="domcontentloaded")
    time.sleep(2)
    accept_cookie_banner(page)
    time.sleep(0.5)

    mein_konto = page.locator('a:has-text("Mein Konto"), button:has-text("Mein Konto")').first
    mein_konto.click(timeout=3000)
    time.sleep(1)

    page.evaluate("""
        (function() {
            if (typeof fireLoginOrRegisterModalRequest === 'function') {
                fireLoginOrRegisterModalRequest('sign_in');
            } else if (typeof $ !== 'undefined') {
                $('#login_modal').modal('show');
            }
        })();
    """)
    time.sleep(1.5)
    if not page.locator("#login_email_username").is_visible():
        page.locator('a[onclick*="sign_in"]').first.click(force=True, timeout=2000)
        time.sleep(1)
    page.evaluate("$('#login_modal').modal('show')")
    time.sleep(0.5)

    page.locator("#login_email_username").wait_for(state="visible", timeout=5000)
    page.locator("#login_email_username").fill(EMAIL)
    page.locator("#login_password").fill(PASSWORD)
    page.locator("#auto_login").check()
    page.locator("#login_submit").click()
    time.sleep(3)

    if page.locator("text=Login bestätigen").first.is_visible():
        print("2FA required - enter the 6-digit code in the browser, then press Enter here...")
        input()
        time.sleep(2)
    if not (page.locator("text=Mein Konto").first.is_visible() or page.locator("text=Abmelden").first.is_visible()):
        if page.locator("text=Falsche E-Mail-Adresse").first.is_visible() or page.locator("text=Unbekannte E-Mail-Adresse").first.is_visible():
            raise RuntimeError("Login failed: Invalid email or password")
        raise RuntimeError("Login failed")
    print("[OK] Logged in")
