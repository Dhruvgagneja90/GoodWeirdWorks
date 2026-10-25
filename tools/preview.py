"""Create a safe, offline HTML preview of the planned documentary timeline."""
from __future__ import annotations

from html import escape
from pathlib import Path


def render_preview(rows: list[dict], issues: list[dict], destination: Path, title: str = "FrameLedger") -> Path:
    """No external JS, fonts, network or embedded private media."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    runtime = rows[-1]["end_sec"] if rows else 0
    scene_html = []
    for row in rows:
        shot = escape(str(row["id"]))
        narration = escape(str(row["narration"] or "No narration text"))
        image = escape(str(row["image"]))
        chapter = escape(str(row["chapter"] or ""))
        dur = row["duration_sec"]
        percent = max(.4, 100 * dur / runtime) if runtime else 100
        scene_html.append(
            f'<article><div class="head"><b>{shot}</b><span>{row["start_sec"]:.1f}s–{row["end_sec"]:.1f}s · {dur:.1f}s</span></div>'
            f'<div class="bar"><i style="width:{min(percent, 100):.2f}%"></i></div>'
            f'<p class="caption">{narration}</p><p class="meta">Image: {image}'
            f'{" · Chapter: " + chapter if chapter else ""}</p></article>')
    findings_html = "".join(
        f'<li class="{escape(str(i["level"]))}">{escape(str(i["level"]).upper())} · '
        f'{escape(str(i["code"]))}: {escape(str(i["detail"]))}</li>'
        for i in issues
    ) or "<li>No findings.</li>"
    markup = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · FrameLedger preview</title>
<style>
:root{{color-scheme:light; font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:#fafaf9;color:#18181b}}
body{{margin:auto;max-width:940px;padding:32px 22px 75px;line-height:1.5}}
h1{{font-size:clamp(28px,5vw,45px);line-height:1.1;letter-spacing:-.035em;margin-bottom:8px}}
p.sub{{color:#57534e;margin-bottom:30px}} article{{background:#fff;border:1px solid #e4e4e7;padding:21px 23px;margin:14px 0;border-radius:9px}}
.head{{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}}.head span,.meta{{color:#71717a;font-size:13px}}
.bar{{margin:14px 0;background:#e4e4e7;height:10px;border-radius:3px;overflow:hidden}}.bar i{{background:#27272a;display:block;height:100%}}
.caption{{margin:10px 0;white-space:pre-wrap}}.meta{{overflow-wrap:anywhere}}
section{{margin-top:40px}}li{{padding:5px 0;overflow-wrap:anywhere}}li.error{{color:#b91c1c}}li.warning{{color:#92400e}}
footer{{color:#71717a;font-size:12px;margin-top:36px}}
</style></head><body>
<header><h1>{escape(title)}</h1><p class="sub">{len(rows)} scenes · {runtime/60:.1f} minutes · Timeline preview</p></header>
<main>{''.join(scene_html)}</main>
<section><h2>Quality checks</h2><ul>{findings_html}</ul></section>
<footer>FrameLedger · This is a plan, not a playable video. Review audio timing and source rights before publishing.</footer>
</body></html>"""
    destination.write_text(markup, encoding="utf-8")
    return destination
