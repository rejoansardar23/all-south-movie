#!/usr/bin/env python3
"""Safe source folders for imported movie archives, including existing root uploads."""
from pathlib import Path
import re

COLLECTION_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
RESERVED = {".git", ".github", "assets", "data", "aws", "tools",
            "photos", "images", "preview", "dist", "imports", "css", "js"}


def archive_folder(root: Path, entry: dict) -> Path:
    """Allow imports/<collection> or an explicitly registered root upload directory."""
    name = entry.get("id")
    supplied = entry.get("path")
    if not isinstance(name, str) or not COLLECTION_RE.fullmatch(name):
        raise ValueError(f"Invalid collection ID: {name!r}")
    if not isinstance(supplied, str) or not supplied.strip():
        raise ValueError(f"Unsafe archive location for {name}: missing path")
    rel = Path(supplied)
    if rel.is_absolute() or any(part in ("..", ".") for part in rel.parts):
        raise ValueError(f"Unsafe archive location for {name}: {supplied!r}")
    if rel.parts == ("imports", name):
        return (root / rel).resolve()
    if len(rel.parts) == 1 and rel.name not in RESERVED and not rel.name.startswith("."):
        return (root / rel.name).resolve()
    raise ValueError(f"Unsafe archive location for {name}: {supplied!r}")
