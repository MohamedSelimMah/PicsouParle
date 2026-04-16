from __future__ import annotations

from pydantic import BaseModel, Field


class ScriptLine(BaseModel):
    text: str
    emotion: str = "neutral"


class Script(BaseModel):
    title: str
    lines: list[ScriptLine] = Field(min_length=1)
    background_description: str
    mood: str
    estimated_duration_seconds: float = Field(ge=5, le=60)


class TimestampedWord(BaseModel):
    word: str
    start: float  # seconds
    end: float


class SubtitleGroup(BaseModel):
    text: str
    words: list[TimestampedWord]
    start: float
    end: float


class PipelineResult(BaseModel):
    run_id: str
    prompt: str
    script: Script | None = None
    audio_path: str | None = None
    audio_duration: float | None = None
    timestamps: list[TimestampedWord] = []
    subtitle_groups: list[SubtitleGroup] = []
    video_path: str | None = None
    status: str = "pending"
    error: str | None = None
