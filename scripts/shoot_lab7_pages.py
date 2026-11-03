# Capture the run summary page and the repository page (directory structure).
import os
from playwright.sync_api import sync_playwright

PROFILE = r"C:\Users\pc\AppData\Local\Temp\wblogin"
OUT = r"E:\lab3\gh-calculator\docs\shots"
PROXY = os.environ.get("HTTPS_PROXY", "http://127.0.0.1:59493")

PAGES = [
    ("https://github.com/zhouhangyu1234/calculator/actions/runs/41608836418",
     "lab7-06-run-summary.png", 12000),
    ("https://github.com/zhouhangyu1234/calculator",
     "lab7-07-repo-structure.png", 9000),
]

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PROFILE, channel="msedge", headless=True,
        viewport={"width": 1440, "height": 1600},
        device_scale_factor=2,
        color_scheme="light",
        proxy={"server": PROXY},
        args=["--ignore-certificate-errors", "--no-first-run"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    for url, out, wait in PAGES:
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(wait)
        # scroll to trigger lazy rendering, then back to top
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2500)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(OUT, out), full_page=True)
        print("saved", out, flush=True)
    ctx.close()
print("DONE", flush=True)
