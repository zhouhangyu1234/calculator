# Capture console errors and inspect the step element internals.
import json
from playwright.sync_api import sync_playwright

JOB = "https://github.com/zhouhangyu1234/calculator/actions/runs/40523974508/job/122258717179"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, color_scheme="light")
    page = ctx.new_page()
    errs = []
    page.on("console", lambda m: errs.append((m.type, m.text[:200])) if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: errs.append(("pageerror", str(e)[:300])))
    page.goto(JOB, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(10000)

    print("console errors:", len(errs))
    for t, m in errs[:12]:
        print(" ", t, m)

    html = page.evaluate("""
    () => {
        for (const d of document.querySelectorAll('details.js-checks-log-details')) {
            if ((d.innerText||'').includes('List Docker images')) {
                return d.outerHTML.slice(0, 2200);
            }
        }
        return 'not found';
    }
    """)
    print("----- details outerHTML -----")
    print(html)
    browser.close()
