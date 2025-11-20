"""LangChain helper utilities."""

from __future__ import annotations

from typing import Iterable, List

from langchain.schema import Document

from .models.audio import TranscriptSegment
from .models.vision import SlideTextBlock


def transcript_to_documents(segments: Iterable[TranscriptSegment]) -> List[Document]:
    docs: List[Document] = []
    for seg in segments:
        metadata = {"start": seg.start, "end": seg.end, "type": "transcript"}
        docs.append(Document(page_content=seg.text, metadata=metadata))
    return docs


def slides_to_documents(slides: Iterable[SlideTextBlock]) -> List[Document]:
    docs: List[Document] = []
    for slide in slides:
        text = slide.text
        if slide.caption:
            text += f"\n\n{slide.caption}"
        metadata = {
            "timestamp": slide.timestamp,
            "frame_path": str(slide.frame_path),
            "type": "slide",
        }
        docs.append(Document(page_content=text, metadata=metadata))
    return docs

