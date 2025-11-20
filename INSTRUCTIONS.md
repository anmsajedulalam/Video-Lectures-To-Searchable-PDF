# Environment Setup Instructions

Follow these steps to prepare your machine to run the Video Lectures → Searchable PDFs pipeline.

## 1. Clone & Enter Project

```bash
git clone <repo-url> video-searchable-pdf
cd video-searchable-pdf
```

## 2. Choose Your Environment

### Option A — Conda (recommended for CUDA-enabled GPUs)

```bash
conda env create -f environment.yml
conda activate vlsp
```

Conda installs Python 3.10, CUDA 11.8 toolkit, PyTorch, and FFmpeg. Pip packages are automatically pulled from `environment.yml`.

### Option B — Virtualenv + pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Ensure system-level FFmpeg is available (`sudo apt install ffmpeg` on Ubuntu).

## 3. Hugging Face Credentials (optional but recommended)

```bash
huggingface-cli login
```

This unlocks gated checkpoints (e.g., LLaVA). Models will download when first used.

## 4. Verify GPU Access

```python
python - <<'PY'
import torch
print("CUDA available:", torch.cuda.is_available())
print("Device count:", torch.cuda.device_count())
PY
```

Expect `CUDA available: True` for an RTX 3060.

## 5. Install yt-dlp System Dependency (optional)

Although included in Python deps, you may prefer system install:

```bash
sudo wget -O /usr/local/bin/yt-dlp https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp
```

## 6. Create Required Directories

```bash
mkdir -p data/raw data/processed
```

The app auto-creates them, but this command ensures permissions are correct.

## 7. Smoke Test the CLI

```bash
vlsp run --type local --source /path/to/sample.mp4
```

Outputs will land under `data/processed/<video_id>/`.

## 8. Launch the API (optional)

```bash
uvicorn app.server:app --reload --port 8080
```

Send a POST to `/process` with JSON:

```json
{
  "source_type": "youtube",
  "source": "https://youtu.be/..."
}
```

## 9. Troubleshooting Tips

- **CUDA errors**: ensure the Conda env uses `cudatoolkit=11.8` and NVIDIA drivers ≥ 525.
- **Large model downloads**: expect 7–8 GB for LLaVA; ensure disk space and stable connection.
- **ffmpeg missing**: install via `conda install ffmpeg` (already done in Conda env) or system package manager.

Once these steps are complete, you are ready to process webinar videos into searchable PDFs.

