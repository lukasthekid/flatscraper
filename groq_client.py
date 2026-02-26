#!/usr/bin/env python3
"""
Groq API client for generating WG Anschreiben (application messages).
Uses Llama models via Groq.
"""

import re
import time
from typing import Callable

from config import (
    GOOGLE_DRIVE_LINK,
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_AD_TYPE_INSTRUCTIONS_WG,
    LLM_AD_TYPE_INSTRUCTIONS_WOHNUNG,
    LLM_MESSAGE_PROMPT_TEMPLATE,
    LLM_SYSTEM_PROMPT,
    get_persona_name,
)
from models import ListingData


def _build_message_prompt(data: ListingData) -> str:
    ad_type = data.ad_type
    ad_type_label = "WG-Zimmer" if ad_type == "wg" else "Wohnung"
    ad_type_instructions = (
        LLM_AD_TYPE_INSTRUCTIONS_WG if ad_type == "wg" else LLM_AD_TYPE_INSTRUCTIONS_WOHNUNG
    )

    return LLM_MESSAGE_PROMPT_TEMPLATE.format(
        title=data.title,
        address=data.address,
        publisher_name=data.publisher_name,
        description=data.full_description,
        google_drive_link=data.google_drive or GOOGLE_DRIVE_LINK,
        ad_type_label=ad_type_label,
        ad_type_instructions=ad_type_instructions,
        persona_name=get_persona_name(),
    )


def _extract_message_only(raw: str) -> str:
    """
    Strip LLM meta-commentary (thoughts, explanations) and return only the actual message.
    Some models output reasoning before/around the message; we need just the message.
    """
    text = raw.strip()
    original = text

    # Common separators before the actual message (e.g. "---" between thoughts and message)
    for sep in ("\n---\n", "---\n", "---"):
        if sep in text:
            parts = text.split(sep, 1)
            if len(parts) == 2:
                for part in (parts[1], parts[0]):
                    if re.search(r"\b(Hallo|Hi|Sehr geehrte)\b", part, re.I):
                        text = part.strip()
                        break
            break

    # Find start of actual message; drop meta-commentary before first greeting
    match = re.search(
        r"^(.*?)((?:Hallo|Hi|Sehr geehrte)[^\n]*(?:\n|$))",
        text,
        re.I | re.DOTALL,
    )
    if match:
        prefix = match.group(1).strip()
        if any(
            x in prefix.lower()
            for x in ("kurzfassung", "überlegungen", "gedanken", "anrede-regel", "icebreaker")
        ):
            text = match.group(2) + text[match.end() :]

    result = text.strip()
    # Fallback: if extraction left almost nothing, keep original
    if len(result) < 30 and len(original) > 50:
        return original
    return result


def _parse_retry_after(error: Exception) -> float | None:
    """Parse 'try again in X.XXs' from Groq rate limit error. Returns seconds or None."""
    msg = str(error)
    m = re.search(r"try again in ([\d.]+)\s*s", msg, re.I)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def generate_anschreiben(
    listing_data: ListingData,
    *,
    on_retry: Callable[[float, int], None] | None = None,
) -> str:
    """
    Call Groq API to generate WG Anschreiben.
    Retries on rate limit (429) with backoff. on_retry(wait_seconds, attempt) is called before each wait.
    """
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY not set. Set GROQ_API_KEY in your .env file or environment"
        )

    import groq
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    user_content = _build_message_prompt(listing_data)
    max_retries = 4

    for attempt in range(max_retries):
        try:
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
            return _extract_message_only(content.strip())
        except groq.RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = _parse_retry_after(e) or 5.0
            if on_retry:
                on_retry(wait_time, attempt + 1)
            time.sleep(wait_time)
