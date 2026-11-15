#!/usr/bin/env python3
"""Browser smoke test for Worldscreen packaged with imported movie poster images."""
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = os.environ.get("WORLDSCREEN_TEST_URL", "http://127.0.0.1:8765/")
SCREENSHOT = Path(os.environ.get("WORLDSCREEN_SCREENSHOT", "/tmp/worldscreen-home.png"))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 1365, "height": 900})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    resp = page.goto(URL, wait_until="domcontentloaded", timeout=45000)
    assert resp and resp.status == 200, "Website did not return HTTP 200"
    page.locator(".movie-card").first.wait_for(state="visible", timeout=60000)
    assert "Worldscreen" in page.title(), "New branding missing in document title"
    assert page.locator(".language-chips a").count() >= 6, "Multilingual browsing missing"
    cards = page.locator(".movie-card").count()
    assert cards > 20, f"Only {cards} cards rendered"
    page.locator(".movie-card img").first.wait_for(state="attached")
    page.wait_for_function("""() => {
      const el = document.querySelector('.movie-card img');
      return el && el.complete && el.naturalWidth > 0;
    }""", timeout=25000)
    print("Worldscreen homepage rendered", cards, "cards; first poster image loaded")
    page.screenshot(path=str(SCREENSHOT), full_page=False)
    page.locator(".movie-card .poster-link").first.click()
    page.locator("#movie-dialog[open]").wait_for(state="visible", timeout=10000)
    assert page.locator("#movie-dialog .source-link").count() > 0, "No provider links"
    assert "View original post" not in page.locator("#movie-dialog").inner_text()
    if page.locator("#movie-dialog [data-action='source-quality']").count() > 1:
        page.locator("#movie-dialog [data-action='source-quality']").nth(1).click()
        assert page.locator("#movie-dialog .source-link:visible").count() > 0
    print("Movie dialog, source controls and quality options passed")
    assert not errors, "Runtime errors: " + repr(errors)
    page.locator("#movie-dialog [data-action='close-movie']").click()
    page.locator("#movie-dialog").wait_for(state="hidden", timeout=10000)
    page.locator("#search").fill("rrr")
    page.locator("#search-suggestions").wait_for(state="visible", timeout=10000)
    print("Search suggestions passed")
    assert not errors, "Runtime errors: " + repr(errors)
    browser.close()
print("PASS: Worldscreen from actual packaged catalog and media works in Chromium")
