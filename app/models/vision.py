"""Slide OCR + VLM descriptions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from paddleocr import PaddleOCR
from PIL import Image
from rich.console import Console
from transformers import AutoProcessor, AutoTokenizer, LlavaForConditionalGeneration

from ..config import ModelConfig, Settings, resolve_settings

console = Console()


@dataclass
class SlideTextBlock:
    """Text extracted from a slide frame."""

    frame_path: Path
    timestamp: float
    text: str
    caption: str | None = None


class SlideAnalyzer:
    """Combine OCR (PaddleOCR) with LLaVA captions for richer context."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or resolve_settings()
        cfg: ModelConfig = self.settings.models

        console.log("[bold green]Loading PaddleOCR[/]")
        self.ocr = PaddleOCR(lang=cfg.ocr_lang, use_gpu=cfg.device == "cuda", show_log=False)

        if cfg.vlm_model.lower() != "none":
            console.log(f"[bold green]Loading VLM[/] {cfg.vlm_model}")
            self.processor = AutoProcessor.from_pretrained(cfg.vlm_model)
            self.tokenizer = AutoTokenizer.from_pretrained(cfg.vlm_model)
            self.model = LlavaForConditionalGeneration.from_pretrained(
                cfg.vlm_model, device_map="auto"
            )
        else:
            console.log("[yellow]Skipping VLM captions (vlm_model=none)[/]")
            self.processor = None
            self.tokenizer = None
            self.model = None

    def analyze(self, frames: List[tuple[float, Path]]) -> List[SlideTextBlock]:
        blocks: List[SlideTextBlock] = []
        for timestamp, frame_path in frames:
            text = self._ocr_frame(frame_path)
            caption = self._caption_frame(frame_path) if self.model else None
            merged_text = "\n".join(filter(None, [text, caption or ""])).strip()
            if not merged_text:
                continue
            blocks.append(
                SlideTextBlock(
                    frame_path=frame_path,
                    timestamp=timestamp,
                    text=text,
                    caption=caption,
                )
            )
        return blocks

    def _ocr_frame(self, frame_path: Path) -> str:
        result = self.ocr.ocr(str(frame_path), cls=True)
        lines: List[str] = []
        for line in result:
            for _, (text, score) in line:
                if score > 0.7:
                    lines.append(text)
        return "\n".join(lines)

    def _caption_frame(self, frame_path: Path) -> str | None:
        if not self.model or not self.processor or not self.tokenizer:
            return None
        image = Image.open(frame_path).convert("RGB")
        prompt = "Describe the lecture slide content thoroughly for study notes:"
        inputs = self.processor(prompt, image, return_tensors="pt").to(self.model.device)
        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=128,
            do_sample=False,
        )
        caption = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
        return caption[0].strip() if caption else None


__all__ = ["SlideAnalyzer", "SlideTextBlock"]

