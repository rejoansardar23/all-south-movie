# Southscreen 2.0 — development and preview

## Preview website

**Browser preview:** https://rejoansardar23.github.io/all-south-movie/preview/

The preview is published under `preview/` on the repository's existing **main-branch GitHub Pages** website. It uses its own `preview/index.html`, `preview/assets/app.js` and `preview/assets/site.css`, while sharing poster images and `data/catalog.json` from the root. It does not replace the production homepage.

The feature development branch is `feature/southscreen-2`. Update the preview snapshot deliberately after testing further feature commits; the `southscreen-2-preview` branch and RawGitHack service are not the supported browser preview.

## Product requirements

Southscreen is a lightweight Indian movie-discovery catalog that links to external providers. **Keep movie details simple.** The user does not want additional plot descriptions, introductions, cast biographies, directors, runtimes, or trailers. Do not rebuild the removed editorial workspace.

Display only the core existing movie fields (title, poster, release year, genres, recorded audio languages, recorded source-quality options) plus watchlist/Favorites and related titles. Source qualities and links are archive-derived, not independently verified. Do not suggest that opening a provider means a movie was played.

## Implemented

- [x] Separate development branch `feature/southscreen-2`.
- [x] Remove visible original-post and legacy archive links from the application.
- [x] Cinematic styling polish, accessible focus styles, improved mobile typography.
- [x] Search suggestions, keyboard interaction, basic title spelling aliases.
- [x] Tamil and Telugu audio discovery shelves.
- [x] Related movies ranked by genre, language, title type, and year.
- [x] Quality filters on existing external source links and more honest availability labels.
- [x] Browser-local Favorites and existing saved list.
- [x] No extra description, director, cast, runtime, trailer or editorial management fields.
- [x] JavaScript syntax, frontend invariants, catalog validation through GitHub Actions.
- [x] GitHub Pages `/preview/` files published separately from production index.
- [x] Preview HTTP smoke-check workflow created; see Actions for latest result.

## Architecture

- Root `index.html` + `assets/`: production website
- `preview/index.html` + `preview/assets/`: preview snapshot, deployed from main with GitHub Pages
- `data/catalog.json`: generated catalog shared by production and preview
- `photos/`: shared image assets
- `tools/build_catalog.py`: importer
- `tools/check_catalog.py`: validates source provenance and assets
- `tools/check_site.py`: validates frontend invariants
- `.github/workflows/preview-web-check.yml`: checks preview URLs over HTTPS

**Preview path details:** Because the preview is one directory below the site root, its JavaScript loads `../data/catalog.json`, and poster URLs point to `../photos/...`. Its CSS and app script load from `preview/assets/`. If files are copied to the preview snapshot after development changes, preserve those paths and update the HTML asset version query strings.

## Remaining priorities

1. Verify the GitHub Pages deployment via a real HTTP check and manual browser testing (desktop and mobile).
2. Add a **reported broken source** workflow with moderation, no embedded client write token or unauthorized probing.
3. Improve search keyboard accessibility, aliasing, quick filters, and zero-results handling.
4. Compress/reformat poster assets, measure actual Core Web Vitals, and remove unnecessary network/image costs.
5. Improve collections and recommendations based only on available, accurate metadata; do not invent view counts.
6. Ensure stable SEO for the browsing site, and add meaningful accessible metadata without creating new descriptive movie content.
7. Add an optional installable PWA and more robust local watchlist/favorites import/export.
8. Consider a secure backend only for features that truly need it.

## How to validate

On a full checkout:

```sh
node --check assets/app.js
python3 tools/check_site.py
python3 tools/check_catalog.py
python3 -m http.server 8000
```

Review the development version at `http://localhost:8000/` and compare against the live preview URL above. For a local test of preview paths, browse `http://localhost:8000/preview/` in a checkout of main containing preview assets.

**Do not merge the draft PR without review.** The original Telegram HTML and JSON export files are still public repository files despite links being hidden in the app; this is not access control. Only link to content you have permission to distribute or reference, and respect provider terms.

