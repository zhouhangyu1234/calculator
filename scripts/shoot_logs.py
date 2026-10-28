# Click-expand GitHub Actions job log steps and capture per-step screenshots.
import json
from playwright.sync_api import sync_playwright

JOB = "https://github.com/zhouhangyu1234/calculator/actions/runs/40523974508/job/122258717179"
OUT = r"E:\lab3\gh-calculator\docs\shots"

TARGETS = [
    ("Build Docker image",                  "06-docker-build.png",  2000),
    ("List Docker images",                  "07-docker-images.png", 900),
    ("Run calculator inside the container", "08-container-run.png", 1200),
    ("Division by zero must be reported",   "09-divzero.png",       900),
    ("Tag and push image",                  "10-push.png",          900),
]

def doc_rects(page, names):
    return page.evaluate("""
    (names) => {
        const res = {};
        for (const d of document.querySelectorAll('details.js-checks-log-details')) {
            const t = (d.innerText || '').trim();
            for (const n of names) {
                if (t.includes(n) && !(n in res)) {
                    const r = d.getBoundingClientRect();
                    res[n] = { top: r.top + window.scrollY, bottom: r.bottom + window.scrollY,
                               open: d.open };
                }
            }
        }
        return res;
    }
    """, names)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 1000},
        device_scale_factor=2,
        color_scheme="light",
    )
    page = ctx.new_page()
    page.goto(JOB, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)

    for name, out, maxh in TARGETS:
        summ = page.locator("summary.js-check-step-summary").filter(has_text=name)
        n = summ.count()
        if n == 0:
            print("MISS(header)", name)
            continue
        try:
            summ.first.click(timeout=8000)
        except Exception:
            summ.first.click(timeout=8000, force=True)
        page.wait_for_timeout(3500)
        r = doc_rects(page, [name]).get(name)
        print(("open  " if r and r["open"] else "FAIL  ") + name, "->", r and round(r["bottom"] - r["top"]), "px")

    # scroll back to top so document coords are stable, then re-measure
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(1500)
    rects = doc_rects(page, [t[0] for t in TARGETS])
    print("rects:", json.dumps(rects, indent=1))
    total_h = page.evaluate("() => document.body.scrollHeight")
    print("page height:", total_h)

    for name, out, maxh in TARGETS:
        if name not in rects or not rects[name]["open"]:
            print("SKIP", name)
            continue
        top = max(0, rects[name]["top"] - 6)
        height = min(maxh, total_h - top, rects[name]["bottom"] - top + 30)
        path = OUT + "\\" + out
        page.screenshot(path=path, full_page=True, clip={"x": 0, "y": top, "width": 1440, "height": max(300, height)})
        print("saved", out, round(height), "px")

    browser.close()
print("DONE")
