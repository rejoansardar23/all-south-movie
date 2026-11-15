#!/usr/bin/env python3
"""Regression tests for multi-archive imports. No private archives required."""
import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_multi_catalog as imp


def message(mid: int, title="Collision Movie", year=2024, quality="1080p"):
    return {
        "id": mid, "type": "message", "date": "2026-11-01T00:00:00",
        "photo": "photos/photo_1.jpg",
        "text": f"{title} ({year})\nGenre: Action\nAudio: Hindi | Telugu\n{quality}",
        "text_entities": [
            {"type": "plain", "text": f"{quality}\n"},
            {"type": "link", "text": f"https://example.org/{mid}/{quality.lower()}"},
        ],
    }


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "imports").mkdir()
        (self.root / "data").mkdir()
        self.manifest = self.root / "imports/collections.json"
        self.catalog = self.root / "data/catalog.json"
        self.base_movie = {
            "id": 42, "title": "Legacy South Film", "year": 2022, "type": "Movie",
            "genres": ["Action"], "languages": ["Hindi"],
            "poster": "photos/old.jpg", "thumbnail": "photos/old.jpg",
            "added": "2026-01-01", "reactions": 2,
            "sources": [{"url": "https://example.org/old", "host": "example.org", "label": "720p"}],
            "sourceIds": [42], "sourcePage": "messages.html"
        }
        self.catalog.write_text(json.dumps({"version": 1, "name": "Southscreen", "movies": [self.base_movie]}))
        self.names = ["bollywood-movies", "hollywood-movies"]
        self.manifest.write_text(json.dumps({"collections": [
            {"id": name, "path": f"imports/{name}", "enabled": True} for name in self.names
        ]}))
        self.args = argparse.Namespace(
            manifest=self.manifest, base=self.catalog, output=self.catalog,
            media_base_url="", check_only=False, strict_missing=False,
            prune_unlisted=False, prune_unavailable=False
        )
        self.root_patch = patch.object(imp, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def archive(self, name, messages):
        folder = self.root / "imports" / name
        (folder / "photos").mkdir(parents=True, exist_ok=True)
        (folder / "photos/photo_1.jpg").write_bytes(b"fake image content")
        (folder / "result.json").write_text(json.dumps({"messages": messages}))
        # Test fourth HTML page support, including reused message IDs.
        (folder / "messages4.html").write_text(
            '<div class="message default" id="message7">'
            '<img class="photo" src="photos/photo_1.jpg"></div>'
        )

    def test_name_collisions_and_legacy_id_preservation(self):
        self.archive(self.names[0], [message(7)])
        self.archive(self.names[1], [message(7)])
        report = imp.build(self.args)
        self.assertEqual(report["titles"], 3)
        catalog = json.loads(self.catalog.read_text())
        self.assertEqual(catalog["version"], 2)
        self.assertEqual(catalog["movies"][-1]["id"], 42)
        new = [m for m in catalog["movies"] if m.get("collectionId")]
        self.assertEqual(len(new), 2)
        self.assertEqual(len({m["id"] for m in new}), 2)
        self.assertNotEqual(new[0]["poster"], new[1]["poster"])
        self.assertTrue(all(m["sourcePage"].endswith("messages4.html") for m in new))
        self.assertTrue(all(m["languages"] == ["Hindi", "Telugu"] for m in new))
        self.assertTrue(all(m["poster"].startswith("imports/") for m in new))
        report2 = imp.build(self.args)
        self.assertEqual(report2["titles"], 3)
        self.assertEqual(len(json.loads(self.catalog.read_text())["movies"]), 3)

    def test_duplicate_posts_same_collection_merge(self):
        self.archive(self.names[0], [message(7), message(8, quality="720p")])
        report = imp.build(self.args)
        self.assertEqual(report["titles"], 2)
        imported = [m for m in json.loads(self.catalog.read_text())["movies"] if m.get("collectionId")]
        self.assertEqual(len(imported), 1)
        self.assertEqual(len(imported[0]["sources"]), 2)
        self.assertEqual(len(imported[0]["sourceIds"]), 2)

    def test_partial_media_preserves_link_aliases(self):
        one = message(7, quality="1080p")
        two = message(8, quality="720p")
        two["photo"] = "photos/photo_2.jpg"
        self.archive(self.names[0], [one, two])
        (self.root / "imports/bollywood-movies/photos/photo_2.jpg").write_bytes(b"other poster")
        imp.build(self.args)
        initial = [m for m in json.loads(self.catalog.read_text())["movies"] if m.get("collectionId")][0]
        self.assertEqual(len(initial["sourceIds"]), 2)
        self.assertEqual(len(initial["sources"]), 2)
        # The next checkout has only the first poster; previous links must survive.
        (self.root / "imports/bollywood-movies/photos/photo_2.jpg").unlink()
        imp.build(self.args)
        updated = [m for m in json.loads(self.catalog.read_text())["movies"] if m.get("collectionId")][0]
        self.assertEqual(set(updated["sourceIds"]), set(initial["sourceIds"]))
        self.assertEqual({s["url"] for s in updated["sources"]}, {s["url"] for s in initial["sources"]})

    def test_missing_media_or_archive_preserves_previous_catalog(self):
        self.archive(self.names[0], [message(7)])
        imp.build(self.args)
        (self.root / "imports/bollywood-movies/photos/photo_1.jpg").unlink()
        again = imp.build(self.args)
        self.assertEqual(again["titles"], 2)
        self.assertEqual(again["collections"][self.names[0]]["preservedPrevious"], 1)
        (self.root / "imports/bollywood-movies/result.json").unlink()
        again = imp.build(self.args)
        self.assertEqual(again["titles"], 2)
        self.assertEqual(again["collections"][self.names[0]]["status"], "missing-preserved")

    def test_check_only_and_security_of_manifest(self):
        self.archive(self.names[0], [message(7)])
        before = self.catalog.read_bytes()
        self.args.check_only = True
        report = imp.build(self.args)
        self.assertEqual(report["titles"], 2)
        self.assertEqual(self.catalog.read_bytes(), before)
        self.args.check_only = False
        self.manifest.write_text(json.dumps({"collections": [
            {"id": "bollywood-movies", "path": "../somewhere", "enabled": True}
        ]}))
        with self.assertRaisesRegex(ValueError, "Unsafe archive location"):
            imp.build(self.args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
