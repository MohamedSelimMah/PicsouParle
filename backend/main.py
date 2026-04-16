"""Picsou Parle — API server."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.config import settings
from backend.pipeline.orchestrator import run_pipeline, get_run, start_run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(title="Picsou Parle", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATIC = Path(__file__).resolve().parent.parent / "static"


_ASSETS = Path(__file__).resolve().parent.parent / "assets"


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(_STATIC / "index.html")


@app.get("/assets/character/{filename}", include_in_schema=False)
async def character_asset(filename: str):
    safe = Path(filename).name  # prevent path traversal
    path = _ASSETS / "character" / safe
    if not path.exists() or not path.suffix == ".png":
        raise HTTPException(404)
    return FileResponse(path, media_type="image/png")


class GenerateRequest(BaseModel):
    prompt: str


class GenerateResponse(BaseModel):
    run_id: str


# SSE progress events
_progress_queues: dict[str, asyncio.Queue] = {}


def _on_progress(run_id: str, step: str) -> None:
    q = _progress_queues.get(run_id)
    if q:
        q.put_nowait({"step": step})


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(400, "Prompt is required")
    if len(prompt) > 500:
        raise HTTPException(400, "Prompt too long (max 500 chars)")

    q: asyncio.Queue = asyncio.Queue()
    run_id = start_run(prompt)
    _progress_queues[run_id] = q

    async def _run():
        try:
            await run_pipeline(run_id, on_progress=_on_progress)
        finally:
            _progress_queues.pop(run_id, None)

    asyncio.create_task(_run())
    return GenerateResponse(run_id=run_id)


@app.get("/api/runs/{run_id}/status")
async def run_status(run_id: str):
    ctx = get_run(run_id)
    if not ctx:
        raise HTTPException(404, "Run not found")
    return {
        "run_id": ctx.run_id,
        "status": ctx.status,
        "current_step": ctx.current_step,
        "error": ctx.error,
        "script": ctx.script.model_dump() if ctx.script else None,
        "audio_duration": ctx.audio_duration,
        "video_path": str(ctx.video_path) if ctx.video_path else None,
    }


@app.get("/api/runs/{run_id}/progress")
async def run_progress(run_id: str):
    ctx = get_run(run_id)
    if not ctx:
        raise HTTPException(404, "Run not found")

    q = _progress_queues.get(run_id)
    if not q:
        q = asyncio.Queue()
        _progress_queues[run_id] = q

    async def event_stream():
        # Send current state immediately
        yield {"event": "status", "data": ctx.status}

        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=30)
                yield {"event": "step", "data": msg["step"]}
                if msg["step"] == "done":
                    break
            except asyncio.TimeoutError:
                yield {"event": "ping", "data": ""}
                # Check if run is finished
                current = get_run(run_id)
                if current and current.status in ("completed", "failed"):
                    yield {"event": "status", "data": current.status}
                    break

    return EventSourceResponse(event_stream())


@app.get("/api/runs/{run_id}/video")
async def run_video(run_id: str):
    ctx = get_run(run_id)
    if not ctx or not ctx.video_path:
        raise HTTPException(404, "Video not found")
    path = Path(ctx.video_path)
    if not path.exists():
        raise HTTPException(404, "Video file missing")
    return FileResponse(path, media_type="video/mp4", filename=f"picsou_{run_id}.mp4")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


# Mount static files last so API routes take priority
if _STATIC.exists():
    app.mount("/", StaticFiles(directory=_STATIC, html=True), name="static")
