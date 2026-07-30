"""TwelveLabs visual-description integration."""

from __future__ import annotations

import os

from twelvelabs import TwelveLabs
from twelvelabs.types import VideoContext_Url


class TwelveLabsError(RuntimeError):
    """Raised when TwelveLabs cannot produce an analysis."""


_VISUAL_PROMPT = """Describe the primary visible person or subject for likeness comparison.
Focus only on observable visual details: apparent age range, presentation, hair,
facial features, skin tone, build, clothing, accessories, and distinctive marks.
Describe uncertainty explicitly. Do not identify or guess a real person's name.
Return one concise but comprehensive paragraph."""


def describe_primary_subject(video_url: str) -> str:
    """Analyze a public direct video URL and return visual attributes only."""
    api_key = os.getenv("TWELVELABS_API_KEY")
    if not api_key:
        raise TwelveLabsError("TWELVELABS_API_KEY is not configured.")

    try:
        client = TwelveLabs(api_key=api_key)
        stream = client.analyze_stream(
            model_name="pegasus1.5",
            video=VideoContext_Url(url=video_url),
            prompt=_VISUAL_PROMPT,
            temperature=0.1,
            max_tokens=700,
        )
        parts = [event.text for event in stream if getattr(event, "event_type", "") == "text_generation"]
    except Exception as exc:  # SDK exceptions vary by installed version.
        raise TwelveLabsError(f"TwelveLabs analysis failed: {exc}") from exc

    description = "".join(parts).strip()
    if not description:
        raise TwelveLabsError("TwelveLabs returned no visual description.")
    return description
