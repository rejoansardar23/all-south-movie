# Southscreen — Cinema, collected.

A cinematic, responsive movie-discovery website built from the existing **All South Hindi dubbed movies** export.

**Website:** https://rejoansardar23.github.io/all-south-movie/

## Features

- Featured-movie carousel, poster shelves, handpicked titles, and genre collections.
- Instant search across titles, years, genres, and available audio languages.
- Combined genre, year, language, quality, and movie/series filters.
- Sort by title, release year, archive addition date, or original archive reactions.
- A paginated catalog: 48 cards initially, with a working Show more control.
- Movie details, grouped provider/quality links, related titles, and shareable movie URLs.
- Persistent browser watchlist with JSON export/import and synchronization between tabs.
- Recently opened sources and a random movie picker.
- Mobile bottom navigation, responsive layouts, keyboard search shortcut (`/`), native modal focus handling, and reduced-motion support.
- Old `messages*.html` bookmarks open the new interface. Add `?archive=1` to see the original export.

The current catalog contains **1,768 deduplicated titles and 6,794 source links**. Titles, years, genre/audio labels, poster images, and provider links come from the original posts. They are not independently verified movie metadata. The importer excludes promotional/social and image-only links.

## Playback and storage

This is a static discovery website. Existing provider pages open in new tabs; they are not direct media URLs and are not passed to a pretend embedded video player. Providers may require their own app/sign-in, and older links can expire. There is no video-hosting backend or user account system.

Watchlists and recently opened titles are stored only in the visitor's browser. Export a watchlist to back it up or import it on another device. Clearing browser storage clears these local lists. Imported lists are validated and merged; they do not overwrite the current list.

## Structure

| Path | Purpose |
| --- | --- |
| `index.html` | Application shell and navigation |
| `assets/app.js` | Catalog browsing, routing, dialogs, watchlists, and source links |
| `assets/site.css` | Responsive dark theme |
| `assets/favicon.svg` | Southscreen mark |
| `data/catalog.json` | Deduplicated catalog used by the website |
| `tools/build_catalog.py` | Rebuilds the catalog from the original export |
| `tools/check_catalog.py` | Checks catalog provenance, local image references, and safe links |
| `messages*.html`, `result.json`, `photos/`, `images/`, `css/` | Preserved original export |
| `js/script.js` | Original archive behavior plus legacy-URL redirection |

## Update the catalog

Add or update the original export and its images, then run with Python 3.9+:

```sh
python3 tools/build_catalog.py
python3 tools/check_catalog.py
```

Commit the changed export, images, and generated `data/catalog.json`. No API key, package installation, bundler, or paid domain is needed. Fonts load from Google Fonts with system fallbacks.

Movie IDs are the newest merged source-message IDs. The application also resolves previous message IDs through `sourceIds`, so existing saved titles and original message bookmarks can survive a rebuild.

## Preview locally

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000/`. Use HTTP rather than opening `index.html` directly because the application fetches its catalog.

## GitHub Pages

The configured publishing source is **main / (root)**. Commits to `main` are published by GitHub Pages. `.nojekyll` keeps the repository as plain static files.

## Validation

Before publication, JavaScript syntax and catalog provenance/asset references were checked. Desktop browser checks covered the homepage, movie details, saved-list persistence after reload, search, combined year/language filters, empty results, pagination from 48 to 96 cards, and title sorting. Mobile visual checks and browser-based import/export checks were interrupted by preview-session expiry and a subsequent browser access restriction; those checks are not claimed as passed.
