"""OpenRouter LLM client — OpenAI-compatible SDK, any model."""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from backend.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

# Free fallback chain — if primary is rate-limited, try the next
FALLBACK_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openrouter/elephant-alpha",
    "arcee-ai/trinity-large-preview:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-3-27b-it:free",
]


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        _client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    return _client


async def chat(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """Single chat completion with automatic fallback on rate limits."""
    client = get_client()
    primary = model or settings.llm_model
    models_to_try = [primary] + [m for m in FALLBACK_MODELS if m != primary]

    last_error: Exception | None = None
    for m in models_to_try:
        try:
            response = await client.chat.completions.create(
                model=m,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")
            if m != primary:
                logger.info(f"Used fallback model: {m}")
            return content.strip()
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                logger.warning(f"Model {m} rate-limited, trying next...")
                last_error = e
                continue
            raise

    raise last_error or RuntimeError("All models rate-limited")
