# Movie & Series Vault — Searchable Archive

A responsive, searchable catalog built from the archived HTML exports already in this repository. The original HTML, JSON, CSS, JS and photo files are preserved.

## Collections

The homepage at [index.html](index.html) now loads **14 HTML pages** from four collections:

| Collection | Folder | HTML pages |
|---|---|---|
| Hollywood Movies | repository root | messages.html through messages6.html (6) |
| South Hindi Dubbed Movies | All South Hindi dubbed movies/ | messages.html through messages3.html (3) |
| Hollywood Web Series | all hollywood webseries/ | messages.html through messages3.html (3) |
| Bollywood Web Series | bollywood web series/ | messages.html and web series.html (2) |

The entry named **all bollywood movie** is currently a Git *gitlink* (submodule-style commit reference, mode 160000), not an ordinary directory containing committed HTML pages. It cannot be included until its file contents are made accessible to the website.

### Features

- Search by title, release year, genre, audio, and collection.
- Filter by collection, genre, year, and version (all, originals, updates, latest per title).
- Sort alphabetically, by release year or by archived post date.
- Show local poster thumbnails and original source post details.
- Preserve repeated entries; within each collection and title+year group, label the first **Original**, then **Updated 1**, **Updated 2**, etc. These labels mean repeated *posts*, not independently verified changes to any files or links.
- Responsive desktop and phone layout, with progressive result loading.

## Preview privately on your computer

You need an HTTP server because web browsers normally block file-based fetch requests when opening index.html as file://.

Clone the repository, then from its root run:

~~~bash
python -m http.server 8000
~~~

On Windows, if python does not work, use:

~~~bash
py -m http.server 8000
~~~

Visit **http://localhost:8000/**, wait for the source files to load, and test each collection using the Collection dropdown. On slower devices, the archive may take a little time to parse.

### Testing checklist

1. Open the Collection dropdown and select each of the four collections.
2. Search a known title from each archive.
3. Filter by genre and release year.
4. Check **Versions → Updates only**, then **Latest per title**.
5. Open an entry's **View details**, then open its original post.
6. Verify poster images load, including filenames containing spaces or parentheses.
7. Watch for the in-page error notice if any of the 14 HTML source files cannot be fetched.

## GitHub Pages publication: important size limit

**Do not assume deploying this repository from main/(root) will work.** Its tracked files are approximately **1.80 GB**, mostly photos. GitHub's documented limits recommend a source repository of at most 1 GB and cap published Pages sites at 1 GB, so this entire repository is too large to publish as-is.

See: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits

This repository was also confirmed **private** when inspected. On GitHub Free, publishing a GitHub Pages site requires a **public** repository. Changing this repository's visibility would expose its archives and images to everyone; review all content and rights before any public release. Merely making this repository public would not fix the Pages size problem.

**Recommended approach for a public site:** Keep this repository private as the source archive. Build a separate small website repository from an intentionally curated list of movie/series metadata and appropriately licensed or authorized optimized poster images. Publish only the needed content rather than all original Telegram exports and photos. A static JSON catalog plus compressed thumbnail images can be much smaller than the source data.

## How to fix the extra Bollywood Movies folder

The root entry **all bollywood movie** is currently a Gitlink, not ordinary uploaded files. If your intention was to upload the movies/HTML files there, make sure its contents are committed as regular files inside this repository, or configure a legitimate public submodule with a valid .gitmodules file. Keep a local backup before modifying Git metadata, and do not delete the local media or HTML. Once the folder has actual HTML export files, it can be added to the catalog's source list.

## Notes

- Each archive is processed in the browser; no external database or paid API is needed for local preview.
- The code has been saved and checked for JavaScript syntax, but not verified as a live GitHub Pages deployment.
- The archived entries, third-party links, and media rights were not independently verified. Only make public material you have the rights to share.
