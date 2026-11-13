#!/usr/bin/env python3
"""Build a small, deduplicated catalogue from the original Telegram export.

No external services are queried. Text is data, never HTML. Promotional/social
links are excluded; the original export remains available for provenance.
Run from any directory: python tools/build_catalog.py
"""
import collections
import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
GENRES = {g.casefold(): g for g in (
    'Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime',
    'Documentary', 'Drama', 'Family', 'Fantasy', 'History', 'Horror', 'Musical',
    'Mystery', 'Romance', 'Sci-Fi', 'Sport', 'Thriller', 'War', 'Western')}
GENRES.update({'scifi': 'Sci-Fi', 'sci_fi': 'Sci-Fi', 'sci fi': 'Sci-Fi',
               'sports': 'Sport', 'biographical': 'Biography'})
SOCIAL = ('t.me', 'telegram.me', 'instagram.com', 'youtube.com', 'youtu.be',
          'whatsapp.com', 'facebook.com', 'play.google.com', 'twitter.com', 'x.com')


def normalize(text):
    return unicodedata.normalize('NFKC', text).replace('\u200b', '').replace('\xa0', ' ')


class ArchiveMap(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.page = ''
        self.entries = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div' and 'message default' in attrs.get('class', ''):
            self.current = int(attrs['id'].removeprefix('message'))
            self.entries[self.current] = {'page': self.page}
        if tag == 'img' and attrs.get('class') == 'photo' and self.current:
            self.entries[self.current]['thumbnail'] = attrs['src']


def get_links(message):
    links, seen, previous = [], set(), ''
    for entity in message.get('text_entities', []):
        part = normalize(entity.get('text', ''))
        if entity.get('type') in ('link', 'text_link'):
            url = entity.get('href', entity.get('text', '')).strip()
            parsed = urlsplit(url)
            host = (parsed.hostname or '').lower().removeprefix('www.')
            is_social = any(host == d or host.endswith('.' + d) for d in SOCIAL)
            is_image = bool(re.search(r'\.(?:jpg|jpeg|png|gif|webp)(?:$|/)', parsed.path, re.I)) or host == 'm.media-amazon.com'
            if parsed.scheme in ('https', 'http') and host and not is_social and not is_image and not parsed.username and url not in seen:
                # Captions use a quality/size label immediately before each URL.
                context = previous.rsplit('\n\n', 1)[-1][-100:] + ' ' + part[:40]
                qualities = re.findall(r'(?i)\b(2160p|1080p|720p|480p|360p|4k)\b', context)
                sizes = re.findall(r'(?i)\b(\d+(?:\.\d+)?\s*(?:GB|MB))\b', context)
                label = qualities[-1].lower() if qualities else (sizes[-1].upper().replace(' ', '') if sizes else 'Source link')
                if label == '4k':
                    label = '2160p'
                links.append({'label': label, 'url': url, 'host': host})
                seen.add(url)
        previous += part
    return links


def build():
    export = json.loads((ROOT / 'result.json').read_text())
    archive = ArchiveMap()
    for page in ('messages.html', 'messages2.html', 'messages3.html'):
        archive.page = page
        archive.feed((ROOT / page).read_text())
    grouped, skipped = {}, collections.Counter()
    for message in export['messages']:
        if message.get('type') != 'message':
            continue
        raw = message.get('text', '')
        text = normalize(raw if isinstance(raw, str) else ''.join(p if isinstance(p, str) else p.get('text', '') for p in raw))
        first_lines = [line.strip() for line in text.splitlines() if line.strip()][:3]
        title_match = None
        for line in first_lines:
            title_match = re.search(r'^(.+?)\s*\((19\d{2}|20\d{2})\)', line)
            if title_match:
                break
        if not title_match:
            skipped['no_title_and_year'] += 1
            continue
        title = title_match[1].strip()
        title = re.sub(r'^.*?\btitle\s*[:\-]\s*', '', title, flags=re.I)
        title = re.sub(r'^[^\w\u0900-\u097f]+|[^\w\u0900-\u097f!?]+$', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        if not title or len(title) > 120 or re.search(r'uploaded|join our|premium channel', title, re.I):
            skipped['announcement'] += 1
            continue
        sources = get_links(message)
        if not sources:
            skipped['no_movie_links'] += 1
            continue
        genre_line = re.search(r'(?im)genre\s*:\s*(.+)', text)
        genres = []
        if genre_line:
            for token in re.split(r'[|,#]+', genre_line[1]):
                candidate = token.strip().strip('#').casefold()
                if candidate in GENRES:
                    genres.append(GENRES[candidate])
                else:
                    for word in re.findall(r'[A-Za-z-]+', token):
                        if word.casefold() in GENRES:
                            genres.append(GENRES[word.casefold()])
        genres = sorted(set(genres))
        year = int(title_match[2])
        audio = re.search(r'(?im)audio\s*:\s*(.+)', text)
        audio_text = audio[1].upper() if audio else ''
        languages = [name for name, pattern in (
            ('Hindi', r'\bHINDI\b|\bHIN\b'), ('Tamil', r'\bTAMIL\b|\bTAM\b'),
            ('Telugu', r'\bTELUGU\b|\bTEL\b'), ('Malayalam', r'\bMALAYALAM\b|\bMAL\b'),
            ('Kannada', r'\bKANNADA\b|\bKAN\b'), ('English', r'\bENGLISH\b|\bENG\b'))
            if re.search(pattern, audio_text)]
        season = re.search(r'(?i)\bseason\s*(\d+)\b|\bS(\d{1,2})\b', '\n'.join(first_lines))
        if season and not re.search(r'(?i)\bseason\b|\bS\d{1,2}\b', title):
            title += ' — Season ' + next(v for v in season.groups() if v)
        kind = 'Series' if season or re.search(r'(?i)web.?series|\bseries\b', '\n'.join(first_lines)) else 'Movie'
        source = archive.entries.get(message['id'], {})
        poster = message.get('photo', '')
        if not poster.startswith('photos/'):
            skipped['no_poster'] += 1
            continue
        thumb = source.get('thumbnail', poster)
        key = re.sub(r'\W+', '', title.casefold()) + ':' + str(year)
        item = {
            'id': message['id'], 'title': title, 'year': year, 'type': kind,
            'genres': genres, 'languages': languages, 'poster': poster,
            'thumbnail': thumb, 'added': message['date'][:10],
            'reactions': sum(r.get('count', 0) for r in message.get('reactions', [])),
            'sources': sources, 'sourcePage': source.get('page', 'messages.html'),
            'sourceIds': [message['id']],
        }
        if key in grouped:
            older = grouped[key]
            item['sourceIds'] = older['sourceIds'] + item['sourceIds']
            item['reactions'] = max(older['reactions'], item['reactions'])
            item['genres'] = sorted(set(older['genres'] + item['genres']))
            item['languages'] = sorted(set(older['languages'] + item['languages']))
            # Keep the newest source for each provider and quality combination.
            seen = {(s['host'], s['label']) for s in item['sources']}
            seen_urls = {s['url'] for s in item['sources']}
            for src in older['sources']:
                if (src['host'], src['label']) not in seen and src['url'] not in seen_urls:
                    item['sources'].append(src)
                    seen.add((src['host'], src['label']))
                    seen_urls.add(src['url'])
        grouped[key] = item
    movies = sorted(grouped.values(), key=lambda m: (m['added'], m['id']), reverse=True)
    out = {'version': 1, 'name': 'Southscreen', 'updated': export['messages'][-1]['date'][:10],
           'sourceMessages': len(export['messages']), 'movies': movies}
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data/catalog.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(json.dumps({'titles': len(movies), 'sources': sum(len(m['sources']) for m in movies),
                      'genres': sorted({g for m in movies for g in m['genres']}),
                      'types': dict(collections.Counter(m['type'] for m in movies)),
                      'skipped': dict(skipped), 'bytes': (ROOT / 'data/catalog.json').stat().st_size}, indent=2))


if __name__ == '__main__':
    build()
