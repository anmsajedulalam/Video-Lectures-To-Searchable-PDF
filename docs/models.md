 # Recommended Models & GPU Notes

## Audio

- **Whisper Large-V3** via [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper)
  - VRAM: ~6 GB (float16); fits RTX 3060 8 GB.
  - Pros: strong multilingual accuracy, timestamped segments.

## Slides

| Purpose | Model | Notes |
| --- | --- | --- |
| OCR backbone | `PaddleOCR` (PP-OCRv4) | Great accuracy on slide fonts, GPU optional. |
| VLM captions | `llava-hf/llava-1.5-13b-hf` | Requires ~7 GB VRAM; use 7B if memory constrained. |
| Optional cleanup | `microsoft/layoutlmv3-base` | Useful for structured text post-processing. |

## Pipelines

1. Extract frames via FFmpeg (scene detection).
2. PaddleOCR -> base text.
3. LLaVA -> semantic summary & key bullets.
4. Combine text + captions, deduplicate via cosine similarity.

## Alternatives

- **Slides-only**: use `Nougat` (pdf2markup) if the deck is available separately.
- **Audio**: `distil-whisper` for CPU-only deployment.

All checkpoints are available on Hugging Face Hub. Use `huggingface-cli download` to cache offline.

