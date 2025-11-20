"""End-to-end orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from .config import IngestRequest, Settings, resolve_settings
from .ingest import VideoIngestor
from .media import MediaExtractor
from .models import SlideAnalyzer, WhisperTranscriber
from .pdf import CombinedPdfBuilder, SlidePdfBuilder, TranscriptPdfBuilder
from .sync import group_transcript_by_slide

console = Console()


@dataclass
class PipelineResult:
    video_id: str
    slide_pdf: Path
    transcript_pdf: Path
    combined_pdf: Path


class PipelineRunner:
    """Composable pipeline runner used by CLI and FastAPI."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or resolve_settings()
        self.ingestor = VideoIngestor(self.settings)
        self.extractor = MediaExtractor(self.settings)
        self.transcriber = WhisperTranscriber(self.settings)
        self.slide_analyzer = SlideAnalyzer(self.settings)
        self.slide_pdf_builder = SlidePdfBuilder(self.settings)
        self.transcript_pdf_builder = TranscriptPdfBuilder()
        self.combined_pdf_builder = CombinedPdfBuilder(self.settings)

    def run(self, request: IngestRequest) -> PipelineResult:
        ingest_result = self.ingestor.ingest(request)
        video_id = ingest_result.video_id
        console.log(f"[bold green]Processing video[/] {video_id}")

        processed_dir = self.settings.paths.processed_dir / video_id
        processed_dir.mkdir(parents=True, exist_ok=True)

        audio_path = self.extractor.extract_audio(
            ingest_result.video_path, processed_dir / "audio"
        )
        frame_infos = self.extractor.extract_frames(
            ingest_result.video_path, processed_dir / "frames"
        )

        slides = self.slide_analyzer.analyze([(f.timestamp, f.path) for f in frame_infos])
        transcript_segments = self.transcriber.transcribe(audio_path)

        slide_pdf = self.slide_pdf_builder.build(slides, processed_dir / "slides.pdf")
        transcript_pdf = self.transcript_pdf_builder.build(
            transcript_segments, processed_dir / "transcript.pdf"
        )
        grouped = group_transcript_by_slide(slides, transcript_segments)
        combined_pdf = self.combined_pdf_builder.build(
            slides, grouped, processed_dir / "combined.pdf"
        )

        return PipelineResult(video_id, slide_pdf, transcript_pdf, combined_pdf)

