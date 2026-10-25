"""FrameLedger production CLI: preflight, preview, plan, and local video assembly."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .frameledger import export, inspect
    from .media import audit_media
    from .preview import render_preview
    from .render import RenderError, render_video
except ImportError:
    from frameledger import export, inspect
    from media import audit_media
    from preview import render_preview
    from render import RenderError, render_video


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline documentary shot planning and assembly")
    parser.add_argument("command", choices=["check", "plan", "preview", "render"])
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, default=Path("build"))
    parser.add_argument("--max-still", type=float, default=12)
    parser.add_argument("--check-assets", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        rows, findings = inspect(args.manifest, check_assets=args.check_assets or args.command == "render",
                                 max_still=args.max_still)
        video = json.loads(args.manifest.read_text(encoding="utf-8")).get("video", {})
        w = video.get("width", 1920) if isinstance(video, dict) else 1920
        h = video.get("height", 1080) if isinstance(video, dict) else 1080
        if rows and not any(f["level"] == "error" for f in findings):
            findings += audit_media(args.manifest, rows, target_width=w, target_height=h)
        for finding in findings:
            print(f'{finding["level"].upper()} [{finding["code"]}]: {finding["detail"]}')
        if any(f["level"] == "error" for f in findings):
            return 2
        if args.command in ("plan", "preview", "render"):
            export(rows, findings, args.out)
        if args.command == "preview":
            dest = render_preview(rows, findings, args.out / "preview.html", title=video.get("title", "FrameLedger"))
            print(f"Preview written to {dest}")
        if args.command == "render":
            print(f"Video written to {render_video(args.manifest, rows, args.out, overwrite=args.overwrite)}")
        if args.command == "plan":
            print(f"Shot list, captions, chapters and QA report written to {args.out}")
        return 0
    except (OSError, ValueError, TypeError, RenderError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
