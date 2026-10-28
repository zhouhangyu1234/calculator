# Expand steps, wait for lazy log content, then element-screenshot each step.
import json
from playwright.sync_api import sync_playwright

PROFILE = r"C:\Users\pc\AppData\Local\Temp\wblogin"
JOB = "https://github.com/zhouhangyu1234/calculator/actions/runs/40523974508/job/122258717179"
OUT = r"E:\lab3\gh-calculator\docs\shots"
PROXY = "http://127.0.0.1:57667"

TARGETS = [
    ("Build Docker image",                  "06-docker-build.png"),
    ("List Docker images",                  "07-docker-images.png"),
    ("Run calculator inside the container", "08-container-run.png"),
    ("Division by zero must be reported",   "09-divzero.png"),
    ("Tag and push image",                  "10-push.png"),
]

def step_state(page, name):
    return page.evaluate("""
    (n) => {
        for (const d of document.querySelectorAll('details.js-checks-log-details')) {
            if ((d.innerText || '').includes(n)) {
                return { open: d.open, textLen: (d.innerText || '').length };
            }
        }
        return null;
    }
    """, name)

def details_loc(page, name):
    return page.locator("details.js-checks-log-details").filter(has_text=name).first

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PROFILE, channel="msedge", headless=True,
        viewport={"width": 1440, "height": 1000},
        device_scale_factor=2,
        color_scheme="light",
        proxy={"server": PROXY},
        args=["--ignore-certificate-errors", "--no-first-run"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(JOB, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(8000)
    print("login:", page.evaluate("() => { const m = document.querySelector('meta[name=\"user-login\"]'); return m ? m.content : null; }"), flush=True)

    # expand all and wait for lazy content
    for name, out in TARGETS:
        summ = page.locator("summary.js-check-step-summary").filter(has_text=name)
        if summ.count() == 0:
            print("MISS", name, flush=True)
            continue
        summ.first.click(force=True)
        # poll until content beyond the header renders (header ~ 30-60 chars)
        ready = False
        for _ in range(15):
            page.wait_for_timeout(2000)
            st = step_state(page, name)
            if st and st["open"] and st["textLen"] > 150:
                ready = True
                break
        st = step_state(page, name)
        print(("ready  " if ready else "TIMEOUT ") + name, st, flush=True)

    # element screenshots (handles scrolling + stitching internally)
    for name, out in TARGETS:
        loc = details_loc(page, name)
        try:
            loc.scroll_into_view_if_needed(timeout=10000)
            page.wait_for_timeout(2500)
            loc.screenshot(path=OUT + "\\" + out, timeout=30000)
            print("saved", out, flush=True)
        except Exception as e:
            print("shot failed", name, e.__class__.__name__, str(e)[:120], flush=True)

    ctx.close()
print("DONE", flush=True)
