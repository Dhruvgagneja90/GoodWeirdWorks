import json
import tempfile
import unittest
import wave
from pathlib import Path

from tools.media import audit_media, png_size, wav_seconds
from tools.preview import render_preview
from tools.production import main


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.file = self.path / "example.json"
        self.document = {"schema_version": 1, "video": {"title": "Example <video>", "width": 1920, "height": 1080, "fps": 30},
                         "scenes": [{"id": "one", "image": "a.png", "duration_sec": 2, "caption": "<script>bad</script>"},
                                    {"id": "two", "image": "a.png", "duration_sec": 3, "narration": "Ending"}]}
        self.file.write_text(json.dumps(self.document), encoding="utf-8")

    def test_preview_escapes_html(self):
        rows = [{"id": "x", "image": "a.png", "start_sec": 0, "end_sec": 2, "duration_sec": 2,
                 "caption": "", "narration": "<script>alert(1)</script>", "chapter": ""}]
        dest = render_preview(rows, [], self.path / "preview.html", title="<title>")
        html = dest.read_text()
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;title&gt;", html)

    def test_repeated_image_detected(self):
        from tools.frameledger import inspect
        rows, _ = inspect(self.file)
        findings = audit_media(self.file, rows)
        self.assertIn("reused_image", {f["code"] for f in findings})

    def test_wav_length(self):
        wav = self.path / "audio.wav"
        with wave.open(str(wav), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(8000)
            handle.writeframes(b"\0\0" * 8000)
        self.assertAlmostEqual(wav_seconds(wav), 1, places=2)
        self.assertIsNone(png_size(wav))

    def test_preview_command(self):
        result = main(["preview", str(self.file), "--out", str(self.path / "out")])
        self.assertEqual(result, 0)
        self.assertTrue((self.path / "out" / "preview.html").is_file())

    def test_render_missing_asset(self):
        self.assertEqual(main(["render", str(self.file), "--out", str(self.path / "out")]), 2)


if __name__ == "__main__":
    unittest.main()
