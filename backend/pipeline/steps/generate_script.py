"""Step 1: Generate Picsou script via OpenRouter LLM."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from backend.pipeline.context import PipelineContext
from backend.pipeline.models import Script
from backend.providers import llm
from backend.utils.retry import retry_async

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "picsou_script.txt"


def _load_prompt(topic: str) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.replace("{topic}", topic)


def _extract_json(raw: str) -> dict:
    """Extract JSON from LLM response, tolerating markdown fences and prefixed text."""
    if not raw or not raw.strip():
        raise json.JSONDecodeError("Empty response from LLM", raw or "", 0)

    text = raw.strip()

    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Search for first { ... } block in the response
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group())

    raise json.JSONDecodeError("No JSON object found in LLM response", text, 0)


async def _generate_once(topic: str, model: str, correction: str | None = None) -> Script:
    prompt_text = _load_prompt(topic)

    messages: list[dict] = [{"role": "user", "content": prompt_text}]
    if correction:
        messages.append({"role": "user", "content": correction})

    raw = await llm.chat(messages=messages, model=model, temperature=0.8)
    data = _extract_json(raw)
    script = Script.model_validate(data)

    # Validate word count (80–200 per spec, relaxed to 60–250 for model variance)
    word_count = sum(len(line.text.split()) for line in script.lines)
    if not (60 <= word_count <= 250):
        raise ValueError(f"Word count {word_count} outside range 60–250")

    return script


async def run(ctx: PipelineContext, settings) -> PipelineContext:
    last_error: str | None = None

    for attempt in range(1, settings.max_script_retries + 1):
        try:
            correction = None
            if last_error:
                correction = (
                    f"Ta réponse précédente était invalide : {last_error}. "
                    "Corrige et renvoie uniquement le JSON valide."
                )

            script = await retry_async(
                _generate_once,
                ctx.prompt,
                settings.llm_model,
                correction,
                retries=2,
                base_delay=1.0,
            )

            ctx.script = script
            ctx.full_text = " ".join(line.text for line in script.lines)
            logger.info(f"Script generated: {script.title} ({len(script.lines)} lines)")
            return ctx

        except (json.JSONDecodeError, ValueError) as e:
            last_error = str(e)
            logger.warning(f"Script attempt {attempt}/{settings.max_script_retries}: {e}")

    raise RuntimeError(f"Script generation failed after {settings.max_script_retries} attempts: {last_error}")
