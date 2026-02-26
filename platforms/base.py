"""Abstract base for flat search platforms."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from playwright.sync_api import Page


@dataclass
class Listing:
    """Parsed listing from search results (platform-agnostic)."""
    ad_id: str
    title: str
    url: str
    price: str
    size: str
    age_minutes: int | None
    raw_age_text: str


@dataclass
class ListingDetails:
    """Extracted details from a listing detail page (platform-agnostic)."""
    title: str
    address: str
    full_description: str
    ad_id: str
    rent: str
    size: str
    available_from: str
    publisher_name: str
    wg_details: str = ""  # Platform-specific extra
    ad_type: str = "wg"  # "wg" = WG-Zimmer, "wohnung" = Wohnung/1-Zimmer-Wohnung


class Platform(ABC):
    """Base interface for flat search platforms."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Platform identifier."""
        pass

    @abstractmethod
    def login(self, page: Page) -> None:
        """Log in to the platform."""
        pass

    @abstractmethod
    def run_search(self, page: Page, include_all: bool = False) -> list[Listing]:
        """Run search and return listings."""
        pass

    @abstractmethod
    def extract_details(self, page: Page, url: str) -> ListingDetails | None:
        """Extract listing details from a detail page."""
        pass

    @abstractmethod
    def send_message(self, page: Page, listing_url: str, message_text: str) -> bool:
        """Send contact message for a listing."""
        pass
