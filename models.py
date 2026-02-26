"""
Pydantic models for type-safe configuration and data structures.
"""

from pydantic import BaseModel, Field


# --- Platform / Listing models ---


class Listing(BaseModel):
    """Parsed listing from search results (platform-agnostic)."""

    ad_id: str
    title: str
    url: str
    price: str
    size: str
    age_minutes: int | None
    raw_age_text: str


class ListingDetails(BaseModel):
    """Extracted details from a listing detail page (platform-agnostic)."""

    title: str
    address: str
    full_description: str
    ad_id: str
    rent: str
    size: str
    available_from: str
    publisher_name: str
    wg_details: str = ""
    ad_type: str = "wg"


class ListingData(BaseModel):
    """Input for LLM Anschreiben generation."""

    title: str
    address: str
    publisher_name: str = ""
    full_description: str
    google_drive: str = ""
    ad_type: str = "wg"


# --- User profile models ---


class Persona(BaseModel):
    """User persona for personalized Anschreiben."""

    first_name: str = "Nutzer"
    age: str = ""
    from_city: str = ""
    target_city: str = ""
    looking_for: str = ""
    job: str = ""
    move_in: str = "So schnell wie möglich"
    personality: str = ""
    hobbies: str = ""
    documents: str = "Alle Unterlagen im Google Drive Link"


class UserProfile(BaseModel):
    """Full user profile (user_profile.json)."""

    persona_block: str
    persona: Persona
    persona_name: str = "Nutzer"
    search_urls: list[str] = Field(default_factory=list)


# --- Setup wizard models ---


class EnvData(BaseModel):
    """Credentials and API keys for .env file."""

    email: str = ""
    password: str = ""
    groq_api_key: str = ""
    google_drive_link: str = ""
    groq_model: str = "llama-3.1-8b-instant"
