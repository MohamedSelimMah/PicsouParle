"""Tests for subtitle grouping logic."""

import pytest

from backend.pipeline.models import TimestampedWord
from backend.pipeline.steps.build_subtitles import _group_words, MAX_WORDS_PER_GROUP, MAX_DURATION_PER_GROUP


def _words(texts: list[str], start: float = 0.0, gap: float = 0.3, duration: float = 0.25) -> list[TimestampedWord]:
    """Build a list of TimestampedWord with evenly spaced timing."""
    result = []
    t = start
    for text in texts:
        result.append(TimestampedWord(word=text, start=t, end=t + duration))
        t += duration + gap
    return result


def test_empty_words_returns_empty():
    assert _group_words([]) == []


def test_single_word_becomes_one_group():
    groups = _group_words(_words(["Bonjour"]))
    assert len(groups) == 1
    assert groups[0].text == "Bonjour"


def test_splits_at_max_words():
    # 6 words → should produce at least 2 groups (max 5 per group)
    words = _words(["a", "b", "c", "d", "e", "f"])
    groups = _group_words(words)
    assert all(len(g.words) <= MAX_WORDS_PER_GROUP for g in groups)
    assert len(groups) >= 2


def test_all_words_present():
    texts = ["Mon", "coffre-fort", "est", "sacré", "rapiat"]
    words = _words(texts)
    groups = _group_words(words)
    recovered = " ".join(g.text for g in groups)
    assert all(t in recovered for t in texts)


def test_group_timing():
    words = _words(["a", "b", "c"])
    groups = _group_words(words)
    assert groups[0].start == words[0].start
    assert groups[-1].end == words[-1].end


def test_splits_on_long_duration():
    # Words with large gaps — the grouper should produce multiple groups
    long_words = _words(["a", "b", "c", "d"], gap=1.2, duration=1.4)
    groups = _group_words(long_words)
    # Should split into more than one group given large durations
    assert len(groups) > 1
    # No group should have more words than the max
    for g in groups:
        assert len(g.words) <= MAX_WORDS_PER_GROUP


def test_group_text_matches_words():
    words = _words(["Picsou", "est", "riche"])
    groups = _group_words(words)
    for g in groups:
        expected = " ".join(w.word for w in g.words)
        assert g.text == expected
