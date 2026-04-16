"""Async retry with exponential backoff for API calls."""

from __future__ import annotations

import asyncio
import logging
from typing import TypeVar, Callable, Awaitable

T = TypeVar("T")
logger = logging.getLogger(__name__)


async def retry_async(
    fn: Callable[..., Awaitable[T]],
    *args,
    retries: int = 3,
    base_delay: float = 2.0,
    **kwargs,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < retries:
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(f"Attempt {attempt}/{retries} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {retries} attempts failed: {e}")
    raise last_error  # type: ignore
