#!/usr/bin/env python3
"""
Send WG Anschreiben via WG-Gesucht message form.
"""

import time

from playwright.sync_api import Page


def _message_url_from_listing_url(listing_url: str) -> str:
    """Build message page URL from listing URL."""
    return listing_url.replace("wg-gesucht.de/", "wg-gesucht.de/nachricht-senden/")


def send_anschreiben(page: Page, listing_url: str, message_text: str) -> bool:
    """
    Navigate to message page, fill the Anschreiben, and send.
    Returns True if sent successfully, False otherwise.
    """
    message_url = _message_url_from_listing_url(listing_url)
    page.goto(message_url, wait_until="domcontentloaded", timeout=15000)
    time.sleep(2)

    try:
        textarea = page.locator(
            'textarea[name="message"], textarea[id*="message"], '
            'textarea[placeholder*="Nachricht"], textarea[placeholder*="Message"], '
            'form textarea'
        ).first
        textarea.wait_for(state="visible", timeout=8000)
        textarea.fill(message_text)
        time.sleep(0.5)

        try:
            modal_btn = page.locator("#sec_advice button, #sec_advice .modal-footer button").first
            if modal_btn.is_visible(timeout=1000):
                modal_btn.click(timeout=3000)
                time.sleep(0.8)
        except Exception:
            pass

        try:
            page.evaluate("""
                const m = document.getElementById('sec_advice');
                if (m) {
                    if (typeof $ !== 'undefined') $('#sec_advice').modal('hide');
                    else m.style.display = 'none';
                }
            """)
            time.sleep(0.5)
        except Exception:
            pass

        send_btn = page.locator(
            'button.conversation_send_button, button:has-text("Senden"), '
            'input[type="submit"][value*="Senden"]'
        ).first
        send_btn.click(timeout=5000)
        time.sleep(2)
        return True
    except Exception:
        return False
