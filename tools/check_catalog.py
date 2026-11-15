#!/usr/bin/env python3
"""Validate legacy and multi-archive catalog records without contacting providers.

Imported media may live only on S3; use --require-import-media before an initial
upload to ensure all import posters exist on the staging computer.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from archive_paths import archive_folder

ROOT = Path(__file__).resolve().parents[1]
IMAGE = re.compile(r"^photos/[A-Za-z0-9_@.() +\-]+\.(?:jpg|jpeg|png|webp)$", re.I)
NEW_IMAGE = re.compile(r"^imports/([a-z0-9-]+)/(photos|images)/[A-Za-z0-9_@.() +\-]+\.(?:jpg|jpeg|png|webp)$", re.I)
HTML = re.compile(r"^messages(?:\d+)?\.html$", re.I)
COLLECTION = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")


def image_valid(path, collection_id):
    if not isinstance(path, str):
        return False
    if not collection_id:
        return bool(IMAGE.fullmatch(path))
    if NEW_IMAGE.fullmatch(path):
        return NEW_IMAGE.fullmatch(path).group(1) == collection_id
    parsed = urlsplit(path)
    # Optional imported images on a HTTPS media CDN.
    return (parsed.scheme == "https" and bool(parsed.hostname) and
            not parsed.username and not parsed.password and
            f"/imports/{collection_id}/" in parsed.path and
            re.search(r"\.(?:jpg|jpeg|png|webp)$", parsed.path, re.I) is not None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", type=Path, help="Optional JSON array of paths for partial checkouts")
    parser.add_argument("--require-import-media", action="store_true", help="Require imported images to exist locally")
    args = parser.parse_args()
    known_paths = set(json.loads(args.paths.read_text())) if args.paths else None
    export = json.loads((ROOT / "result.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "data/catalog.json").read_text(encoding="utf-8"))
    original = {m["id"]: m for m in export["messages"]}
    manifest_path = ROOT / "imports/collections.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"collections": []}
    source_folders = {entry["id"]: archive_folder(ROOT, entry) for entry in manifest.get("collections", [])}
    errors, ids, aliases, source_count = [], set(), set(), 0
    for movie in catalog["movies"]:
        mid = movie["id"]
        name = movie.get("collectionId")
        imported = bool(name)
        if imported and (not isinstance(name, str) or not COLLECTION.fullmatch(name)):
            errors.append(f"Invalid collection ID: {mid}/{name!r}")
        if mid in ids:
            errors.append(f"Duplicate movie ID: {mid}")
        ids.add(mid)
        if type(mid) is not int or not movie.get("title", "").strip() or not 1900 <= movie.get("year", 0) <= 2099:
            errors.append(f"Invalid title, ID, or year: {mid}")
        if imported and (mid < 1 << 48 or mid >= 1 << 53):
            errors.append(f"Imported ID out of safe browser range: {mid}")
        ids_for_movie = movie.get("sourceIds")
        if not isinstance(ids_for_movie, list) or not ids_for_movie or mid not in ids_for_movie:
            errors.append(f"Missing current source ID: {mid}")
            ids_for_movie = []
        for alias in ids_for_movie:
            if alias in aliases:
                errors.append(f"Duplicate source ID across movies: {mid}/{alias}")
            aliases.add(alias)
        allowed_urls = set()
        if not imported:
            for source_id in ids_for_movie:
                if source_id not in original:
                    errors.append(f"Unknown legacy source message: {mid}/{source_id}")
                    continue
                for entity in original[source_id].get("text_entities", []):
                    if entity.get("type") in ("link", "text_link"):
                        allowed_urls.add(entity.get("href", entity.get("text", "")).strip())
        for field in ("poster", "thumbnail"):
            image = movie.get(field)
            if not image_valid(image, name):
                errors.append(f"Invalid image reference: {mid}/{image}")
                continue
            is_remote = image.startswith("https://")
            should_exist = not imported or args.require_import_media
            # Raw import assets are ignored in Git; do not require them in CI.
            if should_exist and not is_remote:
                if imported and name in source_folders:
                    # Imported paths are normalized for AWS; raw files may live in a
                    # different top-level upload folder that must not be renamed.
                    relative = image.split("/", 2)[2]
                    original_path = source_folders[name] / relative
                else:
                    original_path = ROOT / image
                present = image in known_paths if known_paths is not None else original_path.is_file()
                if not present:
                    errors.append(f"Missing image: {mid}/{image}")
        seen = set()
        for source in movie.get("sources", []):
            source_count += 1
            url = source.get("url", "")
            parsed = urlsplit(url)
            if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
                errors.append(f"Unsafe source URL: {mid}")
            if not imported and url not in allowed_urls:
                errors.append(f"Source URL missing from legacy archive: {mid}")
            if url in seen:
                errors.append(f"Duplicate source URL: {mid}")
            seen.add(url)
            if re.search(r"\.(?:jpg|jpeg|png|gif|webp)$", parsed.path, re.I):
                errors.append(f"Image incorrectly included as video source: {mid}")
        if not movie.get("sources"):
            errors.append(f"No source links: {mid}")
        page = movie.get("sourcePage", "")
        if imported:
            if not page.startswith(f"imports/{name}/") or not HTML.fullmatch(page.rsplit("/", 1)[-1]):
                errors.append(f"Invalid imported source page: {mid}/{page}")
        elif page not in ("messages.html", "messages2.html", "messages3.html"):
            errors.append(f"Unknown legacy source page: {mid}")
    if errors:
        print("\n".join(errors[:100]))
        raise SystemExit(f"{len(errors)} catalog checks failed")
    count_imported = sum(bool(m.get("collectionId")) for m in catalog["movies"])
    print(f"PASS: {len(ids):,} movies ({count_imported:,} imported), {source_count:,} source links, no ID collisions")


if __name__ == "__main__":
    main()
