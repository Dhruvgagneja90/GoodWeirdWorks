"""Optional local FFmpeg video assembly. No shell commands or cloud calls."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


class RenderError(RuntimeError):
    pass


def _call(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RenderError("FFmpeg failed:\n" + "\n".join(result.stderr.splitlines()[-12:]))


def render_video(manifest_path: Path, rows: list[dict], output_folder: Path, *,
                 overwrite: bool = False) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RenderError("FFmpeg is required for render (install it and add it to PATH)")
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    video = doc.get("video") or {}
    width, height, fps = (video.get("width", 1920), video.get("height", 1080), video.get("fps", 30))
    source_root = manifest_path.resolve().parent
    output_folder.mkdir(parents=True, exist_ok=True)
    output = (output_folder / "video.mp4").resolve()
    if output.exists() and not overwrite:
        raise RenderError(f"Output already exists: {output}; pass --overwrite to replace it")
    for row in rows:
        image = source_root / row["image"]
        if not image.is_file():
            raise RenderError(f"Missing image for scene {row['id']}: {image}")
        if row["audio"] and not (source_root / row["audio"]).is_file():
            raise RenderError(f"Missing audio for scene {row['id']}: {row['audio']}")
    with tempfile.TemporaryDirectory(prefix="frameledger_") as tmp:
        temp = Path(tmp)
        segments: list[Path] = []
        for index, row in enumerate(rows):
            dest = temp / f"scene_{index:05d}.mp4"
            scale = (f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                     f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,format=yuv420p")
            cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-loop", "1",
                   "-framerate", str(fps), "-i", str(source_root / row["image"])]
            if row["audio"]:
                cmd.extend(["-i", str(source_root / row["audio"])])
            else:
                cmd.extend(["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"])
            cmd.extend(["-map", "0:v:0", "-map", "1:a:0", "-vf", scale,
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                        "-r", str(fps), "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2"])
            if row["audio"]:
                cmd.extend(["-af", "apad"])
            cmd.extend(["-t", f"{row['duration_sec']:.3f}", "-movflags", "+faststart", str(dest)])
            _call(cmd)
            segments.append(dest)
        concat = temp / "segments.txt"
        concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in segments), encoding="utf-8")
        combined = temp / "combined.mp4"
        _call([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat",
               "-safe", "0", "-i", str(concat), "-c", "copy",
               "-movflags", "+faststart", str(combined)])
        shutil.copyfile(combined, output)
    return output
