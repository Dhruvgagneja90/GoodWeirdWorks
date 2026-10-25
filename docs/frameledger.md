# FrameLedger user guide

## Schema

A JSON object with `schema_version: 1`, a `video` object and a nonempty `scenes` array.

Each scene requires:
- `id`: unique 1–64 character identifier (letters, digits, underscore, hyphen)
- `image`: a path to a PNG/JPEG/WebP/BMP image, relative to the manifest
- `duration_sec`: positive finite number no more than 3,600

Optional strings: `audio`, `caption`, `narration`, `chapter`. An audio field is a reference to an existing file; this planner **does not** generate voices, decode audio or measure audio length. The optional `video` settings `width`, `height` and `fps` must be positive integers; width and height must be even.

## Example

```bash
python3 tools/frameledger.py check examples/documentary.json
python3 tools/frameledger.py check examples/documentary.json --max-still 6
python3 tools/frameledger.py plan examples/documentary.json --out build
```

When using `--check-assets`, reference real image/audio files first or the command reports missing files. This is intentional.

## Output accuracy

Timestamps derive from the explicit scene durations, not the recorded audio. SRT subtitles are a *scene-level draft*, not word-aligned captions. Chapter titles appear at the first frame of a scene. Check all exported files in a video editor before publication.

## Limitations

This is a planning and QA tool only, not a rendering or full video-generation solution. The tool does not guarantee retention, platform monetization, original content, accessibility compliance or third-party licensing.
