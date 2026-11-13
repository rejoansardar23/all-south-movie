# Southscreen 2.0 — developer roadmap

This document is the source of truth for work on the `feature/southscreen-2` branch. **Do not merge to `main` until CI and manual mobile/desktop smoke tests pass.** The production website uses GitHub Pages from `main`.

## Product definition

Southscreen is currently an **Indian cinema discovery catalog**, not a movie-hosting or streaming service. Existing provider URLs open in a new browser tab and may be expired or require sign-in. Never pretend that clicking an external link confirms a movie was watched, and never misrepresent a label such as 1080p as a verified file property.

## Architecture

- `index.html` — page shell, header search, modal dialogs, accessible navigation
- `assets/app.js` — catalog state, hash routing, client-side search, movie dialogs, source links, browser watchlist
- `assets/site.css` — responsive presentation
- `data/catalog.json` — generated archive-derived metadata and source references
- `tools/build_catalog.py` — extraction and deduplication from the Telegram export
- `tools/check_catalog.py` — provenance, URL and asset assertions
- `tools/check_site.py` — website smoke checks
- `messages*.html`, `result.json`, `photos/` — legacy source assets (still public while present in the published repository)

The site's watchlist and recently opened items currently live in `localStorage`. No account system or server-side playback state exists.

## Implemented on the 2.0 branch

- [x] Development branch isolated from production.
- [x] Remove visible legacy archive navigation from the header/footer/About/error flow and keep movie-level original-post links removed.
- [x] Inline movie title autocomplete in the header with keyboard access, using existing catalog data only.
- [x] Add movie shelves for titles labeled with Telugu or Tamil audio when present in catalog.
- [x] Filter external source links by labeled quality, keeping provider groups visible only when relevant.
- [x] Distinguish **recorded source links** from verified availability; sort quality buttons consistently.
- [x] Improve similar-movie ranking using genre, language, type and approximate release year.
- [x] Basic page canonical / Open Graph URL metadata.
- [x] Add source-focused CSS and static checks.
- [x] Personal favorites stored locally, with Favorites filtering and a homepage shelf.
- [x] Common title spelling aliases in browse and autocomplete.
- [x] Editorial draft workspace at `admin/editor.html` (local edits, JSON import/export only).
- [x] Reviewed metadata layer at `data/curated.json` with safe optional synopsis, director, cast, runtime and official YouTube trailer display.
- [x] Validate curated metadata in CI and automatically mirror the development branch into the `southscreen-2-preview` branch for the browser preview.

## Next: Phase 1 — reliability and content correctness

- [ ] Verify the deployed GitHub Pages site after every production deploy. Check published `index.html` / JavaScript versions rather than assuming a commit was published.
- [ ] Manual browser smoke test at mobile 375px, tablet 768px, desktop 1440px (catalog load, search, keyboard, quality filter, navigation, watchlist, dialogs, reduced motion).
- [ ] Implement visitor reports for broken external links through a moderated, spam-resistant backend or a GitHub issue workflow (never place write credentials in client code).
- [ ] Audit external links and take-down process. Availability statuses require a verification timestamp, not guesswork.
- [ ] Evaluate legal rights for images, promotional material and third-party movie sources before public expansion.

## Phase 2 — interface and discovery

- [ ] Stronger responsive hero and card detail design, poster aspect-ratio and small-screen text improvements.
- [ ] Search aliases, typos and transliterations (e.g. Baahubali / Bahubali) using a curated alias list.
- [ ] Better catalog categories and discoverability without invented popularity metrics.
- [ ] Larger, accessible mobile targets and complete screen-reader/keyboard audits.
- [ ] Populate accurate, licensed or originally written synopses, cast, director, runtime and verified official trailers via the editorial workspace. The metadata fields are implemented; the content still needs editorial review.
- [ ] Search/filter URL and dialog history test coverage in a real browser.

## Phase 3 — publishing, performance and SEO

- [ ] Measure Core Web Vitals on the published site; optimize poster variants and caching with evidence.
- [ ] Produce crawlable movie pages with conventional URLs, per-movie metadata, sitemap and only truthful schema.org Movie structured data.
- [ ] Add curated content workflows and staged catalog releases via reviewed GitHub pull requests.
- [ ] Move beyond the browser-only editorial workspace to a secure multi-user admin application after deciding on authentication, roles and backend storage. Keep secrets server-side.
- [ ] Add staging preview/deploy checks before merging.

## Phase 4 — optional advanced features

- [ ] Private watchlist sync across devices (requires secure accounts/backend).
- [ ] Personalized recommendations based on opt-in interactions, never falsely claim watched state.
- [ ] Reviews/ratings only with moderation, anti-spam and privacy controls.
- [ ] Progressive Web App/offline metadata cache with explicit update behavior.
- [ ] Licensed video playback integration only if rights and hosting are obtained.

## Contributing

1. Branch from `feature/southscreen-2`; keep changes small and scoped.
2. Avoid manually editing `data/catalog.json`; update its source / importer when necessary.
3. Run:
   ```sh
   node --check assets/app.js
   python3 tools/check_site.py
   python3 tools/check_catalog.py
   ```
4. Preview over HTTP: `python3 -m http.server 8000`, then open `http://localhost:8000`.
5. Open a pull request with desktop/mobile screenshots, test results and any data/provenance changes.
6. Keep `main` as the reviewed release branch. Changes on `feature/southscreen-2` are not automatically published to the production URL.

## Limits and security notes

Removing links to original posts from the UI does **not** make old `messages*.html` or `result.json` private. GitHub Pages does not provide file-level access control. To withhold source exports from public access, remove them from the published build and host authoring inputs separately.

The catalog contains archive-derived source labels and URLs, not independently validated video availability. Respect provider terms, copyright, user privacy and regional laws. Do not use hidden or unlicensed streams.

## Browser preview (development only)

Open [Southscreen 2.0](https://raw.githack.com/rejoansardar23/all-south-movie/southscreen-2-preview/index.html) to preview static files through RawGitHack. This is an external third-party host and not a separate GitHub Pages deployment. The `southscreen-2-preview` mirror is kept up-to-date by `.github/workflows/update-preview.yml` when GitHub Actions permissions allow it. Cache propagation can take a few minutes.

Open the [editorial workspace preview](https://raw.githack.com/rejoansardar23/all-south-movie/southscreen-2-preview/admin/editor.html) to prepare reviewed metadata. Edits remain in the current browser until the downloaded `curated.json` is committed to `data/curated.json`. This static editor has **no server-side admin authentication and no publishing privileges**.

Current production GitHub Pages should remain on the default `main` branch. Never switch the production Pages source merely to preview development changes.

