# Picsou Parle

> Turn any topic into a vertical short video starring the richest duck in the world — for **$0.00 per video**.

Picsou Parle is a fully automated prompt-to-video pipeline that generates French-language short videos (1080×1920, YouTube Shorts / TikTok / Reels format) featuring Uncle Scrooge delivering opinionated monologues on any subject.

Type a topic → get a finished MP4 with:
- AI-generated script in Picsou's voice
- Natural French TTS with word-level timing
- Animated character with lip-sync
- Dynamic highlighted subtitles
- Preset-driven animated backgrounds + optional music

---

## Demo

```bash
python -m backend.cli --prompt "Pourquoi il ne faut jamais prêter d'argent à ses amis"
```

Output: a ~20–40s vertical MP4 in `output/`.

### Screenshots

| Prompt | Generating | Result |
|:---:|:---:|:---:|
| ![Main page](screenshots/main-page.png) | ![Generating](screenshots/generating.png) | ![Result](screenshots/results.png) |

### Example output

**Prompt:** *"Explique pourquoi il ne faut jamais prêter de l'argent à ses amis, avec un ton sarcastique et cynique, comme si un milliardaire donnait un conseil brutal."*

📥 [Download the generated video](screenshots/generated-test/picsou_189d594409f8.mp4)

---

## Architecture

```
 Prompt
   │
   ▼
 ┌──────────────────┐
 │  generate_script  │  LLM (OpenRouter, free models) → structured JSON
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  generate_voice   │  edge-tts → MP3 + WordBoundary timestamps
 └────────┬─────────┘
          ▼
 ┌──────────────────────┐
 │  generate_timestamps  │  Validate & normalize word timing
 └────────┬─────────────┘
          ▼
 ┌──────────────────┐
 │  prepare_visuals  │  Preset background render/cache + character assets + audio amplitudes
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  build_subtitles  │  Group words → subtitle blocks (≤5 words, ≤2.5s)
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  compose_video    │  Frame-by-frame render → FFmpeg H.264/AAC MP4
 └──────────────────┘
```

Each step receives and returns a `PipelineContext` dataclass — no globals inside the pipeline itself. The current run registry is in memory, so `--from-step` is a developer-oriented hook, not a persisted resume mechanism across fresh CLI invocations.

---

## Features

| Feature | Details |
|---|---|
| **Script generation** | LLM via OpenRouter with structured JSON output and a bundled fallback chain |
| **Voice synthesis** | edge-tts (Microsoft Neural TTS) — free, no API key |
| **Word timing** | Native `WordBoundary` timestamps from edge-tts |
| **Lip-sync animation** | Adaptive RMS threshold, open/closed mouth states at 30fps |
| **Dynamic subtitles** | Word-level highlight with auto line-wrapping |
| **Background presets** | `luxury_car` and `seaside`, exposed in the CLI, API, and web UI |
| **Background rendering** | Animated preset scenes, cached in `assets/cache/`, with OpenRouter image generation when a key is available |
| **Background music** | Auto-mixed at low volume from `assets/music/` |
| **Web UI** | Single-file frontend with SSE real-time progress and background selection |
| **Auto-retry** | Exponential backoff + model fallback on rate limits |

---

## Prerequisites

- **Python** ≥ 3.11
- **FFmpeg** ≥ 4.x in PATH
- **OpenRouter API key** (free tier works)

```bash
# Ubuntu/Debian
sudo apt install -y ffmpeg

# Verify
ffmpeg -version
```

---

## Installation

```bash
git clone <repo-url> && cd picsou-parle

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` from the example:

```bash
cp .env.example .env
# Edit .env and add your OpenRouter key
```

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENROUTER_API_KEY` | Yes | — | OpenRouter API key |
| `LLM_MODEL` | No | `google/gemma-4-26b-a4b-it:free` | Primary LLM model |
| `TTS_VOICE` | No | `fr-FR-HenriNeural` | edge-tts voice ID |
| `IMAGE_MODEL` | No | `black-forest-labs/FLUX.1-schnell:free` | Image generation model |
| `VIDEO_FPS` | No | `30` | Output video framerate |
| `MUSIC_VOLUME` | No | `0.12` | Background music mix level |
| `KEEP_TEMP` | No | `false` | Keep intermediate files |

Background presets currently try OpenRouter image generation automatically when `OPENROUTER_API_KEY` is available, then fall back to built-in renders and cache the result in `assets/cache/`.

---

## Usage

### CLI

```bash
# Basic generation
python -m backend.cli --prompt "Les crypto-monnaies sont une arnaque"

# Choose the visual universe
python -m backend.cli --prompt "..." --background seaside

# Keep intermediates and enable verbose logging
python -m backend.cli --prompt "..." --keep-temp --verbose

