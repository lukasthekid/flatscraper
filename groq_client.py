#!/usr/bin/env python3
"""
Groq API client for generating WG Anschreiben (application messages).
Uses Llama models via Groq (e.g. llama-3.1-8b-instant).
"""

from config import (
    GOOGLE_DRIVE_LINK,
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_AD_TYPE_INSTRUCTIONS_WG,
    LLM_AD_TYPE_INSTRUCTIONS_WOHNUNG,
    LLM_MESSAGE_PROMPT_TEMPLATE,
    LLM_SYSTEM_PROMPT,
)


def _build_message_prompt(listing_data: dict) -> str:
    ad_type = listing_data.get("ad_type", "wg")
    ad_type_label = "WG-Zimmer" if ad_type == "wg" else "Wohnung"
    ad_type_instructions = (
        LLM_AD_TYPE_INSTRUCTIONS_WG if ad_type == "wg" else LLM_AD_TYPE_INSTRUCTIONS_WOHNUNG
    )

    return LLM_MESSAGE_PROMPT_TEMPLATE.format(
        title=listing_data.get("title", ""),
        address=listing_data.get("address", ""),
        publisher_name=listing_data.get("publisher_name", ""),
        description=listing_data.get("full_description", ""),
        google_drive_link=listing_data.get("google_drive", GOOGLE_DRIVE_LINK),
        ad_type_label=ad_type_label,
        ad_type_instructions=ad_type_instructions,
    )


def generate_anschreiben(listing_data: dict) -> str:
    """
    Call Groq API to generate WG Anschreiben.
    listing_data: dict with title, address, publisher_name, full_description, google_drive (optional)
    """
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY not set. Set GROQ_API_KEY in your .env file or environment"
        )

    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    user_content = _build_message_prompt(listing_data)

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.8,
        max_completion_tokens=2048,
        top_p=1,
    )

    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("Groq API returned empty response")
    return content.strip()
