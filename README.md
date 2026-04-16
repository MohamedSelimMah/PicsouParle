# Picsou Parle

Prompt-to-video generator that creates short vertical MP4 videos in the style of social Shorts/Reels:

- Script generation (LLM via OpenRouter)
- French voice generation (edge-tts)
- Word-level timestamps
- Character mouth animation (open/closed states from audio amplitude)
- Dynamic highlighted subtitles
- Final composition with FFmpeg

Output videos are written to `output/`.

## Features

- End-to-end pipeline from a single text prompt
- French-first content and voice defaults
- Automatic retry and fallback model behavior for LLM calls
- CLI mode for quick local generation
- FastAPI mode for web/app integration (with SSE progress endpoint)
- Optional background music mixing (drop a file into `assets/music/`)

## Tech Stack

- Python 3
- FastAPI + Uvicorn
- OpenRouter (OpenAI-compatible SDK)
- edge-tts
- Pillow
- FFmpeg

## Project Layout

```text
backend/
	cli.py                    # CLI entry point
	main.py                   # FastAPI app
	config.py                 # Settings from env/.env
	pipeline/
		orchestrator.py         # Step orchestration + run state
		steps/
			generate_script.py
			generate_voice.py
			generate_timestamps.py
			prepare_visuals.py
			build_subtitles.py
			compose_video.py
assets/
	character/
		picsou_mouth_closed.png
		picsou_mouth_open.png
output/                     # Final MP4 files
tmp/                        # Intermediate files
prompts/
	picsou_script.txt
```

## Prerequisites

1. Python 3.10+
2. FFmpeg installed and available in PATH
3. OpenRouter API key

Install FFmpeg on Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y ffmpeg
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

Create a `.env` file at repository root:

```env
OPENROUTER_API_KEY=your_openrouter_key

# Optional
LLM_MODEL=google/gemma-4-26b-a4b-it:free
TTS_VOICE=fr-FR-HenriNeural
VIDEO_FPS=30
KEEP_TEMP=false
MUSIC_VOLUME=0.12
```

Notes:

- `OPENROUTER_API_KEY` is required for script generation.
- `edge-tts` does not require an API key.

## Quick Start (CLI)

Generate a video from a prompt:

```bash
python -m backend.cli --prompt "Pourquoi il ne faut jamais preter d'argent a ses amis"
```

Useful flags:

```bash
python -m backend.cli --prompt "..." --verbose
python -m backend.cli --prompt "..." --keep-temp
python -m backend.cli --prompt "..." --voice fr-FR-HenriNeural
python -m backend.cli --prompt "..." --model google/gemma-4-31b-it:free
python -m backend.cli --prompt "..." --from-step compose_video
```

## Run as API

Start server:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints:

- `POST /api/generate` with body `{ "prompt": "..." }`
- `GET /api/runs/{run_id}/status`
- `GET /api/runs/{run_id}/progress` (SSE)
- `GET /api/runs/{run_id}/video`

Example:

```bash
curl -X POST http://localhost:8000/api/generate \
	-H "Content-Type: application/json" \
	-d '{"prompt":"Explique pourquoi la radinerie est une strategie"}'
```

## Pipeline Steps

1. `generate_script` — LLM generates structured Picsou monologue JSON
2. `generate_voice` — edge-tts synthesizes MP3 + word boundaries
3. `generate_timestamps` — validates/normalizes timing data
4. `prepare_visuals` — builds gradient background and loads character states
5. `build_subtitles` — builds dynamic subtitle groups
6. `compose_video` — frame rendering + FFmpeg muxing to MP4

## Assets

Character assets expected by default:

- `assets/character/picsou_mouth_closed.png`
- `assets/character/picsou_mouth_open.png`

If `picsou_mouth_open.png` is missing, the closed image is reused.

Optional background music:

- Place one file in `assets/music/` (`.mp3`, `.wav`, `.ogg`, `.m4a`)

## Testing

Run tests:

```bash
pytest -q
```

Or run the quick end-to-end script:

```bash
python test_pipeline.py
```

## Troubleshooting

- `OPENROUTER_API_KEY is not set`
	- Add the key in `.env` and restart your shell/server.

- `ffmpeg: command not found`
	- Install FFmpeg and verify with `ffmpeg -version`.

- No character visible in output
	- Check `assets/character/picsou_mouth_closed.png` exists.

- Subtitle font looks basic
	- Add a bold font at `assets/fonts/Montserrat-Bold.ttf`.

## Related Docs

- `SUJET.md`
- `ARCHITECTURE.md`
- `EVALUATION.md`
- `CLAUDE_MD_GUIDE.md`
