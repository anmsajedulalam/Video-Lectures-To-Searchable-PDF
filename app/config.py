"""Application configuration models."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class StoragePaths(BaseModel):
    """Resolved directory structure for the pipeline."""

    root: Path = Field(default_factory=lambda: Path.cwd())
    raw_dir: Path = Field(default_factory=lambda: Path.cwd() / "data" / "raw")
    processed_dir: Path = Field(default_factory=lambda: Path.cwd() / "data" / "processed")
    temp_dir: Path = Field(default_factory=lambda: Path.cwd() / "data" / "tmp")

    def ensure(self) -> None:
        """Create directories if they do not exist."""
        for target in (self.root, self.raw_dir, self.processed_dir, self.temp_dir):
            target.mkdir(parents=True, exist_ok=True)


class IngestRequest(BaseModel):
    """Request payload for ingestion."""

    source_type: Literal["local", "youtube", "gdrive"]
    source: str

    @field_validator("source")
    @classmethod
    def ensure_non_empty(cls, value: str) -> str:
        if not value.strip():
            msg = "source must be a path or URL"
            raise ValueError(msg)
        return value


class ExtractionConfig(BaseModel):
    """Controls FFmpeg extraction granularity."""

    frame_strategy: Literal["scene", "interval"] = "scene"
    frame_interval_seconds: float = 3.0
    scene_threshold: float = 0.4
    audio_sample_rate: int = 16000


class ModelConfig(BaseModel):
    """Model choices and parameters."""

    whisper_model: str = "medium"
    whisper_language: str | None = None
    vlm_model: str = "llava-hf/llava-1.5-7b-hf"
    ocr_lang: str = "en"
    device: str = "cuda"


class PdfConfig(BaseModel):
    """Rendering options for PDFs."""

    page_width: int = 1280
    page_height: int = 720
    margin: int = 24
    font_name: str = "Helvetica"
    font_size: int = 12


class Settings(BaseSettings):
    """Top-level settings loaded from env vars."""

    paths: StoragePaths = Field(default_factory=StoragePaths)
    extract: ExtractionConfig = Field(default_factory=ExtractionConfig)
    models: ModelConfig = Field(default_factory=ModelConfig)
    pdf: PdfConfig = Field(default_factory=PdfConfig)

    yt_downloader: str = "yt-dlp"
    ffmpeg_binary: str = "ffmpeg"

    youtube_cookie_file: Path | None = None
    google_service_account_json: Path | None = None

    class Config:
        env_nested_delimiter = "__"
        env_file = ".env"


def resolve_settings() -> Settings:
    """Helper to fetch settings with ensured directories."""
    settings = Settings()
    settings.paths.ensure()
    return settings

