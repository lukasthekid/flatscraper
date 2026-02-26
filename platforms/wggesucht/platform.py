"""WG-Gesucht platform implementation of the Platform ABC."""

from platforms.base import Platform, Listing, ListingDetails
from platforms.wggesucht.login import login_wggesucht
from platforms.wggesucht.search import run_search
from platforms.wggesucht.extractor import extract_listing_details
from platforms.wggesucht.messenger import send_anschreiben

from playwright.sync_api import Page


class WgGesuchtPlatform(Platform):
    """WG-Gesucht.de platform implementation."""

    @property
    def name(self) -> str:
        return "wggesucht"

    def login(self, page: Page) -> None:
        login_wggesucht(page)

    def run_search(self, page: Page, include_all: bool = False) -> list[Listing]:
        return run_search(page, include_all_for_debug=include_all)

    def extract_details(self, page: Page, url: str) -> ListingDetails | None:
        return extract_listing_details(page, url)

    def send_message(self, page: Page, listing_url: str, message_text: str) -> bool:
        return send_anschreiben(page, listing_url, message_text)
