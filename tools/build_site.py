#!/usr/bin/env python3
"""Package the existing Southscreen interface and imported posters for AWS.

Never publishes Telegram HTML exports or original result.json files.
"""
import argparse
import json
import shutil
from pathlib import Path

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


def build(output: Path, skip_media=False, clean=True):
    output = output.resolve()
    if output.name != "dist" or output == ROOT:
        raise ValueError("Output must be a directory named dist; refusing to delete arbitrary folders")
    if clean and output.exists():
        if output == Path(output.anchor) or output == ROOT / "assets" or output == ROOT / "data":
            raise ValueError("Refusing to delete an important directory")
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    for filename in ("index.html",):
        shutil.copy2(ROOT / filename, output / filename)
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
            for media_dir in ("photos", "images"):
                count += copy_media(
                    ROOT / "imports" / name / media_dir,
                    output / "imports" / name / media_dir
                )
    print(json.dumps({"output": str(output), "imagesCopied": count,
                      "sourceExportsIncluded": False, "skipMedia": bool(skip_media)}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--skip-media", action="store_true", help="Fast HTML/CSS/JS/catalog build only")
    args = parser.parse_args()
    build(args.output, skip_media=args.skip_media)


if __name__ == "__main__":
    main()
