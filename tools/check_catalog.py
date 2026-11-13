#!/usr/bin/env python3
"""Check catalog provenance and links without contacting video providers.

Run in a full checkout with `python3 tools/check_catalog.py`.
For a partial checkout, --paths accepts a JSON array of repository paths.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paths', type=Path)
    args = parser.parse_args()
    known_paths = set(json.loads(args.paths.read_text())) if args.paths else None
    export = json.loads((ROOT / 'result.json').read_text())
    catalog = json.loads((ROOT / 'data/catalog.json').read_text())
    original = {m['id']: m for m in export['messages']}
    errors, ids, source_count = [], set(), 0
    for movie in catalog['movies']:
        mid = movie['id']
        if mid in ids:
            errors.append(f'Duplicate movie ID: {mid}')
        ids.add(mid)
        if not movie['title'].strip() or not 1900 <= movie['year'] <= 2099:
            errors.append(f'Invalid title or year: {mid}')
        if not movie['sourceIds'] or mid not in movie['sourceIds']:
            errors.append(f'Missing current source ID: {mid}')
        allowed_urls = set()
        for source_id in movie['sourceIds']:
            if source_id not in original:
                errors.append(f'Unknown source message: {mid}/{source_id}')
                continue
            for entity in original[source_id].get('text_entities', []):
                if entity.get('type') in ('link', 'text_link'):
                    allowed_urls.add(entity.get('href', entity.get('text', '')).strip())
        for field in ('poster', 'thumbnail'):
            path = movie[field]
            if not re.fullmatch(r'photos/[A-Za-z0-9_@.() -]+\.(?:jpg|jpeg|png|webp)', path, re.I):
                errors.append(f'Invalid image path: {mid}/{path}')
            exists = path in known_paths if known_paths is not None else (ROOT / path).is_file()
            if not exists:
                errors.append(f'Missing image: {mid}/{path}')
        seen = set()
        for source in movie['sources']:
            source_count += 1
            url = source['url']
            parsed = urlsplit(url)
            if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
                errors.append(f'Unsafe source URL: {mid}')
            if url not in allowed_urls:
                errors.append(f'Source URL not in original movie posts: {mid}')
            if url in seen:
                errors.append(f'Duplicate source URL: {mid}')
            seen.add(url)
            if re.search(r'\.(?:jpg|jpeg|png|gif|webp)$', parsed.path, re.I):
                errors.append(f'Image incorrectly included as video source: {mid}')
        if not movie['sources']:
            errors.append(f'No source links: {mid}')
        if movie['sourcePage'] not in ('messages.html', 'messages2.html', 'messages3.html'):
            errors.append(f'Unknown original page: {mid}')
    if errors:
        print('\n'.join(errors))
        raise SystemExit(f'{len(errors)} catalog checks failed')
    print(f'PASS: {len(ids):,} unique titles, {source_count:,} original source links, '
          f'{len(ids) * 2:,} image references; all checks passed.')


if __name__ == '__main__':
    main()
