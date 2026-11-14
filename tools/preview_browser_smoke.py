#!/usr/bin/env python3
"""Run a real Chromium smoke test against deployed Southscreen preview."""
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = os.environ.get("SOUTHSCREEN_PREVIEW_URL", "https://rejoansardar23.github.io/all-south-movie/preview/")
SCREENSHOT = Path(os.environ.get("SOUTHSCREEN_SCREENSHOT", "/tmp/southscreen-preview-smoke.png"))


def main():
    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1365, "height": 900})
        page.on("pageerror", lambda err: failures.append(str(err)))
        try:
            for attempt in range(1, 9):
                response = page.goto(URL + "?qa=" + str(attempt), wait_until="domcontentloaded", timeout=45000)
                print("Attempt", attempt, "response", response.status if response else None, flush=True)
                try:
                    page.locator(".movie-card").first.wait_for(state="visible", timeout=15000)
                    break
                except Exception:
                    print("Collection failed:", page.locator("#main").inner_text()[:500], flush=True)
                    time.sleep(8)
            else:
                raise AssertionError("Published preview did not render movie cards")

            print("Movie cards visible:", page.locator(".movie-card").count(), flush=True)
            assert page.locator(".movie-card").count() >= 1
            assert "couldn’t load" not in page.locator("body").inner_text().lower()
            assert not failures, "JavaScript errors: " + repr(failures)

            page.locator(".movie-card .poster-link").first.click()
            page.locator("#movie-dialog[open]").wait_for(timeout=15000)
            assert page.locator("#movie-dialog h2#movie-title").inner_text().strip(), "No movie title"
            assert page.locator("#movie-dialog a[data-source]").count() > 0, "No external sources"
            print("Movie details and sources visible", flush=True)

            if page.locator("#movie-dialog button[data-action='source-quality']").count() > 1:
                page.locator("#movie-dialog button[data-action='source-quality']").nth(1).click()
                assert page.locator("#movie-dialog a[data-source]:visible").count() >= 1
                print("Quality filter works", flush=True)

            page.locator("#movie-dialog button[data-action='close-movie']").click()
            page.locator("#movie-dialog").wait_for(state="hidden", timeout=15000)
            page.locator("#search").fill("rrr")
            page.locator("#search-suggestions").wait_for(state="visible", timeout=15000)
            print("Search suggestions visible", flush=True)
            assert not failures, "JavaScript errors: " + repr(failures)
            page.screenshot(path=str(SCREENSHOT), full_page=True)
            print("PASS: Catalog, movie dialog, provider links, filtering and search render correctly", flush=True)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
