from pathlib import Path
try:
    import tomllib
except ImportError:
    import tomli as tomllib
import unittest

class PackagingTests(unittest.TestCase):
    def test_project_metadata(self):
        root = Path(__file__).resolve().parents[1]
        metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(metadata["project"]["scripts"]["frameledger"], "tools.production:main")
        self.assertTrue((root / "LICENSE").exists())

if __name__ == "__main__":
    unittest.main()
