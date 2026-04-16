"""Tests for async retry utility."""

import asyncio
import pytest

from backend.utils.retry import retry_async


@pytest.mark.asyncio
async def test_succeeds_on_first_try():
    calls = []

    async def fn():
        calls.append(1)
        return "ok"

    result = await retry_async(fn, retries=3, base_delay=0)
    assert result == "ok"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_retries_on_failure_then_succeeds():
    calls = []

    async def fn():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("not yet")
        return "done"

    result = await retry_async(fn, retries=3, base_delay=0)
    assert result == "done"
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_raises_after_all_retries_exhausted():
    async def fn():
        raise RuntimeError("always fails")

    with pytest.raises(RuntimeError, match="always fails"):
        await retry_async(fn, retries=3, base_delay=0)


@pytest.mark.asyncio
async def test_passes_args_and_kwargs():
    async def fn(a, b, *, c):
        return a + b + c

    result = await retry_async(fn, 1, 2, retries=1, base_delay=0, c=10)
    assert result == 13
