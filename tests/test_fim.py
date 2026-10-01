import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fim


class IntegrityMonitorTests(unittest.TestCase):
    def test_compare_reports_each_change_type(self):
        added, removed, modified = fim.compare(
            {"same.txt": "a", "gone.txt": "b", "changed.txt": "c"},
            {"same.txt": "a", "new.txt": "d", "changed.txt": "e"},
        )
        self.assertEqual(added, ["new.txt"])
        self.assertEqual(removed, ["gone.txt"])
        self.assertEqual(modified, ["changed.txt"])

    def test_manifest_excludes_its_own_file_and_hashes_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "nested").mkdir()
            (root / "nested" / "note.txt").write_text("hello", encoding="utf-8")
            manifest = root / "manifest.json"
            result = fim.build_manifest(root, manifest)
            self.assertEqual(list(result["files"]), ["nested/note.txt"])
            fim.write_manifest(result, manifest)
            self.assertNotIn("manifest.json", fim.build_manifest(root, manifest)["files"])

    def test_load_manifest_rejects_bad_structure(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "bad.json"
            source.write_text(json.dumps({"version": 1, "algorithm": "sha256"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                fim.load_manifest(source)


if __name__ == "__main__":
    unittest.main()