# Custom voice and model
python -m backend.cli --prompt "..." --voice fr-FR-HenriNeural --model google/gemma-4-26b-a4b-it:free
```

Valid background modes are currently `luxury_car` and `seaside`.

`--from-step` is exposed in the CLI, but it does not restore a previous run from disk on its own. It is only useful when the in-memory `PipelineContext` has already been populated by the current process.

### Web UI

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://127.0.0.1:8000** (or `http://localhost:8000`) — the UI shows real-time progress with step-by-step tracking, animated character, and gold confetti on completion.

The web UI exposes the same two background presets as the CLI and sends them as `background_mode` in the generation request.

> **Note:** If `localhost` doesn't work, use `127.0.0.1` directly. Some Linux systems resolve `localhost` to IPv6 `::1` which may not match the server binding.

### API

```bash
curl -X POST http://127.0.0.1:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Pourquoi les riches deviennent parano", "background_mode": "seaside"}'
```

`background_mode` currently accepts `luxury_car` or `seaside`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/generate` | Start generation (`{"prompt": "...", "background_mode": "luxury_car"}`) |
| `GET` | `/api/runs/{id}/status` | Run status + script metadata |
| `GET` | `/api/runs/{id}/progress` | SSE stream of step updates |
| `GET` | `/api/runs/{id}/video` | Download finished MP4 |

---

## Project Structure

```
backend/
├── cli.py                          # CLI entry point
├── main.py                         # FastAPI server + SSE
├── config.py                       # pydantic-settings configuration
├── presets.py                      # Background preset definitions
├── pipeline/
│   ├── orchestrator.py             # Step sequencing & run state
│   ├── context.py                  # PipelineContext dataclass
│   ├── models.py                   # Script, TimestampedWord, SubtitleGroup
│   └── steps/                      # One module per pipeline step
│       ├── generate_script.py
│       ├── generate_voice.py
│       ├── generate_timestamps.py
│       ├── prepare_visuals.py
│       ├── build_subtitles.py
│       └── compose_video.py
├── providers/
│   ├── llm.py                      # OpenRouter client + fallback chain
│   ├── tts.py                      # edge-tts wrapper
│   └── image.py                    # AI background generation
└── utils/
    ├── audio.py                    # RMS amplitude extraction
  ├── backgrounds.py              # Animated preset background renderers
    ├── fonts.py                    # Font discovery
    ├── rendering.py                # Frame rendering (Ken Burns, subtitles)
    └── retry.py                    # Async retry with backoff

static/index.html                   # Web UI (single-file)
scripts/generate_character.py       # SVG→PNG character asset generator
prompts/picsou_script.txt           # System prompt for script generation
assets/
├── character/                      # Mouth open/closed PNGs
├── fonts/                          # Optional: Montserrat-Bold.ttf
├── backgrounds/                    # Optional: static backgrounds
├── cache/                          # Auto-cached preset backgrounds by mode
└── music/                          # Optional: background music file
tests/                              # 26 unit tests
output/                             # Generated MP4 files
tmp/                                # Intermediate pipeline files
```

---

## Character Assets

The character is rendered as SVG and rasterized to PNG via `cairosvg`:

```bash
python scripts/generate_character.py
# → assets/character/picsou_mouth_closed.png
# → assets/character/picsou_mouth_open.png
```

The SVG uses bezier curves, radial gradients, drop shadows, and detailed vector paths for a clean 2D cartoon look.

---

## Testing

```bash
# Unit tests (26 tests)
pytest tests/ -v

# Full end-to-end pipeline test
python test_pipeline.py
```

Tests cover: JSON parsing edge cases, subtitle grouping logic, audio threshold computation, and async retry behavior.

---

## Cost

| Component | Provider | Cost |
|---|---|---|
| Script | OpenRouter (free models) | $0.00 |
| Voice | edge-tts | $0.00 |
| Timestamps | edge-tts native | $0.00 |
| Background | Pillow gradient / FLUX.1 free | $0.00 |
| Composition | FFmpeg local | $0.00 |
| **Total** | | **$0.00 / video** |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `OPENROUTER_API_KEY is not set` | Add key to `.env` and restart |
| `ffmpeg: command not found` | Install FFmpeg: `sudo apt install ffmpeg` |
| No character in video | Check `assets/character/picsou_mouth_closed.png` exists |
| Subtitle font looks basic | Add `assets/fonts/Montserrat-Bold.ttf` |
| Invalid `background_mode` | Use `luxury_car` or `seaside` |
| `--from-step` doesn't resume an old CLI run | Current run state is in memory only; rerun from the start or wire resume to an existing context |
| 429 rate limit errors | Automatic — falls back through the bundled model chain |
| Subtitles cut off | Handled — auto line-wrapping at 52px font size |
