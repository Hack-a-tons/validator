"""OpenAI arbitration for protected-likeness validation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from openai import OpenAI
from pydantic import BaseModel, Field


class ArbitrationError(RuntimeError):
    """Raised when a reliable verdict cannot be returned."""


class _ArbitrationPayload(BaseModel):
    verdict: str = Field(pattern="^(DECLINE|APPROVE)$")
    reasoning: str = Field(min_length=1, max_length=600)


@dataclass(frozen=True)
class Verdict:
    verdict: str
    reasoning: str


def arbitrate(protected_description: str, visual_description: str) -> Verdict:
    """Return DECLINE for a likely match and APPROVE only for clear differences."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ArbitrationError("OPENAI_API_KEY is not configured.")

    prompt = f"""You are a conservative visual-likeness safety arbiter.
Compare the protected description with the observed visual description. Do not infer
identity from a name, reputation, context, or any feature not stated below. Compare
only the observable attributes. Return DECLINE when the descriptions materially
match or evidence is too limited to confidently rule out a match. Return APPROVE
only when clear, material visual differences rule out the protected description.

Protected description:\n{protected_description}\n\nObserved visual description:\n{visual_description}\n
Respond with JSON only: {{"verdict":"DECLINE or APPROVE","reasoning":"brief explanation"}}"""
    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=prompt,
            temperature=0,
        )
        payload = _ArbitrationPayload.model_validate(json.loads(response.output_text))
    except Exception as exc:
        raise ArbitrationError(f"OpenAI arbitration failed: {exc}") from exc
    return Verdict(verdict=payload.verdict, reasoning=payload.reasoning)
