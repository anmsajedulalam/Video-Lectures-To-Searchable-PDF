"""Video ingestion utilities."""

from __future__ import annotations

import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from .config import IngestRequest, Settings, resolve_settings

console = Console()


@dataclass
class IngestResult:
    """Metadata describing an ingested asset."""

    video_id: str
    source: str
    source_type: str
    video_path: Path


class VideoIngestor:
    """Handle ingestion from various sources."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or resolve_settings()

    def ingest(self, req: IngestRequest) -> IngestResult:
        console.log(f"[bold green]Ingesting source[/]: {req.source_type} -> {req.source}")
        if req.source_type == "local":
            return self._copy_local(Path(req.source))
        if req.source_type == "youtube":
            return self._download_youtube(req.source)
        if req.source_type == "gdrive":
            return self._download_gdrive(req.source)
        msg = f"Unsupported source type {req.source_type}"
        raise ValueError(msg)

    # region helpers
    def _copy_local(self, src: Path) -> IngestResult:
        if not src.exists():
            msg = f"Local file not found: {src}"
            raise FileNotFoundError(msg)
        video_id = src.stem
        destination = self.settings.paths.raw_dir / video_id
        destination.mkdir(parents=True, exist_ok=True)
        target = destination / src.name
        shutil.copy2(src, target)
        return IngestResult(video_id, str(src), "local", target)

    def _download_youtube(self, url: str) -> IngestResult:
        video_id = uuid.uuid4().hex[:8]
        destination = self.settings.paths.raw_dir / video_id
        destination.mkdir(parents=True, exist_ok=True)

        output_template = str(destination / "%(title)s.%(ext)s")
        cmd = [
            self.settings.yt_downloader,
            url,
            "-o",
            output_template,
            "-f",
            "bestvideo+bestaudio/best",
            "--merge-output-format",
            "mp4",
        ]
        if self.settings.youtube_cookie_file:
            cmd += ["--cookies", str(self.settings.youtube_cookie_file)]

        console.log(f"[cyan]yt-dlp[/] {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        files = list(destination.glob("*.mp4"))
        if not files:
            msg = "Failed to download video via yt-dlp"
            raise RuntimeError(msg)
        return IngestResult(video_id, url, "youtube", files[0])

    def _download_gdrive(self, drive_url: str) -> IngestResult:
        try:
            from gdown import download as gdown_download
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "gdown not available; install extras or add gdown dependency."
            ) from exc

        video_id = uuid.uuid4().hex[:8]
        destination = self.settings.paths.raw_dir / video_id
        destination.mkdir(parents=True, exist_ok=True)
        output = destination / "drive_video.mp4"

        console.log(f"[cyan]gdown[/] downloading {drive_url}")
        gdown_download(url=drive_url, output=str(output), quiet=False, fuzzy=True)

        if not output.exists():
            msg = "Google Drive download failed"
            raise RuntimeError(msg)
        return IngestResult(video_id, drive_url, "gdrive", output)


__all__ = ["VideoIngestor", "IngestResult", "IngestRequest"]

