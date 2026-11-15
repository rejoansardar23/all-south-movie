# Worldscreen — Cinema, worldwide.

A multilingual movie and series discovery website with Southscreen's established browsing experience, source selection, watchlist, Favorites, and responsive design. Worldscreen supports worldwide collections and language labels including **Hindi, English, Tamil, Telugu, Malayalam, Kannada**, and more when available in the uploaded archive.

**Development branch:** `feature/worldscreen-catalog-aws`

**Important:** The existing production GitHub Pages website still points to `main`; this work is a draft until catalog import and browser testing pass.

## Your latest upload is preserved

The newly uploaded archive is in `all bollywodd/`. Do **not** rename, remove, flatten, or reupload its `photos/`, `images/`, `messages*.html`, or `result.json` files. It is registered in `imports/collections.json` as `world-archive-01`. Our importer translates image paths to `imports/world-archive-01/photos/...` in the **generated catalog** only, while the original files remain untouched.

GitHub Actions can generate the merged catalog from this uploaded archive. Manually, from a full clone:

```powershell
python tools/build_multi_catalog.py --check-only
python tools/build_multi_catalog.py
python tools/check_catalog.py --require-import-media
python tools/build_site.py
```

The AWS package is built in `dist/`. It contains the Worldscreen website, the generated catalog, and normalized media directories. It explicitly **does not include** the original Telegram JSON or HTML exports.

## Current features

- Cinematic homepage with hero and poster shelves.
- World cinema discovery by language and genre.
- Combined title/year/genre/language/quality filters and autocomplete.
- External provider/source controls grouped by domain and recorded quality.
- My List, Favorites, recent titles, and related movie suggestions.
- Mobile-first layout and accessible keyboard interactions.

**No additional synopsis, cast, director, runtime, or trailer information is added.**

## Multi-archive and AWS deployment

See [AWS Deployment Guide](docs/AWS_DEPLOYMENT.md), [Collection Format](imports/README.md), and `aws/cloudfront-site.yaml`.

We have **not** created AWS resources, registered your domain or deployed a live AWS site yet. CloudFront and private S3 require your AWS account and billing approval. Only upload or distribute movie material you have rights to use.

## Legacy compatibility

Existing Southscreen saved lists remain compatible. The original `southscreen-list-v1` / Favorites storage keys and `southscreen-watchlist` import format are intentionally retained, so the branding change doesn't erase visitor preferences. Existing movie IDs remain unchanged. New archive IDs are namespaced.
