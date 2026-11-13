# All South Hindi Dubbed Movies

A static website for the existing three-page HTML archive.

## GitHub Pages setup

1. Open [Settings → Pages](https://github.com/rejoansardar23/all-south-movie/settings/pages).
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select the **main** branch and **/(root)** folder, then click **Save**.
4. Wait for the **pages build and deployment** run to complete.

Once GitHub Pages is enabled and deployment succeeds, the website address is:

https://rejoansardar23.github.io/all-south-movie/

## Files

- `index.html` opens the first archive page and preserves query strings and message anchors.
- `messages.html`, `messages2.html`, and `messages3.html` contain the original archive.
- `css/`, `js/`, `images/`, and `photos/` contain its existing assets.
- `.nojekyll` tells GitHub Pages to serve the repository as plain static files.
- `result.json` is the original structured export.

No install, build command, server, or paid domain is required. Updates to the configured publishing branch are published by GitHub Pages.

The website displays the content and external links present in the original export; availability of third-party destinations is independent of this repository.
