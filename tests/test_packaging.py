from pathlib import Path
import unittest

class PackagingTests(unittest.TestCase):
    def test_project_metadata(self):
        root = Path(__file__).resolve().parents[1]
        metadata = (root / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('frameledger = "tools.production:main"', metadata)
        self.assertIn('name = "frameledger-open-tools"', metadata)
        self.assertTrue((root / "LICENSE").exists())

if __name__ == "__main__":
    unittest.main()
