# Southscreen: 10,000+ Movie Import and AWS Hosting

**Branch:** `feature/southscreen-multi-archive-aws` (based on the existing Southscreen 2.0 work).

This upgrades the data pipeline, **not the UI design**. It retains the existing hero, movie cards, browse/search, genre/audio/year/quality filters, Favorites, My List, related titles, and external source buttons. It does not add cast, descriptions, directors, runtimes or trailers.

## 1. Clone the prepared branch on Windows

```powershell
cd "C:\Main Dev"
git clone --branch feature/southscreen-multi-archive-aws --single-branch https://github.com/rejoansardar23/all-south-movie.git Southscreen
cd .\Southscreen
```

The public GitHub repository already contains the development code and the manifest. Do not clone the old raw movie export folder as a second Git repository inside it.

## 2. Copy your different Telegram archives into isolated locations

The collection IDs are in `imports/collections.json`; the script will not allow an unregistered name.

First run without `-Execute` to inspect the source size and destination. For example, the Windows screenshot showed:

```powershell
.\tools\stage_collection.ps1 -Source "C:\Main Dev\all bollywoodd\all bollywood movie" -CollectionId bollywood-movies
.\tools\stage_collection.ps1 -Source "C:\Main Dev\all bollywoodd\all bollywood movie" -CollectionId bollywood-movies -Execute
```

Other examples (replace paths if your actual folder names differ):

```powershell
.\tools\stage_collection.ps1 -Source "C:\Main Dev\hollywood movie" -CollectionId hollywood-movies -Execute
.\tools\stage_collection.ps1 -Source "C:\Main Dev\bollywood web series" -CollectionId bollywood-web-series -Execute
.\tools\stage_collection.ps1 -Source "C:\Main Dev\all bollywoodd\all hollywoood webseries" -CollectionId hollywood-web-series -Execute
.\tools\stage_collection.ps1 -Source "C:\Main Dev\ullu and nixs indian web series" -CollectionId ullu-nix-series -Execute
```

Each copy preserves its own `result.json`, `messages*.html`, `photos/`, `images/`, etc. The contents are NEVER merged into the same `photos` directory, so duplicate filenames do not overwrite one another. The source directories remain untouched.

**Before the first import**, keep a backup of the existing catalog and do not manually edit it. Importer IDs for new collections are stable JavaScript-safe integers based on the collection ID and source message ID. Existing Southscreen IDs stay unchanged, so previously saved movies keep working. Identical titles in **different collections are deliberately left separate**, because two movies can share a name/year; repeated posts within a single collection are combined.

## 3. Build the unified catalog

Install Python 3.9+ (the scripts require the standard library only). In the cloned repository:

```powershell
python tools/build_multi_catalog.py --check-only
python tools/build_multi_catalog.py
python tools/check_catalog.py
python tools/check_catalog.py --require-import-media
node --check assets/app.js
node tools/check_runtime.js
```

The `--require-import-media` check should pass on your Windows staging computer before the first AWS upload. It will intentionally fail on CI or a fresh clone without locally copied media. The importer reads `data/catalog.json` to preserve original titles and IDs. It adds entries only for successfully imported source collections. Rerunning it is idempotent: it replaces the previous imported records for a collection rather than duplicating them. If source images have not been copied or are excluded from a new clone, previously imported records are preserved, not silently deleted.

**Important:** The `--prune-unlisted` and `--prune-unavailable` flags are explicit deletion options; do not use them during normal imports.

Generated new poster paths look like `imports/bollywood-movies/photos/photo_1.jpg`. Another `imports/hollywood-movies/photos/photo_1.jpg` is a distinct file. The UI accepts both, retaining the same cards and source buttons.

If you want the imported image URLs to point to a dedicated media domain instead of same-host paths, use `--media-base-url https://media.example.com` on a fresh import. Default is relative URLs, recommended for hosting HTML and media on the same CloudFront distribution.

## 4. What to push to GitHub

`imports/.gitignore` deliberately keeps large media in your working folder but excludes those media files from Git. This avoids growing a Git repository beyond the GitHub limits as you add 10,000+ posters. *Your local importer still sees those files.*

Commit the generated catalog, source archive metadata, and the manifest after reviewing them:

```powershell
git status
git add data/catalog.json imports/collections.json
git add imports/bollywood-movies imports/hollywood-movies imports/bollywood-web-series imports/hollywood-web-series imports/ullu-nix-series
git status
git commit -m "Import additional movie collections"
git push origin feature/southscreen-multi-archive-aws
```

This intentionally includes `result.json` / `messages*.html` if you added them. **Do not push them if they contain private information, credentials, unauthorized links, or content you cannot distribute**. To keep private exports off public GitHub, do not `git add` them; instead keep local backups and push just `data/catalog.json` plus the scripts.

GitHub limits include a 100 MiB maximum for individual Git objects and a 2 GiB push-size limit. This workflow excludes large images and videos intentionally. Avoid Git LFS unless you have confirmed a budget and usage plan.

## 5. Preview locally before AWS

From the root:

