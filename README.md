# Good Weird Works — Open Tools

Practical, free tools for small creative teams. This repository is a public workshop, not the source code of the Good Weird Works commercial website.

## FrameLedger

**FrameLedger** is a zero-dependency Python command-line utility for planning documentary-style videos from scene manifests. It checks image durations and missing assets, exports shot lists, subtitle drafts and chapter timestamps, and provides a QA report.

This initial open-source release does not synthesize speech, generate images, render animation or claim external adoption.

### Quick start

Python 3.10 or later:

```bash
python3 tools/frameledger.py check examples/documentary.json --check-assets
python3 tools/frameledger.py plan examples/documentary.json --out build
python3 -m unittest discover -s tests -v
```

The supplied demo references imaginary media filenames, so `check --check-assets` intentionally reports missing assets. Use `check` without that switch to check structure alone; replace asset paths with your own before production.

### Expanded production workflow (v0.2 prototype)

For preflight checks, offline HTML previews and optional MP4 rendering:

```bash
python3 tools/production.py check examples/documentary.json
python3 tools/production.py preview examples/documentary.json --out build
python3 tools/production.py plan examples/documentary.json --out build
# Supply actual images and install FFmpeg before attempting:
python3 tools/production.py render examples/documentary.json --out build
```

New functionality detects repeated image paths, assesses PNG size/aspect ratio, compares PCM WAV audio length to scene duration, escapes user-supplied text in a standalone HTML preview, and assembles H.264/AAC MP4s locally through FFmpeg. See [production guide](docs/production.md). The sample references deliberately nonexistent assets, so render fails until you supply images. The renderer is a basic still-image assembler, **not** animated video generation.

### Output

- `build/shotlist.csv`: shot timing, source file and narration
- `build/timeline.json`: structured scene-level timeline
- `build/subtitles.srt`: draft scene captions
- `build/chapters.txt`: chapter timestamps
- `build/report.md`: validation findings

### Scope and limitations

The planner is offline and uses Python's standard library only. The basic planner does not align captions to voice recordings. The optional production command checks PCM WAV duration and can assemble a simple MP4 with FFmpeg. Review subtitles, source media licensing and video edits before publication.

See [usage and schema](docs/frameledger.md), [contribution guide](CONTRIBUTING.md), [security policy](SECURITY.md), and [license](LICENSE).

## Status

Experimental v0.1.0. No claims about users, downloads, third-party contributors, or suitability for production. Feedback and reproducible bug reports are welcome.
