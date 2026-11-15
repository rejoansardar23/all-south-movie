#!/usr/bin/env python3
"""Package the existing Southscreen interface and imported posters for AWS.

Never publishes Telegram HTML exports or original result.json files.
"""
import argparse
import json
import shutil
from pathlib import Path
from urllib.parse import urlsplit

from archive_paths import archive_folder

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".svg"}


def copy_media(source: Path, target: Path):
    count = 0
    if not source.is_dir():
        return count
    for item in source.rglob("*"):
        if not item.is_file() or item.suffix.lower() not in SUFFIXES:
            continue
        relative = item.relative_to(source)
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest)
        count += 1
    return count


def build(output: Path, skip_media=False, clean=True, site_url=''):
    output = output.resolve()
    if output.name != "dist" or output == ROOT:
        raise ValueError("Output must be a directory named dist; refusing to delete arbitrary folders")
    if clean and output.exists():
        if output == Path(output.anchor) or output == ROOT / "assets" or output == ROOT / "data":
            raise ValueError("Refusing to delete an important directory")
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    for filename in ("index.html",):
        index = (ROOT / filename).read_text(encoding="utf-8")
        if site_url:
            parsed = urlsplit(site_url)
            if (parsed.scheme != "https" or not parsed.hostname or parsed.username or
                parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
                raise ValueError("--site-url must be HTTPS origin only, e.g. https://www.example.com")
            url = site_url.rstrip("/") + "/"
            index = index.replace("https://rejoansardar23.github.io/all-south-movie/", url)
        (output / filename).write_text(index, encoding="utf-8")
    shutil.copytree(ROOT / "assets", output / "assets", dirs_exist_ok=True)
    (output / "data").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "data/catalog.json", output / "data/catalog.json")
    count = 0
    if not skip_media:
        count += copy_media(ROOT / "photos", output / "photos")
        manifest = json.loads((ROOT / "imports/collections.json").read_text(encoding="utf-8"))
        for collection in manifest.get("collections", []):
            name = collection["id"]
            if not name.replace("-", "").isalnum() or "/" in name:
                raise ValueError(f"Invalid collection name: {name}")
            folder = archive_folder(ROOT, collection)
            for media_dir in ("photos", "images"):
                count += copy_media(
                    folder / media_dir,
                    output / "imports" / name / media_dir
                )
    print(json.dumps({"output": str(output), "imagesCopied": count,
                      "sourceExportsIncluded": False, "skipMedia": bool(skip_media)}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--skip-media", action="store_true", help="Fast HTML/CSS/JS/catalog build only")
    parser.add_argument("--site-url", default="", help="HTTPS public domain for canonical and sharing metadata")
    args = parser.parse_args()
    build(args.output, skip_media=args.skip_media, site_url=args.site_url)


if __name__ == "__main__":
    main()
