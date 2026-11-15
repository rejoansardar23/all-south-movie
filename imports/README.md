# Southscreen collection imports

Drop each Telegram export into a separate directory, **never merge folders with identical names**.

- `imports/bollywood-movies/result.json`, `messages.html`, `messages2.html`, `messages3.html`, `messages4.html`, `photos/`, `images/`
- `imports/hollywood-movies/...`
- `imports/bollywood-web-series/...`
- `imports/hollywood-web-series/...`
- `imports/ullu-nix-series/...`

The five collection names are configured in `imports/collections.json`. Add other collections using unique lowercase IDs (`a-z`, digits, hyphens). The existing South Hindi catalog is already in the root; **do not import it a second time unless you intentionally want duplicates**.

Use `tools/stage_collection.ps1` to copy a source folder to the right location, excluding nested `.git` and without deleting the original. Then run:

```powershell
python tools/build_multi_catalog.py --check-only
python tools/build_multi_catalog.py
python tools/check_catalog.py
```

The importer preserves the original 1,768 catalog entries, their IDs, and all current UI functionality. New movie IDs are unique across collections, even when the original Telegram messages have identical numbers. Two collections may both contain `photos/photo_1.jpg` because their paths are namespaced.

**IMPORTANT — before `git add`:** `imports/.gitignore` intentionally excludes photos, images and other media. The files remain on your computer so imports work, but `git push` does not upload them. Upload those media files to S3 instead (see `docs/AWS_DEPLOYMENT.md`). Committing the raw `result.json` and `messages*.html` exports to a public repository makes their contents public; carefully review or omit them if they contain private data, unwanted source links, or rights-restricted material. Do not commit actual movie video files.

If you clone the repository again later, `result.json` and `messages*.html` should be present if you committed them, but ignored media will need to be copied from local backups or fetched from S3. The importer safely preserves previously generated movies when a configured archive is absent; it will not silently delete their catalog entries.

For 10,000+ titles, put images in S3 + CloudFront and keep GitHub mostly text and source code. GitHub enforces size limits; a successful import is not proof that every source URL still works or that you have rights to distribute media.
