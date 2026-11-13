#!/usr/bin/env python3
"""Validate optional reviewed editorial metadata without altering archive sources."""
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
catalog = json.loads((ROOT / "data/catalog.json").read_text(encoding="utf-8"))
curated = json.loads((ROOT / "data/curated.json").read_text(encoding="utf-8"))
ids = {str(movie["id"]) for movie in catalog["movies"]}
allowed = {"synopsis", "director", "cast", "runtime", "trailer"}
hosts = {"youtube.com", "www.youtube.com", "youtu.be", "www.youtube-nocookie.com"}
errors = []
if curated.get("version") != 1 or not isinstance(curated.get("movies"), dict):
    errors.append("Expected curated.json version=1 with object movies")
else:
    for key, entry in curated["movies"].items():
        if key not in ids:
            errors.append(f"Unknown movie ID {key}")
        if not isinstance(entry, dict):
            errors.append(f"{key}: expected object record")
            continue
        for field in entry:
            if field not in allowed:
                errors.append(f"{key}: unsupported field {field}")
        for field, max_len in (("director", 180), ("synopsis", 1400)):
            if field in entry and (not isinstance(entry[field], str) or len(entry[field]) > max_len):
                errors.append(f"{key}: invalid {field}")
        if "runtime" in entry and (
            type(entry["runtime"]) is not int or not 1 <= entry["runtime"] <= 600
        ):
            errors.append(f"{key}: runtime must be integer minutes, 1 to 600")
        if "cast" in entry:
            cast = entry["cast"]
            if (not isinstance(cast, list) or len(cast) > 30 or
                any(not isinstance(name, str) or not name.strip() or len(name) > 120 for name in cast)):
                errors.append(f"{key}: cast must be a list of up to 30 names")
        if "trailer" in entry:
            trailer = entry["trailer"]
            if not isinstance(trailer, str) or len(trailer) > 400:
                errors.append(f"{key}: trailer must be a short URL")
            else:
                parsed = urlsplit(trailer)
                if parsed.scheme != "https" or parsed.hostname not in hosts or parsed.username or parsed.password:
                    errors.append(f"{key}: trailer must link to HTTPS YouTube")
if errors:
    print("\n".join("FAIL: "+err for err in errors))
    raise SystemExit(1)
print(f"PASS: {len(curated['movies'])} curated movie records validated")
