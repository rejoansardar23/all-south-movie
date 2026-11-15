# Worldscreen import and launch validation — 15 November 2026

## What was imported

Source folder: `all bollywodd/` (kept in place; no file renames), registered as `world-archive-01`.

- Existing Southscreen titles: **1,768**
- Imported titles from the new archive: **2,432**
- Combined titles: **4,200**
- Combined external provider links: **14,771**
- Imported archive raw messages: **3,823**
- Skipped posts with no parseable title/year: **226**
- Skipped posts with no usable source links: **6**
- Other difference is non-movie posts and within-archive deduplication; don't equate Telegram message counts with unique films.

Reported audio-language labels (titles can count in multiple languages):
- Hindi: **3,883**
- English: **47**
- Tamil: **342**
- Telugu: **339**
- Malayalam: **131**
- Kannada: **78**

These are archive-derived **audio labels**, not an independently validated inventory of film production countries or guaranteed streaming language options. An empty category isn't filled with invented entries.

## Implemented UI changes

Working name: **Worldscreen — Cinema, Worldwide**. Main navigation, cinematic posters, search, filters, sources, related suggestions, Favorites, and My List are retained from Southscreen 2.0. Multilingual discovery chips and language shelves are added. No movie synopses, cast, director, runtime, introductions or trailers are added.

Existing movie IDs, hash links, browser-local list keys and watchlist import format are intentionally retained to protect previous visitors' preferences.

## Verified

- [x] Parse actual uploaded `result.json` and `messages*.html` pages.
- [x] Detect collisions and retain existing movie IDs.
- [x] Verify imported poster references against their source folder.
- [x] Build AWS package `dist/` with normalized poster directories and without source export JSON/HTML.
- [x] Test package in headless Chromium against a local HTTP server: **96 rendered poster cards**, first poster image loaded, source modal and quality controls working, autocomplete working.
- [x] Validate CloudFormation S3 + CloudFront OAC template in the existing CI workflow.
- [ ] User review of final visual appearance on desktop/mobile.
- [ ] Real AWS S3/CloudFront deployment with account permissions and chosen domain.
- [ ] Review licensing and content rights for published posters and external links.

### Browser proof

GitHub Actions run: https://github.com/rejoansardar23/all-south-movie/actions/runs/43732388289

The workflow saves a screenshot artifact named `worldscreen-browser-homepage` on the Actions page.

### Before a commercial launch

**World Screen** is also the name of an established entertainment publication. Treat "Worldscreen" as a **working name only** until the owner chooses and clears their actual product name and domain. Do not assume a domain or trademark is available.

The raw archive HTML and JSON files already pushed to the public GitHub repository remain publicly accessible there even if AWS packaging excludes them. Review those files for personal information and rights before publishing the AWS website.

For AWS steps, see `docs/AWS_DEPLOYMENT.md`.