```powershell
python -m http.server 8000
```

Open `http://localhost:8000/`. Posters from the imported archives work because their `imports/<collection>/photos` folders exist in this working copy. New movie source buttons keep their original external destinations.

## 6. Prepare the public AWS upload package

The packaging script copies the existing website and only the media required to serve it. It **does not publish** raw Telegram HTML exports or `result.json` publicly on S3:

```powershell
python tools/build_site.py
```

This creates `dist/` with `index.html`, `assets/`, `data/catalog.json`, legacy root `photos/` and each new `imports/<collection>/photos/` and `images/`. The `dist/` folder is not committed to Git.

For a fast code-only build (no images), use `python tools/build_site.py --skip-media`. Only deploy such a build if the images are **already** on S3. The deployment script does not delete old S3 objects.

## 7. AWS prerequisites

You need:
- AWS account with billing enabled and AWS CLI v2 configured using SSO or appropriately scoped credentials.
- A unique S3 bucket name and a chosen AWS region (for example `ap-south-1`).
- Budget alerts configured in AWS Billing **before creating resources**.
- A domain you control if you want a custom hostname. The first deployment can use the generated `*.cloudfront.net` address for testing.

Do not paste AWS access keys into ChatGPT or commit them to your repo.

## 8. Create S3 + CloudFront (without custom domain first)

The CloudFormation template `aws/cloudfront-site.yaml` creates:
- Encrypted, private S3 bucket with public access fully blocked
- CloudFront distribution with HTTPS and compression
- Origin Access Control (OAC), allowing only that distribution to read S3 objects
- Outputs for the bucket name, distribution ID and CloudFront hostname

From PowerShell, replace the bucket name with one you choose:

```powershell
aws cloudformation validate-template --region ap-south-1 --template-body file://aws/cloudfront-site.yaml
aws cloudformation deploy --region ap-south-1 --stack-name southscreen-site --template-file aws/cloudfront-site.yaml --parameter-overrides SiteBucketName=YOUR-UNIQUE-S3-BUCKET
aws cloudformation describe-stacks --region ap-south-1 --stack-name southscreen-site --query "Stacks[0].Outputs" --output table
```

Use the returned `BucketName`, `CloudFrontDistributionId`, and `CloudFrontDomainName`.

This creates billable AWS infrastructure in your account. It is not free by default, even if a promotional trial or credits apply.

## 9. Upload the complete website and poster collection

The included deployment helper first performs a **dry run**:

```powershell
.\aws\deploy.ps1 -Bucket "YOUR-UNIQUE-S3-BUCKET" -DistributionId "CLOUDFRONT-DISTRIBUTION-ID"
```

If the list of files and destination look correct, actually deploy:

```powershell
.\aws\deploy.ps1 -Bucket "YOUR-UNIQUE-S3-BUCKET" -DistributionId "CLOUDFRONT-DISTRIBUTION-ID" -Execute
```

It uploads `dist/` to S3 and creates a CloudFront invalidation for the website's HTML/CSS/JavaScript/catalog. It does **not** upload the raw source exports or remove old S3 media. Open the output CloudFront hostname over HTTPS when deployment finishes.

## 10. Connect your custom domain

1. Request an ACM certificate for `www.yourdomain.com` in **`us-east-1`** (mandatory for CloudFront). Choose DNS validation and finish the certificate's DNS validation process.
2. Update the same stack by supplying `DomainName=www.yourdomain.com` and `CertificateArn=arn:aws:acm:us-east-1:...` alongside the unchanged `SiteBucketName`.
3. Add a DNS record pointing `www.yourdomain.com` to the returned CloudFront domain: a CNAME at most third-party registrars, or a Route 53 Alias when using Route 53. For an apex/root domain use DNS ALIAS/ANAME support or Route 53 Alias instead of a conventional CNAME.
4. Wait for certificate validation and CloudFront distribution deployment, then test HTTPS.

Example (substitute YOUR real values):

```powershell
aws cloudformation deploy --region ap-south-1 --stack-name southscreen-site --template-file aws/cloudfront-site.yaml --parameter-overrides SiteBucketName=YOUR-UNIQUE-S3-BUCKET DomainName=www.yourdomain.com CertificateArn=arn:aws:acm:us-east-1:ACCOUNT:certificate/CERTIFICATE-ID
```

You do **not** need EC2, a paid server, or a database for this static movie-discovery site. If you later host licensed videos, that requires a different storage, streaming, compliance and bandwidth plan.

## 11. Known limits and safe rollout

- The existing `main` production website is unchanged. This branch needs QA before a merge.
- AWS has **not** been deployed from this chat: no AWS account or domain access was provided.
- The multi-importer supports archive exports structured like the currently supported Southscreen `result.json`; unusual or changed Telegram export formats need specific fixtures before promising 100% import coverage.
- Source links and quality labels remain *archive metadata*, not verified availability. The importer never bypasses a provider's restrictions or obtains private content.
- Do not import/publish film artwork or movie material without appropriate rights.
- Start with **one** archive, verify count and poster paths, then add the other archives.
