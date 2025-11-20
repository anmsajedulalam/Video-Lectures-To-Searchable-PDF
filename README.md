 # Video Lectures to Searchable PDFs

Pipeline for turning webinar-style videos into searchable lecture artifacts:

- OCR-driven slide PDF
- Whisper transcript PDF
- Slide-aligned combined PDF

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

## Components

1. Multi-source ingestion (local path, YouTube URL, Google Drive URL)
2. Media extraction via FFmpeg (audio WAV + timestamped frames)
3. GPU-friendly AI models:
   - `faster-whisper` (Whisper Large V3)
   - PaddleOCR + LLaVA (via 🤗 Transformers) for slide text
4. PDF creation using ReportLab + PyPDF
5. Slide-by-slide synchronization with transcript blocks
6. FastAPI service & Typer CLI orchestrating the workflow

See `docs/models.md` for recommended checkpoints and VRAM needs.

