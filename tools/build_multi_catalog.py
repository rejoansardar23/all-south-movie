#!/usr/bin/env python3
"""Merge many Telegram HTML/JSON exports into the existing Southscreen catalog.

Usage:
    python tools/build_multi_catalog.py
    python tools/build_multi_catalog.py --check-only

This keeps all legacy movie IDs and the website's existing catalog schema.
Each new archive has its own namespace. Raw exports are never overwritten.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_catalog import GENRES, get_links, normalize  # existing, tested archive parser
from archive_paths import archive_folder

COLLECTION_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
IMAGE_RE = re.compile(r"^(photos|images)/[A-Za-z0-9_@.() +\-]+\.(?:jpg|jpeg|png|webp)$", re.I)
HTML_RE = re.compile(r"^messages(\d*)\.html$", re.I)


def stable_id(collection_id: str, message_id: int) -> int:
    """Integers below 2**53, stable between imports, distinct from legacy IDs."""
    raw = hashlib.sha256(f"{collection_id}:{message_id}".encode("utf-8")).digest()
    return (1 << 48) + int.from_bytes(raw[:6], "big")


def source_text(message: dict) -> str:
    raw = message.get("text", "")
    if isinstance(raw, str):
        return normalize(raw)
    if isinstance(raw, list):
        return normalize("".join(part if isinstance(part, str) else str(part.get("text", "")) for part in raw if isinstance(part, (str, dict))))
    return ""


def genre_labels(text: str) -> list[str]:
    match = re.search(r"(?im)genre\s*:\s*(.+)", text)
    genres = []
    if match:
        for token in re.split(r"[|,#]+", match.group(1)):
            candidate = token.strip().strip("#").casefold()
            if candidate in GENRES:
                genres.append(GENRES[candidate])
            else:
                genres.extend(GENRES[word.casefold()] for word in re.findall(r"[A-Za-z-]+", token) if word.casefold() in GENRES)
    return sorted(set(genres))


def language_labels(text: str) -> list[str]:
    match = re.search(r"(?im)audio\s*:\s*(.+)", text)
    audio = match.group(1).upper() if match else ""
    patterns = (
        ("Hindi", r"\bHINDI\b|\bHIN\b"),
        ("Tamil", r"\bTAMIL\b|\bTAM\b"),
        ("Telugu", r"\bTELUGU\b|\bTEL\b"),
        ("Malayalam", r"\bMALAYALAM\b|\bMAL\b"),
        ("Kannada", r"\bKANNADA\b|\bKAN\b"),
        ("English", r"\bENGLISH\b|\bENG\b"),
    )
    return [name for name, pattern in patterns if re.search(pattern, audio)]


class ThumbnailMap(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.page = ""
        self.thumbnails = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div" and re.search(r"\bmessage\b", attrs.get("class", "")) and attrs.get("id", "").startswith("message"):
            identifier = attrs["id"].removeprefix("message")
            self.current = identifier if identifier.isdigit() else None
            if self.current:
                self.thumbnails.setdefault(int(self.current), (self.page, None))
        if tag == "img" and self.current and "photo" in attrs.get("class", "").split():
            self.thumbnails[int(self.current)] = (self.page, attrs.get("src"))


def message_pages(folder: Path) -> list[Path]:
    paths = [p for p in folder.iterdir() if p.is_file() and HTML_RE.fullmatch(p.name)]
    return sorted(paths, key=lambda p: (int(HTML_RE.fullmatch(p.name).group(1) or "1"), p.name))


def safe_image(value: str, archive: Path, collection_id: str, media_base: str) -> str | None:
    if not isinstance(value, str) or not IMAGE_RE.fullmatch(value):
        return None
    source = archive / value
    if not source.is_file():
        return None
    relative = f"imports/{collection_id}/{value.replace(chr(92), '/')}"
    return media_base.rstrip("/") + "/" + relative if media_base else relative


def make_movie(message: dict, collection_id: str, folder: Path, thumbs: dict, media_base: str, skipped: collections.Counter) -> dict | None:
    if message.get("type") != "message":
        return None
    text = source_text(message)
    first_lines = [line.strip() for line in text.splitlines() if line.strip()][:3]
    found = next((m for line in first_lines if (m := re.search(r"^(.+?)\s*\((19\d{2}|20\d{2})\)", line))), None)
    if not found:
        skipped["missing_title_year"] += 1
        return None
    title = re.sub(r"^.*?\btitle\s*[:\-]\s*", "", found.group(1).strip(), flags=re.I)
    title = re.sub(r"^[^\w\u0900-\u097f]+|[^\w\u0900-\u097f!?]+$", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    if not title or len(title) > 120 or re.search(r"uploaded|join our|premium channel", title, re.I):
        skipped["invalid_or_advertising"] += 1
        return None
    links = get_links(message)
    if not links:
        skipped["missing_source_links"] += 1
        return None
    message_id = message.get("id")
    if type(message_id) is not int or message_id < 1:
        skipped["invalid_message_id"] += 1
        return None
    photo = safe_image(message.get("photo", ""), folder, collection_id, media_base)
    if not photo:
        skipped["missing_poster"] += 1
        return None
    page, thumb = thumbs.get(message_id, ("messages.html", None))
    thumbnail = safe_image(thumb, folder, collection_id, media_base) if thumb else None
    date = str(message.get("date", ""))[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        skipped["invalid_date"] += 1
        return None
    season = re.search(r"(?i)\bseason\s*(\d+)\b|\bS(\d{1,2})\b", "\n".join(first_lines))
    if season and not re.search(r"(?i)\bseason\b|\bS\d{1,2}\b", title):
        title += " — Season " + next(v for v in season.groups() if v)
    kind = "Series" if season or re.search(r"(?i)web.?series|\bseries\b", "\n".join(first_lines)) else "Movie"
    sid = stable_id(collection_id, message_id)
    return {
        "id": sid, "title": title, "year": int(found.group(2)), "type": kind,
        "genres": genre_labels(text), "languages": language_labels(text),
        "poster": photo, "thumbnail": thumbnail or photo,
        "added": date, "reactions": sum(int(r.get("count", 0)) for r in message.get("reactions", []) if isinstance(r, dict)),
        "sources": links, "sourceIds": [sid], "sourcePage": f"imports/{collection_id}/{page}",
        "collectionId": collection_id,
    }


def group_movies(items: list[dict], existing: dict) -> list[dict]:
    """Deduplicate repeated posts *within* one archive; never merge separate archives."""
    groups = {}
    for movie in sorted(items, key=lambda m: (m["added"], m["id"])):
        key = (re.sub(r"\W+", "", movie["title"].casefold()), movie["year"], movie["type"])
        prior = groups.get(key)
        if not prior:
            groups[key] = movie
            continue
        # Keep the original canonical ID and all aliases for existing watchlists.
        canonical_id = existing.get(key, prior["id"])
        movie["id"] = canonical_id
        movie["sourceIds"] = list(dict.fromkeys(prior["sourceIds"] + movie["sourceIds"]))
        movie["genres"] = sorted(set(prior["genres"] + movie["genres"]))
        movie["languages"] = sorted(set(prior["languages"] + movie["languages"]))
        # Newest link wins for a provider/quality pair.
        seen = {(s["host"], s["label"]) for s in movie["sources"]}
        seen_urls = {s["url"] for s in movie["sources"]}
        for src in prior["sources"]:
            if (src["host"], src["label"]) not in seen and src["url"] not in seen_urls:
                movie["sources"].append(src)
                seen.add((src["host"], src["label"]))
                seen_urls.add(src["url"])
        groups[key] = movie
    for key, movie in groups.items():
        if key in existing and movie["id"] != existing[key]:
            movie["sourceIds"].insert(0, movie["id"])
            movie["id"] = existing[key]
            movie["sourceIds"] = list(dict.fromkeys([movie["id"]] + movie["sourceIds"]))
    return list(groups.values())


def import_collection(collection_id: str, folder: Path, media_base: str, previous: list[dict]) -> tuple[list[dict], dict]:
    json_path = folder / "result.json"
    if not json_path.is_file():
        raise ValueError(f"{collection_id}: missing result.json in {folder}")
    try:
        export = json.loads(json_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"{collection_id}: invalid result.json: {exc}") from exc
    if not isinstance(export.get("messages"), list):
        raise ValueError(f"{collection_id}: result.json must contain a messages array")
    thumbs = ThumbnailMap()
    for page in message_pages(folder):
        thumbs.page = page.name
        thumbs.current = None
        thumbs.feed(page.read_text(encoding="utf-8-sig", errors="replace"))
    skipped = collections.Counter()
    items = [item for message in export["messages"] if isinstance(message, dict)
             if (item := make_movie(message, collection_id, folder, thumbs.thumbnails, media_base, skipped))]
    old = {(re.sub(r"\W+", "", m["title"].casefold()), m["year"], m["type"]): m["id"] for m in previous}
    movies = group_movies(items, old)
    return movies, {"rawMessages": len(export["messages"]), "movies": len(movies), "skipped": dict(skipped)}


def build(args: argparse.Namespace) -> dict:
    manifest_path = args.manifest.resolve()
    content = json.loads(manifest_path.read_text(encoding="utf-8"))
    collections = content.get("collections")
    if not isinstance(collections, list):
        raise ValueError("Manifest must contain a collections array")
    catalog = json.loads(args.base.read_text(encoding="utf-8"))
    if not isinstance(catalog.get("movies"), list):
        raise ValueError("Base catalog must contain a movies array")
    existing = catalog["movies"]
    legacy = [movie for movie in existing if not movie.get("collectionId")]
    previous_by_collection = collections_defaultdict()
    for movie in existing:
        if movie.get("collectionId"):
            previous_by_collection[movie["collectionId"]].append(movie)
    imported = []
    report = {}
    ids = set()
    for entry in collections:
        if not isinstance(entry, dict):
            raise ValueError("Every collection must be an object")
        name = entry.get("id", "")
        if not isinstance(name, str) or not COLLECTION_RE.fullmatch(name) or name in ids:
            raise ValueError(f"Invalid or duplicate collection ID: {name!r}")
        ids.add(name)
        if entry.get("enabled", True) is False:
            # Intentionally disabled entries preserve their last successfully imported catalog.
            imported += previous_by_collection.pop(name, [])
            report[name] = {"status": "disabled-preserved"}
            continue
        folder = archive_folder(ROOT, entry)
        if not folder.is_dir() or not (folder / "result.json").is_file():
            if args.strict_missing:
                raise ValueError(f"Missing source collection: {folder / 'result.json'}")
            previous_items = previous_by_collection.pop(name, [])
            imported.extend(previous_items)
            report[name] = {"status": "missing-preserved" if previous_items else "not-uploaded", "movies": len(previous_items)}
            continue
        previous_items = previous_by_collection.pop(name, [])
        movies, info = import_collection(name, folder, args.media_base_url, previous_items)
        # Missing ignored media must never erase titles that were imported earlier.
        if not args.prune_unavailable:
            old_by_id = {movie["id"]: movie for movie in previous_items}
            present_ids = set()
            for movie in movies:
                old_movie = old_by_id.get(movie["id"])
                if old_movie:
                    # A partial local media checkout may contain just one of several
                    # repeated posts. Keep previous aliases and non-duplicate links.
                    movie["sourceIds"] = list(dict.fromkeys(movie["sourceIds"] + old_movie.get("sourceIds", [])))
                    movie["genres"] = sorted(set(movie["genres"] + old_movie.get("genres", [])))
                    movie["languages"] = sorted(set(movie["languages"] + old_movie.get("languages", [])))
                    known = {(source["host"], source["label"]) for source in movie["sources"]}
                    known_urls = {source["url"] for source in movie["sources"]}
                    for src in old_movie.get("sources", []):
                        if (src["host"], src["label"]) not in known and src["url"] not in known_urls:
                            movie["sources"].append(src)
                            known.add((src["host"], src["label"]))
                            known_urls.add(src["url"])
                present_ids.update(movie.get("sourceIds", [movie["id"]]))
            preserved = [old for old in previous_items
                         if not set(old.get("sourceIds", [old["id"]])).intersection(present_ids)]
            imported.extend(preserved)
            info["preservedPrevious"] = len(preserved)
        imported.extend(movies)
        report[name] = {"status": "imported", **info}
    # Preserve previously imported collections not currently listed in the manifest.
    for name, movies in previous_by_collection.items():
        if args.prune_unlisted:
            report[name] = {"status": "pruned", "movies": len(movies)}
        else:
            imported.extend(movies)
            report[name] = {"status": "unlisted-preserved", "movies": len(movies)}
    merged = sorted(legacy + imported, key=lambda m: (m.get("added", ""), m["id"]), reverse=True)
    seen_ids = set()
    all_aliases = set()
    for movie in merged:
        if movie["id"] in seen_ids:
            raise ValueError(f"Duplicate global movie ID: {movie['id']}")
        seen_ids.add(movie["id"])
        for alias in movie.get("sourceIds", []):
            if alias in all_aliases:
                raise ValueError(f"Duplicate source ID / alias across movies: {alias}")
            all_aliases.add(alias)
    result = {**catalog, "version": 2, "movies": merged}
    if not args.check_only:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return {"titles": len(merged), "legacy": len(legacy), "imported": len(imported),
            "sourceLinks": sum(len(m["sources"]) for m in merged), "output": str(args.output),
            "dryRun": args.check_only, "collections": report}


def collections_defaultdict():
    return collections.defaultdict(list)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "imports/collections.json")
    parser.add_argument("--base", type=Path, default=ROOT / "data/catalog.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/catalog.json")
    parser.add_argument("--media-base-url", default="", help="Optional HTTPS URL prefix for imported images; omit for relative paths")
    parser.add_argument("--strict-missing", action="store_true", help="Fail if any enabled archive is absent")
    parser.add_argument("--prune-unlisted", action="store_true", help="Explicitly remove archived collections no longer in the manifest")
    parser.add_argument("--prune-unavailable", action="store_true", help="Explicitly discard previously imported records absent from the source files")
    parser.add_argument("--check-only", action="store_true", help="Validate and report; do not modify the catalog")
    args = parser.parse_args()
    if args.media_base_url and not args.media_base_url.startswith("https://"):
        parser.error("--media-base-url must use HTTPS")
    try:
        print(json.dumps(build(args), indent=2, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Import error: {exc}\n")


if __name__ == "__main__":
    main()
