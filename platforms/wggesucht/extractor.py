#!/usr/bin/env python3
"""
Extract listing details from a WG-Gesucht detail page for Anschreiben generation.
"""

from dataclasses import dataclass

from playwright.sync_api import Page

from platforms.base import ListingDetails as BaseListingDetails


def extract_listing_details(page: Page, url: str) -> BaseListingDetails | None:
    """
    Navigate to listing URL and extract all data needed for WG Anschreiben.
    Returns None if extraction fails.
    """
    page.goto(url, wait_until="domcontentloaded", timeout=25000)
    page.wait_for_load_state("domcontentloaded")
    import time
    time.sleep(1.5)

    try:
        if page.get_by_text("Unterhaltung ansehen").first.is_visible(timeout=2000):
            return None
    except Exception:
        pass

    try:
        data = page.evaluate("""
            () => {
                const body = document.body.innerText;
                let title = '';
                const h1 = document.querySelector('h1');
                if (h1) title = h1.innerText.replace(/\\s+/g, ' ').trim();

                let address = '';
                const addrMatch = body.match(/Adresse\\s*\\n\\s*([^\\n]+)/);
                if (addrMatch) address = addrMatch[1].trim();

                let full_description = '';
                const beschStart = body.indexOf('Das Zimmer ist') >= 0 ? body.indexOf('Das Zimmer ist') :
                    body.indexOf('Zimmer') >= 0 ? body.indexOf('Zimmer') : body.indexOf('Kosten');
                const beschEnd = body.indexOf('WG-Gesucht+');
                if (beschStart >= 0 && beschEnd > beschStart) {
                    full_description = body.substring(beschStart, beschEnd).trim();
                } else {
                    const wgIdx = body.indexOf('WG-Details');
                    if (wgIdx > 0) full_description = body.substring(0, wgIdx).trim();
                    else full_description = body.substring(0, 5000);
                }
                if (full_description.length > 8000) full_description = full_description.substring(0, 8000);

                const idMatch = window.location.href.match(/\\.(\\d{5,})\\.html/) ||
                    window.location.href.match(/asset_id=(\\d+)/);
                const ad_id = idMatch ? idMatch[1] : '';

                const rentMatch = body.match(/Gesamtmiete\\s*:\\s*([^\\n]+)|(\\d+\\s*€)\\s*\\|/);
                const rent = rentMatch ? (rentMatch[1] || rentMatch[2] || '').trim() : '';

                const sizeMatch = body.match(/Zimmergröße\\s*:\\s*([^\\n]+)|Größe\\s*:\\s*([^\\n]+)|(\\d+\\s*m²)/);
                const size = sizeMatch ? (sizeMatch[1] || sizeMatch[2] || sizeMatch[3] || '').trim() : '';

                let ad_type = 'wohnung';
                const wgDetailsEl = Array.from(document.querySelectorAll('h2.section_panel_title')).find(h => h.textContent.trim() === 'WG-Details');
                if (wgDetailsEl) ad_type = 'wg';

                const availMatch = body.match(/frei ab:\\s*([^\\n]+)|(\\d{2}\\.\\d{2}\\.\\d{4})/);
                const available_from = availMatch ? (availMatch[1] || availMatch[2] || '').trim() : '';

                let publisher_name = '';
                const profileInfo = document.querySelector('.user_profile_info');
                if (profileInfo) {
                    const firstP = profileInfo.querySelector('.vertical-align-center-column.ml20 p.mb0, .ml20 p.mb0, p.mb0');
                    if (firstP) {
                        const name = firstP.innerText.replace(/\\s+/g, ' ').trim();
                        if (name.length >= 2 && name.length <= 60 && !/Mitglied seit|Verifiziert|€|m²|WG-Gesucht|impressum|datenschutz|Private/i.test(name)) {
                            publisher_name = name;
                        }
                    }
                }
                if (!publisher_name) {
                    const stickyB = document.querySelector('.contact_box_sticky b');
                    if (stickyB && stickyB.innerText) {
                        const name = stickyB.innerText.replace(/\\s+/g, ' ').trim();
                        if (name.length >= 2 && name.length <= 60) publisher_name = name;
                    }
                }
                if (!publisher_name) {
                    const onlineEl = document.evaluate("//*[contains(text(), 'Online:')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (onlineEl) {
                        const parent = onlineEl.closest('.row') || onlineEl.closest('.card_body') || onlineEl.parentElement;
                        if (parent) {
                            const block = parent.innerText || '';
                            const beforeOnline = block.split('Online:')[0] || '';
                            const lines = beforeOnline.trim().split(/\\n/);
                            const lastLine = (lines[lines.length - 1] || '').replace(/\\s+/g, ' ').trim();
                            if (lastLine.length >= 2 && lastLine.length <= 50 && !/Verifiziert|€|m²|WG-Gesucht|impressum|datenschutz|\\d{4}/i.test(lastLine)) {
                                publisher_name = lastLine;
                            }
                        }
                    }
                }
                if (!publisher_name) {
                    const ml5 = document.querySelector('.ml5');
                    if (ml5 && ml5.innerText && ml5.innerText.length >= 2 && ml5.innerText.length <= 50) {
                        publisher_name = ml5.innerText.trim();
                    }
                }

                return {
                    title: title,
                    address: address,
                    full_description: full_description,
                    ad_id: ad_id,
                    rent: rent,
                    size: size,
                    available_from: available_from,
                    wg_details: '',
                    publisher_name: publisher_name,
                    ad_type: ad_type
                };
            }
        """)
        if not data or not data.get("title"):
            return None
        return BaseListingDetails(
            title=data.get("title", ""),
            address=data.get("address", ""),
            full_description=data.get("full_description", ""),
            ad_id=data.get("ad_id", ""),
            rent=data.get("rent", ""),
            size=data.get("size", ""),
            available_from=data.get("available_from", ""),
            publisher_name=data.get("publisher_name", ""),
            wg_details=data.get("wg_details", ""),
            ad_type=data.get("ad_type", "wg"),
        )
    except Exception:
        return None
