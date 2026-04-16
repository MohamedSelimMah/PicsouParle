from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # OpenRouter — single key for all LLM calls
    openrouter_api_key: str = ""
    llm_model: str = "google/gemma-4-26b-a4b-it:free"

    # TTS — edge-tts is free, no key needed
    tts_voice: str = "fr-FR-HenriNeural"

    # Paths
    output_dir: Path = Path("output")
    tmp_dir: Path = Path("tmp")
    assets_dir: Path = Path("assets")

    # Pipeline
    max_script_retries: int = 3
    video_fps: int = 30
    keep_temp: bool = False

    # AI background generation (optional — uses OpenRouter image API)
    ai_background: bool = False
    image_model: str = "black-forest-labs/FLUX.1-schnell:free"

    # Background music (optional — place an mp3 in assets/music/)
    music_volume: float = 0.12

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def ensure_dirs(self) -> None:
        for d in [self.output_dir, self.tmp_dir]:
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
