 # Video Lectures to Searchable PDFs

Pipeline for turning webinar-style videos into searchable lecture artifacts:

- OCR-driven slide PDF
- Whisper transcript PDF
- Slide-aligned combined PDF

## Requirements

- **Python**: 3.10+
- **System binaries**:
  - `ffmpeg` (for audio + frame extraction)
- **Hardware**:
  - CPU-only is supported (default will fall back to CPU).
  - GPU (CUDA) is recommended for faster Whisper + OCR if available.

On Ubuntu/Debian, install FFmpeg with:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
vlsp --help
```

## CLI Usage

```bash
vlsp run --type local --source /path/to/webinar.mp4
vlsp run --type youtube --source https://youtu.be/xxxx
vlsp run --type gdrive --source https://drive.google.com/file/d/ID/view
```

Outputs land in `data/processed/<video_id>/`.

## API Server

```bash
uvicorn app.server:app --reload --port 8080
```

POST payload:

```json
{
  "source_type": "youtube",
  "source": "https://youtu.be/... "
}
```

## Architecture Overview

```mermaid
flowchart LR
    subgraph Ingestion
        SRC[(Video Source)]
        SRC -->|local / youtube / gdrive| DL[Downloader]
    end

    DL --> FF[FFmpeg Extractor]
    FF -->|audio| WHISPER[faster-whisper]
    FF -->|frames| OCR[PaddleOCR (+ optional VLM captions)]

    WHISPER --> ALIGN[Slide/Text Aligner]
    OCR --> ALIGN

    ALIGN --> PDFGEN[ReportLab / PyPDF Builder]
    PDFGEN --> OUT[Searchable PDFs]

    OUT -->|persist| STORE[data/processed/<video_id>]
    ALIGN -->|serve| API[(FastAPI + Typer CLI)]
```

The CLI (`vlsp`) and FastAPI server share the same pipeline, so you can drive the workflow via command line, HTTP, or by importing the pipeline directly in Python.

## End-to-End Workflow

1. **Ingestion**: Video is pulled from the specified target (`local`, `youtube`, or `gdrive`). Metadata such as ID, title, and duration is captured for downstream file naming.
2. **Media Extraction**: FFmpeg splits the video into a high-quality WAV track and evenly spaced video frames with timestamps.
3. **Speech + Slide Text Understanding**:
   - `faster-whisper` produces bilingual-friendly transcripts and per-segment timestamps.
   - PaddleOCR extracts slide text from frames.
   - (Optional) A vision-language model (e.g. BLIP / LLaVA) can generate rich slide captions; this is **disabled by default** to keep VRAM usage modest.
4. **Alignment**: Transcript chunks are matched to their corresponding slide frames using temporal overlap and cosine similarity on embeddings.
5. **PDF Generation**:
   - **OCR-driven slide PDF** for crisp slide reproduction with searchable overlays.
   - **Whisper transcript PDF** containing time-linked dialogues.
   - **Combined PDF** merges slides and transcripts per page for study-ready notes.
6. **Delivery**: Artifacts are written to `data/processed/<video_id>/` and optionally surfaced via the FastAPI endpoint.

## Component Details

1. Multi-source ingestion (local path, YouTube URL, Google Drive URL)
2. Media extraction via FFmpeg (audio WAV + timestamped frames)
3. GPU-friendly AI models:
   - `faster-whisper` (configurable checkpoint)
   - PaddleOCR for slide OCR
   - Optional VLM (BLIP / LLaVA via 🤗 Transformers) for dense slide captions
4. PDF creation using ReportLab + PyPDF
5. Slide-by-slide synchronization with transcript blocks
6. FastAPI service & Typer CLI orchestrating the workflow

See `docs/models.md` for recommended checkpoints and VRAM needs.

## Configuration

All runtime settings are driven by a Pydantic `Settings` model and can be overridden via environment variables:

- **Model selection**:
  - `MODELS__whisper_model` – e.g. `small`, `medium`, `large-v3` (default: `medium`).
  - `MODELS__vlm_model` – set to a HF model id (e.g. `Salesforce/blip-image-captioning-base`) to enable captions,
    or `"none"` (default) to skip VLM entirely.
  - `MODELS__device` – `cuda` or `cpu` (default: `cuda`, will fall back to CPU if GPU is not available).
- **Storage paths**:
  - `PATHS__root` – project root (default: `cwd`).
  - `PATHS__raw_dir`, `PATHS__processed_dir`, `PATHS__temp_dir` – override data directories if needed.
- **Binaries**:
  - `FFMPEG_BINARY` – override the `ffmpeg` executable name/path if it is not on `PATH`.

By default the system runs with **VLM captions off**, uses `ffmpeg` from your `PATH`, and writes results under `data/processed/<video_id>/`.