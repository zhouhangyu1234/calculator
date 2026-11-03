"""Capture Lab 7 screenshots from the running Compose stack.

Runs inside the CI runner after `docker compose up -d --wait`, so every pixel
comes from the real stack: the page is served by the web container (nginx) and
the numbers are computed by the backend container (Java) over the Compose
network.

Usage:  python3 scripts/capture_compose.py
"""

import os
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8080")
OUT = pathlib.Path("docs/shots")
OUT.mkdir(parents=True, exist_ok=True)


def launch_browser(playwright):
    """Prefer the Chrome that ships with the runner image, fall back to Chromium."""
    attempts = (
        {"channel": "chrome", "headless": True, "args": ["--no-sandbox"]},
        {"channel": "msedge", "headless": True, "args": ["--no-sandbox"]},
        {"headless": True, "args": ["--no-sandbox"]},
    )
    for kwargs in attempts:
        try:
            return playwright.chromium.launch(**kwargs)
        except Exception as exc:  # noqa: BLE001 - any launch failure means "try the next one"
            print(f"browser launch attempt failed ({kwargs.get('channel', 'bundled')}): {exc}")
    raise SystemExit("could not launch any browser")


def main() -> int:
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(BASE, wait_until="load")

        # 1. Landing page: the status pill only turns green when /health answered
        #    through nginx, i.e. the reverse proxy found the backend service.
        page.wait_for_selector(".status--ok", timeout=30000)
        page.screenshot(path=str(OUT / "lab7-web-home.png"), full_page=True)
        print("captured lab7-web-home.png")

        # 2. A real calculation: 12 x 7 = 84, computed by the backend container.
        for key in ("1", "2", "op:*", "7", "equals"):
            page.click(f'[data-key="{key}"]')
        page.wait_for_selector("#history li b", timeout=15000)
        result = page.inner_text("#display")
        page.screenshot(path=str(OUT / "lab7-web-result.png"), full_page=True)
        print(f"captured lab7-web-result.png (display = {result})")
        if result.strip() != "84":
            print(f"::error::unexpected result {result!r}")
            return 1

        # 3. Error path: 10 / 0 must render the backend's error message.
        page.click('[data-key="clear"]')
        for key in ("1", "0", "op:/", "0", "equals"):
            page.click(f'[data-key="{key}"]')
        page.wait_for_selector(".screen__value--error", timeout=15000)
        page.screenshot(path=str(OUT / "lab7-web-error.png"), full_page=True)
        print("captured lab7-web-error.png (division by zero)")

        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
