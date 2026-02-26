#!/usr/bin/env python3
"""
WG-Gesucht search module.
Scans organic listings (excludes partner section), filters by age (< 1 hour).
"""

import re
import time

from playwright.sync_api import Page

from config import get_search_urls
from models import Listing
from platforms.wggesucht.config import MAX_LISTING_AGE_HOURS, EXCLUDED_PROVIDERS, WG_SEARCH_URLS as DEFAULT_WG_SEARCH_URLS


def _parse_online_age(text: str) -> tuple[int | None, str]:
    """
    Parse "Online: X Minuten" or "X Min." or "X Stunde(n)" to minutes.
    Returns (minutes, raw_text).
    """
    text = text.strip()
    m = re.search(r"(?:Online:\s*)?(\d+)\s*Minuten?", text, re.I)
    if m:
        return int(m.group(1)), text
    m = re.search(r"(?:Online:\s*)?1\s+Stunde\b", text, re.I)
    if m:
        return 60, text
    m = re.search(r"(?:Online:\s*)?(\d+)\s+Stunden?", text, re.I)
    if m:
        return int(m.group(1)) * 60, text
    if re.search(r"gerade\s+(eben|online|jetzt)", text, re.I):
        return 0, text
    m = re.search(r"(?:Online:\s*)?(\d+)\s+Sekunden?", text, re.I)
    if m:
        return 0, text
    return None, text


def _extract_ad_id_from_url(url: str) -> str:
    """Extract ad ID from URL like .../8125289.html or ...?asset_id=12314053"""
    m = re.search(r"/(\d+)\.html", url)
    if m:
        return m.group(1)
    m = re.search(r"asset_id=(\d+)", url)
    if m:
        return m.group(1)
    return ""


def _get_search_urls() -> list[str]:
    urls = get_search_urls() or DEFAULT_WG_SEARCH_URLS
    if isinstance(urls, str):
        return [urls]
    return list(urls)


def _scan_listings_fallback(page: Page, include_all: bool = False) -> list[Listing]:
    """Fallback: use JavaScript to extract listing data from page."""
    excluded = EXCLUDED_PROVIDERS or []
    result = page.evaluate("""
        (excludedProviders) => {
            const listings = [];
            const partnerHeader = document.evaluate(
                "//*[contains(text(), 'Weitere Angebote von verifizierten Anbietern')]",
                document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
            ).singleNodeValue;
            const stopBefore = partnerHeader ? partnerHeader.getBoundingClientRect().top : Infinity;

            const links = document.querySelectorAll('a[href*=".html"]');
            const seen = new Set();
            for (const a of links) {
                const href = a.getAttribute('href') || '';
                let adId = '';
                if (href.includes('asset_id=')) {
                    const m = href.match(/asset_id=(\\d+)/);
                    adId = m ? m[1] : '';
                } else {
                    const m = href.match(/\\.(\\d{5,})\\.html/) || href.match(/\\/(\\d{5,})\\.html/);
                    adId = m ? m[1] : '';
                }
                if (!adId) continue;
                if (seen.has(adId)) continue;
                if (href.includes('impressum') || href.includes('datenschutz')) continue;

                const card = a.closest('tr') || a.closest('[class*="list"]') || a.closest('[class*="card"]') || a.closest('[class*="offer"]') || a.parentElement;
                if (!card) continue;
                const rect = card.getBoundingClientRect();
                if (rect.top > stopBefore) continue;

                const cardText = card.innerText || '';
                if (!cardText.includes('Online:')) continue;
                if (cardText.includes('kontaktiert') || card.querySelector('.ribbon-contacted')) continue;
                if (excludedProviders && excludedProviders.some(p => cardText.includes(p))) continue;

                const onlineMatch = cardText.match(/Online:\\s*([^\\n]+)/);
                const rawAge = onlineMatch ? onlineMatch[1].trim() : '';
                const priceMatch = cardText.match(/(\\d+\\s*€)\\s*\\|?\\s*(\\d+\\s*m²)/);
                const price = priceMatch ? priceMatch[1] : '';
                const size = priceMatch ? priceMatch[2] : '';
                const title = a.innerText ? a.innerText.substring(0, 100) : '';
                const fullUrl = href.startsWith('http') ? href : 'https://www.wg-gesucht.de' + (href.startsWith('/') ? href : '/' + href);

                seen.add(adId);
                listings.push({
                    ad_id: adId,
                    title: title,
                    url: fullUrl,
                    price: price,
                    size: size,
                    raw_age_text: rawAge
                });
            }
            return listings;
        }
    """, excluded)
    listings = []
    max_age_minutes = int(MAX_LISTING_AGE_HOURS * 60)
    for r in result:
        raw = r.get("raw_age_text", "")
        age_minutes, _ = _parse_online_age(raw)
        if not include_all and (age_minutes is None or age_minutes >= max_age_minutes):
            continue
        listings.append(Listing(
            ad_id=r["ad_id"],
            title=r["title"],
            url=r["url"],
            price=r["price"],
            size=r["size"],
            age_minutes=age_minutes,
            raw_age_text=r.get("raw_age_text", ""),
        ))
    return listings


def run_search(page: Page, include_all_for_debug: bool = False) -> list[Listing]:
    """
    Run search across all WG_SEARCH_URLS, return valid listings (< 1 hour old).
    Deduplicates by ad_id. If include_all_for_debug: return all organic listings.
    """
    urls = _get_search_urls()
    all_listings: list[Listing] = []
    seen_ids: set[str] = set()

    for url in urls:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(2)
        try:
            page.wait_for_selector('a[href*=".html"]', timeout=15000)
        except Exception:
            pass
        time.sleep(2)
        listings = _scan_listings_fallback(page, include_all=include_all_for_debug)
        for lst in listings:
            if lst.ad_id not in seen_ids:
                seen_ids.add(lst.ad_id)
                all_listings.append(lst)

    return all_listings
