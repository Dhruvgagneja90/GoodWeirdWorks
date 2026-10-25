"""Offline documentary shot planner and QA checker. Python 3.10+, no dependencies."""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
AUDIO_TYPES = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
SCENE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def timestamp(seconds: float, *, srt: bool = False) -> str:
    milliseconds = round(max(0, seconds) * 1000)
    hours, rest = divmod(milliseconds, 3600000)
    minutes, rest = divmod(rest, 60000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}{',' + format(ms, '03') if srt else ''}"


def inspect(path: Path, *, check_assets: bool = False, max_still: float = 12) -> tuple[list[dict], list[dict]]:
    if not math.isfinite(max_still) or max_still <= 0:
        raise ValueError("max_still must be a positive finite number")
    root = path.resolve().parent
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read JSON manifest: {error}") from error
    if not isinstance(document, dict):
        raise ValueError("Manifest must be a JSON object")
    findings: list[dict] = []
    def issue(level: str, code: str, detail: str) -> None:
        findings.append({"level": level, "code": code, "detail": detail})

    if document.get("schema_version") != 1:
        issue("error", "schema", "schema_version must be 1")
    video = document.get("video", {})
    if not isinstance(video, dict):
        issue("error", "video", "video must be an object")
        video = {}
    for key in ("width", "height", "fps"):
        val = video.get(key, {"width": 1920, "height": 1080, "fps": 30}[key])
        if isinstance(val, bool) or not isinstance(val, int) or val <= 0:
            issue("error", "settings", f"video.{key} must be a positive integer")
        elif key in ("width", "height") and val % 2:
            issue("error", "dimensions", f"video.{key} must be even for common H.264 workflows")
    rows = document.get("scenes")
    if not isinstance(rows, list) or not rows:
        issue("error", "scenes", "scenes must be a nonempty array")
        rows = []

    seen: set[str] = set()
    out: list[dict] = []
    start = 0.0
    for index, scene in enumerate(rows, 1):
        if not isinstance(scene, dict):
            issue("error", "scene_type", f"Scene {index} must be an object")
            continue
        sid = scene.get("id")
        if not isinstance(sid, str) or not SCENE_ID.fullmatch(sid):
            issue("error", "id", f"Scene {index} has an invalid id")
            sid = f"invalid_{index}"
        if sid in seen:
            issue("error", "duplicate", f"Duplicate scene id {sid}")
        seen.add(sid)
        name = scene.get("image")
        if not isinstance(name, str) or not name.strip():
            issue("error", "image", f"{sid}: image is required")
            name = "missing.png"
        suffix = Path(name).suffix.lower()
        if suffix not in IMAGE_TYPES:
            issue("error", "image_type", f"{sid}: unsupported image extension {suffix}")
        image = (root / name).resolve()
        if check_assets and not image.is_file():
            issue("error", "missing_image", f"{sid}: missing image {name}")
        duration = scene.get("duration_sec")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0 or duration > 3600:
            issue("error", "duration", f"{sid}: duration_sec must be >0 and <=3600")
            duration = 1
        if duration > max_still:
            issue("warning", "long_still", f"{sid}: {duration:g}s still exceeds {max_still:g}s")
        audio = scene.get("audio", "")
        if audio:
            if not isinstance(audio, str) or Path(audio).suffix.lower() not in AUDIO_TYPES:
                issue("error", "audio_type", f"{sid}: unsupported audio path")
            elif check_assets and not (root / audio).resolve().is_file():
                issue("error", "missing_audio", f"{sid}: missing audio {audio}")
        for field in ("caption", "narration", "chapter"):
            if not isinstance(scene.get(field, ""), str):
                issue("error", "text_type", f"{sid}: {field} must be text")
        caption = scene.get("caption", "")
        narration = scene.get("narration", "")
        chapter = scene.get("chapter", "")
        if not isinstance(caption, str): caption = ""
        if not isinstance(narration, str): narration = ""
        if not isinstance(chapter, str): chapter = ""
        if narration and not audio:
            issue("warning", "silent_narration", f"{sid}: narration text has no recorded audio")
        out.append({"id": sid, "start_sec": round(start, 3), "end_sec": round(start + duration, 3),
                    "duration_sec": duration, "image": name, "audio": audio or "", "chapter": chapter,
                    "narration": narration, "caption": caption})
        start += duration
    return out, findings


def export(rows: list[dict], findings: list[dict], output: Path) -> None:
    if not rows or any(x["level"] == "error" for x in findings):
        raise ValueError("Fix errors before exporting")
    output.mkdir(parents=True, exist_ok=True)
    (output / "timeline.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (output / "shotlist.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    cues = []
    chapters = []
    for row in rows:
        line = (row["caption"] or row["narration"]).strip()
        if line:
            cues.append(f"{len(cues) + 1}\n{timestamp(row['start_sec'], srt=True)} --> {timestamp(row['end_sec'], srt=True)}\n{line}")
        if row["chapter"].strip():
            chapters.append(f"{timestamp(row['start_sec'])} {row['chapter'].strip()}")
    (output / "subtitles.srt").write_text("\n\n".join(cues) + ("\n" if cues else ""), encoding="utf-8")
    (output / "chapters.txt").write_text("\n".join(chapters) + ("\n" if chapters else ""), encoding="utf-8")
    report = ["# FrameLedger QA", "", f"Scenes: {len(rows)}", f"Runtime: {timestamp(rows[-1]['end_sec'])}", ""]
    report.extend(f"- {x['level'].upper()} [{x['code']}]: {x['detail']}" for x in findings)
    if not findings: report.append("No findings.")
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan scenes, export draft subtitles, and audit still-image timing offline")
    parser.add_argument("command", choices=["check", "plan"])
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--check-assets", action="store_true")
    parser.add_argument("--max-still", type=float, default=12)
    parser.add_argument("--out", type=Path, default=Path("build"))
    args = parser.parse_args(argv)
    try:
        rows, findings = inspect(args.manifest, check_assets=args.check_assets, max_still=args.max_still)
        for finding in findings:
            print(f"{finding['level'].upper()} [{finding['code']}]: {finding['detail']}")
        if any(x["level"] == "error" for x in findings): return 2
        if args.command == "plan":
            export(rows, findings, args.out)
            print(f"Exported {len(rows)} scenes to {args.out}")
        return 0
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
