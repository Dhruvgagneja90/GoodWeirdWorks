"""Offline preflight checks for supplied source media (stdlib only)."""
from __future__ import annotations

import struct
import wave
from pathlib import Path


def png_size(path: Path) -> tuple[int, int] | None:
    """Read PNG header dimensions without decoding image content."""
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
        if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            return None
        width, height = struct.unpack(">II", header[16:24])
        return (width, height) if width and height else None
    except OSError:
        return None


def wav_seconds(path: Path) -> float | None:
    """Return duration of uncompressed PCM WAV; other formats are not probed."""
    try:
        with wave.open(str(path), "rb") as handle:
            rate = handle.getframerate()
            return handle.getnframes() / rate if rate else None
    except (OSError, EOFError, wave.Error):
        return None


def audit_media(manifest_path: Path, rows: list[dict], *,
                target_width: int = 1920, target_height: int = 1080) -> list[dict]:
    root = manifest_path.resolve().parent
    found: list[dict] = []
    already_used: dict[str, str] = {}
    target_ratio = target_width / target_height
    for row in rows:
        sid = row["id"]
        image_name = row["image"]
        if image_name in already_used:
            found.append({"level": "warning", "code": "reused_image",
                          "detail": f"{sid}: reuses image from {already_used[image_name]} ({image_name})"})
        already_used[image_name] = sid
        image = root / image_name
        if image.is_file() and image.suffix.lower() == ".png":
            dimensions = png_size(image)
            if dimensions is None:
                found.append({"level": "warning", "code": "png_unreadable",
                              "detail": f"{sid}: cannot read PNG header: {image_name}"})
            else:
                w, h = dimensions
                if w < target_width * .5 or h < target_height * .5:
                    found.append({"level": "warning", "code": "low_resolution",
                                  "detail": f"{sid}: {w}x{h} image is much smaller than {target_width}x{target_height}"})
                if abs(w / h - target_ratio) > .08:
                    found.append({"level": "warning", "code": "aspect_ratio",
                                  "detail": f"{sid}: {w}x{h} may need cropping or letterboxing"})
        audio_name = row.get("audio", "")
        if audio_name:
            audio = root / audio_name
            if audio.is_file() and audio.suffix.lower() == ".wav":
                observed = wav_seconds(audio)
                if observed is None:
                    found.append({"level": "warning", "code": "wav_unreadable",
                                  "detail": f"{sid}: cannot inspect WAV: {audio_name}"})
                elif abs(observed - row["duration_sec"]) > 1:
                    found.append({"level": "warning", "code": "audio_mismatch",
                                  "detail": f"{sid}: audio is {observed:.1f}s but scene is {row['duration_sec']:.1f}s"})
    return found
