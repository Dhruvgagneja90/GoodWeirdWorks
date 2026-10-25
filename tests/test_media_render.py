"""Integration checks using synthetic media. Renderer test skips if FFmpeg unavailable."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from examples.generate_media import generate
from tools.frameledger import inspect
from tools.media import audit_media, png_size
from tools.render import render_video


class MediaIntegration(unittest.TestCase):
    def setUp(self):
        self.context = tempfile.TemporaryDirectory()
        self.addCleanup(self.context.cleanup)
        self.root = Path(self.context.name)
        self.assets = self.root / "demo_assets"
        generate(self.assets)
        self.path = self.root / "test.json"
        self.path.write_text(json.dumps({
            "schema_version": 1, "video": {"title": "Tiny Demo", "width": 320, "height": 180, "fps": 12},
            "scenes": [
                {"id": "opening", "image": "demo_assets/intro.png",
                 "audio": "demo_assets/silence.wav", "duration_sec": 1},
                {"id": "ending", "image": "demo_assets/reveal.png", "duration_sec": 1}
            ]
        }), encoding="utf-8")

    def test_generated_png_is_valid(self):
        self.assertEqual(png_size(self.assets / "intro.png"), (640, 360))

    def test_asset_check_is_clean(self):
        rows, found = inspect(self.path, check_assets=True)
        self.assertFalse([x for x in found if x["level"] == "error"])
        self.assertFalse([x for x in audit_media(self.path, rows) if x["level"] == "error"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/ffprobe unavailable")
    def test_render_synthetic_mp4(self):
        import subprocess
        rows, found = inspect(self.path, check_assets=True)
        self.assertFalse([x for x in found if x["level"] == "error"])
        mp4 = render_video(self.path, rows, self.root / "build")
        self.assertTrue(mp4.is_file())
        self.assertGreater(mp4.stat().st_size, 1000)
        result = subprocess.run([shutil.which("ffprobe"), "-v", "error", "-show_entries",
                                 "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(mp4)],
                                check=True, text=True, capture_output=True)
        self.assertAlmostEqual(float(result.stdout.strip()), 2, delta=.2)


if __name__ == "__main__":
    unittest.main()
