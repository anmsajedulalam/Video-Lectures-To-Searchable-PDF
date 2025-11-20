"""Whisper-based transcription."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from faster_whisper import WhisperModel
from rich.console import Console

from ..config import ModelConfig, Settings, resolve_settings

console = Console()


@dataclass
class TranscriptSegment:
    """Single transcript snippet with timestamps."""

    text: str
    start: float
    end: float


class WhisperTranscriber:
    """Wrapper around faster-whisper with GPU preference."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or resolve_settings()
        self.model_cfg: ModelConfig = self.settings.models
        console.log(
            f"[bold green]Loading Whisper model[/] {self.model_cfg.whisper_model} on {self.model_cfg.device}"
        )
        self.model = WhisperModel(
            self.model_cfg.whisper_model,
            device=self.model_cfg.device,
            compute_type="float16" if self.model_cfg.device == "cuda" else "int8",
        )

    def transcribe(self, audio_path: Path) -> List[TranscriptSegment]:
        segments, _ = self.model.transcribe(
            str(audio_path),
            language=self.model_cfg.whisper_language,
        )
        parsed: List[TranscriptSegment] = []
        for segment in segments:
            parsed.append(
                TranscriptSegment(
                    text=segment.text.strip(),
                    start=float(segment.start),
                    end=float(segment.end),
                )
            )
        return parsed


__all__ = ["WhisperTranscriber", "TranscriptSegment"]

