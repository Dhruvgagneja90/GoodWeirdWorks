# FrameLedger production commands

The public `tools/production.py` command expands the minimal FrameLedger planner with offline media preflight, HTML timeline previews and optional local FFmpeg assembly.

## Start with a real manifest

Copy `examples/documentary.json` and point every `image` path to a picture you have permission to use. To render narration, point each optional `audio` field to an actual WAV/MP3/etc file. All paths are relative to the manifest.

```bash
python3 tools/production.py check examples/documentary.json
python3 tools/production.py plan examples/documentary.json --out build
python3 tools/production.py preview examples/documentary.json --out build
python3 tools/production.py render examples/documentary.json --out build
```

The supplied sample intentionally references missing assets. **Render will fail until you supply those assets.** For a throwaway media smoke test, generate original synthetic placeholders:

```bash
python3 examples/generate_media.py
```

That script creates three 640×360 PNGs and a silent WAV in `examples/demo_assets`. It does not create a complete documentary or real voiceover.

### New QA signals

- Still duration warnings (configurable with `--max-still`)
- Repeated source image paths
- Low-resolution PNGs and mismatched PNG aspect ratio
- PCM WAV narration duration mismatches above 1 second
- Missing image/audio assets when using `--check-assets` or `render`

PNG and WAV inspections use Python standard library. Other valid formats are accepted by the planner, but only PNG size and PCM WAV duration are measured without external tools.

### Rendering

Rendering requires a local FFmpeg binary with H.264 and AAC encoding available on `PATH`. Each scene is rendered to a segment with an optional audio file; missing audio produces silence. Segments are concatenated losslessly. You get `video.mp4` under `--out`.

Rendering generates static images only (no motion effects, transitions, or real-time audio alignment). It can consume significant CPU and disk space. Check subtitles and timing yourself.

### HTML preview

`preview.html` is a standalone HTML file; it contains no external scripts and escapes text supplied in the manifest. It visualizes scene ordering, still duration, source images and QC findings. It is **not** a playable media preview.

### Disclaimer

Version 0.2 prototype. No claims of external users, independence from FFmpeg for rendering, or Claude integration.
