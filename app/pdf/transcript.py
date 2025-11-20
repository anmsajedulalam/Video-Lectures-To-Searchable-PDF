"""Generate transcript-only searchable PDF."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from ..models.audio import TranscriptSegment


class TranscriptPdfBuilder:
    """Render transcript text grouped by timestamps."""

    def build(self, segments: Iterable[TranscriptSegment], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        for seg in segments:
            timestamp = f"[{seg.start:06.2f} - {seg.end:06.2f}]"
            story.append(Paragraph(f"<b>{timestamp}</b> {seg.text}", styles["BodyText"]))
            story.append(Spacer(1, 12))
        doc.build(story)
        return output_path

