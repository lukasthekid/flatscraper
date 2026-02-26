"""WG-Gesucht.de platform."""

from platforms.base import ListingDetails
from platforms.wggesucht.config import PLATFORM_NAME
from platforms.wggesucht.search import run_search, Listing
from platforms.wggesucht.extractor import extract_listing_details
from platforms.wggesucht.login import login_wggesucht, accept_cookie_banner
from platforms.wggesucht.messenger import send_anschreiben

__all__ = [
    "PLATFORM_NAME",
    "run_search",
    "Listing",
    "extract_listing_details",
    "ListingDetails",
    "login_wggesucht",
    "accept_cookie_banner",
    "send_anschreiben",
]
