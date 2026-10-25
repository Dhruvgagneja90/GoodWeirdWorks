import json
import tempfile
import unittest
from pathlib import Path

from tools.frameledger import export, inspect, main, timestamp


class FrameLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = self.root / "scenes.json"
        self.payload = {
            "schema_version": 1,
            "video": {"width": 1920, "height": 1080, "fps": 30},
            "scenes": [
                {"id": "intro", "image": "a.png", "duration_sec": 4.5, "caption": "A clue", "chapter": "Opening"},
                {"id": "ending", "image": "b.png", "duration_sec": 5.5, "narration": "The end."}
            ]
        }
        self.write()

    def write(self):
        self.manifest.write_text(json.dumps(self.payload), encoding="utf-8")

    def test_timestamps(self):
        self.assertEqual(timestamp(3661.25, srt=True), "01:01:01,250")

    def test_valid_manifest(self):
        rows, findings = inspect(self.manifest)
        self.assertEqual([r["start_sec"] for r in rows], [0, 4.5])
        self.assertFalse(any(x["level"] == "error" for x in findings))

    def test_plan_exports(self):
        rows, findings = inspect(self.manifest)
        export(rows, findings, self.root / "out")
        self.assertIn("00:00:04,500", (self.root / "out" / "subtitles.srt").read_text())
        self.assertIn("Opening", (self.root / "out" / "chapters.txt").read_text())

    def test_duplicate_ids(self):
        self.payload["scenes"][1]["id"] = "intro"
        self.write()
        self.assertIn("duplicate", [f["code"] for f in inspect(self.manifest)[1]])

    def test_missing_assets(self):
        self.assertIn("missing_image", [f["code"] for f in inspect(self.manifest, check_assets=True)[1]])

    def test_reject_bool_duration(self):
        self.payload["scenes"][0]["duration_sec"] = True
        self.write()
        self.assertIn("duration", [f["code"] for f in inspect(self.manifest)[1]])

    def test_empty_scenes(self):
        self.payload["scenes"] = []
        self.write()
        self.assertIn("scenes", [f["code"] for f in inspect(self.manifest)[1]])

    def test_long_still(self):
        self.payload["scenes"][0]["duration_sec"] = 15
        self.write()
        self.assertIn("long_still", [f["code"] for f in inspect(self.manifest)[1]])

    def test_nonfinite_duration(self):
        self.payload["scenes"][0]["duration_sec"] = float("inf")
        self.write()
        self.assertIn("duration", [f["code"] for f in inspect(self.manifest)[1]])

    def test_command_exit_code(self):
        self.assertEqual(main(["check", str(self.manifest)]), 0)
        self.assertEqual(main(["check", str(self.manifest), "--check-assets"]), 2)


if __name__ == "__main__":
    unittest.main()
