#!/usr/bin/env python3
"""Small static-site smoke checks. Use with node --check and check_catalog.py."""
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "index.html").read_text(encoding="utf-8")
app = (ROOT / "assets/app.js").read_text(encoding="utf-8")
css = (ROOT / "assets/site.css").read_text(encoding="utf-8")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a":
            self.links.append(attrs.get("href", ""))


parser = PageParser()
parser.feed(html)
errors = []
expected_ids = {
    "main", "movie-dialog", "about-dialog", "search", "search-form",
    "search-suggestions", "toast"
}
if not expected_ids.issubset(parser.ids):
    errors.append("Required DOM element missing: " + str(sorted(expected_ids - set(parser.ids))))
if len(parser.ids) != len(set(parser.ids)):
    errors.append("Duplicate id attributes in index.html")
if any(link.startswith("messages") and "archive=1" in link for link in parser.links):
    errors.append("Legacy archive link remains in the public interface")
if "View original post" in app or "View original post" in html:
    errors.append("Original post link is exposed")
if 'href="messages.html?archive=1"' in app:
    errors.append("Archive fallback navigation is exposed")
if 'role="combobox"' not in html or "function updateSuggestions()" not in app:
    errors.append("Search suggestion UI or handler missing")
if ".search-suggestions" not in css:
    errors.append("Search suggestion styles missing")
if "data-source-label" not in app or "case'source-quality':" not in app:
    errors.append("Source quality filtering missing")
if "source-quality-button" not in css:
    errors.append("Source quality styles missing")
if 'rel="noopener noreferrer"' not in app:
    errors.append("External source links lack rel protection")
if not (ROOT / "data/catalog.json").is_file():
    errors.append("Catalog JSON missing")
if "https://rejoansardar23.github.io/all-south-movie/" not in html:
    errors.append("Site canonical URL missing")
if errors:
    for err in errors:
        print("FAIL:", err)
    raise SystemExit(1)
print("PASS: static HTML, search, source UI, navigation, metadata and key assets")
