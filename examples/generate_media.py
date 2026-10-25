"""Create tiny synthetic example media (no third-party images or packages)."""
from __future__ import annotations

import struct
import wave
import zlib
from pathlib import Path


def png(path: Path, width: int, height: int, color: tuple[int, int, int]) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    scanline = b"\x00" + bytes(color) * width
    pixels = zlib.compress(scanline * height)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", pixels) + chunk(b"IEND", b""))


def generate(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name, shade in (("intro", (27, 35, 49)), ("evidence", (73, 82, 98)), ("reveal", (33, 76, 79))):
        png(destination / (name + ".png"), 640, 360, shade)
    with wave.open(str(destination / "silence.wav"), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\x00\x00" * 16000)


if __name__ == "__main__":
    generate(Path(__file__).resolve().parent / "demo_assets")
    print("Generated three synthetic PNGs and one 1-second silent WAV.")
