"""Audio and frame extraction utilities."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import cv2
import numpy as np
from rich.progress import track

from .config import ExtractionConfig, Settings, resolve_settings


@dataclass
class FrameInfo:
    """Metadata for an extracted frame."""

    index: int
    timestamp: float
    path: Path


class MediaExtractor:
    """Coordinates audio extraction and frame sampling."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or resolve_settings()
        self.extract_cfg: ExtractionConfig = self.settings.extract

    def extract_audio(self, video: Path, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / "audio.wav"
        cmd = [
            self.settings.ffmpeg_binary,
            "-i",
            str(video),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            str(self.extract_cfg.audio_sample_rate),
            "-ac",
            "1",
            str(audio_path),
        ]
        subprocess.run(cmd, check=True)
        return audio_path

    def extract_frames(self, video: Path, output_dir: Path) -> List[FrameInfo]:
        output_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = output_dir / "frames.json"

        if self.extract_cfg.frame_strategy == "interval":
            return self._extract_interval(video, output_dir, metadata_path)
        return self._extract_scene(video, output_dir, metadata_path)

    # region strategies
    def _extract_interval(self, video: Path, out_dir: Path, meta_path: Path) -> List[FrameInfo]:
        cap = cv2.VideoCapture(str(video))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        interval_frames = int(self.extract_cfg.frame_interval_seconds * fps)
        frame_infos: List[FrameInfo] = []
        idx = 0
        saved = 0
        while True:
            success, frame = cap.read()
            if not success:
                break
            if idx % max(interval_frames, 1) == 0:
                timestamp = idx / fps
                path = out_dir / f"frame_{saved:05d}.jpg"
                cv2.imwrite(str(path), frame)
                frame_infos.append(FrameInfo(saved, float(timestamp), path))
                saved += 1
            idx += 1
        cap.release()
        self._write_metadata(meta_path, frame_infos)
        return frame_infos

    def _extract_scene(self, video: Path, out_dir: Path, meta_path: Path) -> List[FrameInfo]:
        # Use ffmpeg scene detection filtering
        scene_dir = out_dir / "scene_frames"
        scene_dir.mkdir(parents=True, exist_ok=True)
        scene_pattern = str(scene_dir / "scene_%04d.jpg")
        cmd = [
            self.settings.ffmpeg_binary,
            "-i",
            str(video),
            "-vf",
            f"select='gt(scene,{self.extract_cfg.scene_threshold})',showinfo",
            "-vsync",
            "vfr",
            scene_pattern,
        ]
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        frame_infos = self._parse_scene_log(process.stderr, scene_dir)
        self._write_metadata(meta_path, frame_infos)
        return frame_infos

    # endregion
    def _parse_scene_log(self, stderr: str, frame_dir: Path) -> List[FrameInfo]:
        frame_infos: List[FrameInfo] = []
        for idx, line in enumerate(stderr.splitlines()):
            if "pts_time" not in line:
                continue
            parts = [p for p in line.split(" ") if "pts_time" in p]
            if not parts:
                continue
            timestamp = float(parts[0].split(":")[1])
            frame_path = frame_dir / f"scene_{idx:04d}.jpg"
            if frame_path.exists():
                frame_infos.append(FrameInfo(idx, timestamp, frame_path))
        return frame_infos

    @staticmethod
    def _write_metadata(path: Path, frames: Iterable[FrameInfo]) -> None:
        serializable = [
            {"index": f.index, "timestamp": f.timestamp, "path": str(f.path)} for f in frames
        ]
        path.write_text(json.dumps(serializable, indent=2))


__all__ = ["MediaExtractor", "FrameInfo"]

