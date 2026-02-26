"""Abstract base for flat search platforms."""

from abc import ABC, abstractmethod

from playwright.sync_api import Page

from models import Listing, ListingDetails


# Re-export for backward compatibility
__all__ = ["Listing", "ListingDetails", "Platform"]


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
