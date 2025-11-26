"""Generate searchable slide PDFs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from PIL import Image
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from ..config import PdfConfig, Settings, resolve_settings
from ..models.vision import SlideTextBlock


@dataclass
class SlidePdfBuilder:
    """Create PDF with slide images and embedded OCR text."""

    # Use default_factory to avoid mutable default Settings instance at class definition time.
    settings: Settings = field(default_factory=resolve_settings)

    def build(self, blocks: Iterable[SlideTextBlock], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cfg: PdfConfig = self.settings.pdf
        page_size = (cfg.page_width, cfg.page_height)

        c = canvas.Canvas(str(output_path), pagesize=page_size)
        for block in blocks:
            self._draw_slide_page(c, block, page_size, cfg)
        c.save()
        return output_path

    def _draw_slide_page(self, c: canvas.Canvas, block: SlideTextBlock, page_size, cfg: PdfConfig) -> None:
        width, height = page_size
        c.setFont(cfg.font_name, cfg.font_size)
        c.drawString(cfg.margin, height - cfg.margin, f"Timestamp: {block.timestamp:.2f}s")

        img = Image.open(block.frame_path)
        img_width, img_height = img.size
        scale = min(
            (width - 2 * cfg.margin) / img_width,
            (height / 2) / img_height,
        )
        draw_width = img_width * scale
        draw_height = img_height * scale
        x = (width - draw_width) / 2
        y = (height - draw_height) - cfg.margin * 2
        c.drawInlineImage(str(block.frame_path), x, y, draw_width, draw_height)

        text_object = c.beginText(cfg.margin, cfg.margin * 2)
        body = block.text
        if block.caption:
            body += f"\n\n{block.caption}"
        for line in body.splitlines():
            text_object.textLine(line)
        c.drawText(text_object)
        c.showPage()

