"""Tests for LLM JSON extraction and script validation."""

import json
import pytest

from backend.pipeline.steps.generate_script import _extract_json
from backend.pipeline.models import Script


# ── _extract_json ──────────────────────────────────────────────────────────

def test_extract_plain_json():
    raw = json.dumps({"title": "Test", "lines": [], "background_description": "x", "mood": "grumpy", "estimated_duration_seconds": 20})
    result = _extract_json(raw)
    assert result["title"] == "Test"


def test_extract_json_strips_markdown_fence():
    payload = {"title": "Titre", "lines": [], "background_description": "desc", "mood": "sarcastic", "estimated_duration_seconds": 15}
    raw = f"```json\n{json.dumps(payload)}\n```"
    result = _extract_json(raw)
    assert result["mood"] == "sarcastic"


def test_extract_json_strips_plain_fence():
    payload = {"title": "T", "lines": [], "background_description": "d", "mood": "proud", "estimated_duration_seconds": 10}
    raw = f"```\n{json.dumps(payload)}\n```"
    result = _extract_json(raw)
    assert result["mood"] == "proud"


def test_extract_json_finds_embedded_object():
    payload = {"title": "T", "lines": [], "background_description": "d", "mood": "furious", "estimated_duration_seconds": 12}
    raw = f"Voici le script :\n{json.dumps(payload)}\nBonne chance !"
    result = _extract_json(raw)
    assert result["title"] == "T"


def test_extract_json_raises_on_empty():
    with pytest.raises(json.JSONDecodeError):
        _extract_json("")


def test_extract_json_raises_on_no_object():
    with pytest.raises(json.JSONDecodeError):
        _extract_json("Désolé, je ne peux pas générer ce contenu.")


# ── Script model validation ────────────────────────────────────────────────

def _valid_script_data(**overrides):
    base = {
        "title": "L'argent c'est sacré",
        "lines": [{"text": "Mon coffre-fort !", "emotion": "proud"}],
        "background_description": "Coffre rempli de pièces d'or",
        "mood": "grumpy",
        "estimated_duration_seconds": 20,
    }
    base.update(overrides)
    return base


def test_script_model_valid():
    s = Script.model_validate(_valid_script_data())
    assert s.title == "L'argent c'est sacré"
    assert len(s.lines) == 1


def test_script_model_requires_lines():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Script.model_validate(_valid_script_data(lines=[]))


def test_script_model_duration_bounds():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Script.model_validate(_valid_script_data(estimated_duration_seconds=4))
    with pytest.raises(ValidationError):
        Script.model_validate(_valid_script_data(estimated_duration_seconds=61))


def test_script_line_default_emotion():
    s = Script.model_validate(_valid_script_data(lines=[{"text": "Bonjour"}]))
    assert s.lines[0].emotion == "neutral"
