"""Slide-by-slide combined PDF."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List

from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas

from ..config import PdfConfig, Settings, resolve_settings
from ..models.audio import TranscriptSegment
from ..models.vision import SlideTextBlock


@dataclass
class CombinedPdfBuilder:
    """Place slide image next to synchronized transcript paragraphs."""

    # Use default_factory to avoid mutable default Settings instance at class definition time.
    settings: Settings = field(default_factory=resolve_settings)

    def build(
        self,
        slides: Iterable[SlideTextBlock],
        grouped_transcript: dict[str, List[TranscriptSegment]],
        output_path: Path,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cfg: PdfConfig = self.settings.pdf
        page_size = (cfg.page_width, cfg.page_height)
        c = canvas.Canvas(str(output_path), pagesize=page_size)
        for block in slides:
            bucket = grouped_transcript.get(str(block.frame_path), [])
            self._draw_page(c, block, bucket, cfg, page_size)
        c.save()
        return output_path

    def _draw_page(
        self,
        c: canvas.Canvas,
        slide: SlideTextBlock,
        transcript_segments: List[TranscriptSegment],
        cfg: PdfConfig,
        page_size,
    ) -> None:
        width, height = page_size
        half = width / 2
        image_width = half - 2 * cfg.margin
        image_height = height - 2 * cfg.margin
        c.drawImage(
            str(slide.frame_path),
            cfg.margin,
            cfg.margin,
            image_width,
            image_height,
            preserveAspectRatio=True,
            anchor="sw",
        )
        text_x = half + cfg.margin
        text_y = height - cfg.margin
        c.setFont(cfg.font_name, cfg.font_size)
        c.drawString(text_x, text_y, f"Slide @ {slide.timestamp:.2f}s")
        text_object = c.beginText(text_x, text_y - cfg.margin)
        for seg in transcript_segments:
            text_object.textLine(f"[{seg.start:.1f}-{seg.end:.1f}] {seg.text}")
        if not transcript_segments:
            text_object.textLine("(No transcript aligned)")
        c.drawText(text_object)
        c.showPage()

