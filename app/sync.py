"""Utilities to align transcript segments with slide frames."""

from __future__ import annotations

from bisect import bisect_right
from typing import Dict, List, Sequence

from .models.audio import TranscriptSegment
from .models.vision import SlideTextBlock


def group_transcript_by_slide(
    slides: Sequence[SlideTextBlock],
    transcript: Sequence[TranscriptSegment],
) -> Dict[str, List[TranscriptSegment]]:
    """Assign transcript segments to the slide active at their midpoint."""

    if not slides:
        return {}

    slide_times = [slide.timestamp for slide in slides]
    buckets: Dict[str, List[TranscriptSegment]] = {
        str(slide.frame_path): [] for slide in slides
    }

    for segment in transcript:
        midpoint = (segment.start + segment.end) / 2
        idx = bisect_right(slide_times, midpoint) - 1
        idx = max(0, min(idx, len(slides) - 1))
        key = str(slides[idx].frame_path)
        buckets.setdefault(key, []).append(segment)
    return buckets

