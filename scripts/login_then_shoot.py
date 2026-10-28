# Open a visible Edge window controlled by Playwright, let the user sign in to GitHub,
# then expand the docker job steps and capture screenshots.
import json, sys
from playwright.sync_api import sync_playwright

PROFILE = r"C:\Users\pc\AppData\Local\Temp\wblogin"
JOB = "https://github.com/zhouhangyu1234/calculator/actions/runs/40523974508/job/122258717179"
OUT = r"E:\lab3\gh-calculator\docs\shots"
PROXY = "http://127.0.0.1:57667"

TARGETS = [
    ("Build Docker image",                  "06-docker-build.png",  2400),
    ("List Docker images",                  "07-docker-images.png", 800),
    ("Run calculator inside the container", "08-container-run.png", 1400),
    ("Division by zero must be reported",   "09-divzero.png",       700),
    ("Tag and push image",                  "10-push.png",          700),
]

def login_state(page):
    return page.evaluate("""
    () => {
        const loginLink = document.querySelector('a[href="/login"]');
        const avatar = document.querySelector('summary[aria-label*="View profile" i], img.avatar, [data-hovercard-type="user"]');
        const meta = document.querySelector('meta[name="user-login"]');
        return { login: meta ? meta.content : null, hasLogin: !!loginLink, hasAvatar: !!avatar, url: location.href };
    }
    """)

def rects(page, names):
    return page.evaluate("""
    (names) => {
        const res = {};
        for (const d of document.querySelectorAll('details.js-checks-log-details')) {
            const t = (d.innerText || '').trim();
            for (const n of names) {
                if (t.includes(n) && !(n in res)) {
                    const r = d.getBoundingClientRect();
                    res[n] = { top: r.top + window.scrollY, bottom: r.bottom + window.scrollY, open: d.open };
                }
            }
        }
        return res;
    }
    """, names)

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PROFILE,
        channel="msedge",
        headless=False,
        viewport={"width": 1440, "height": 950},
        color_scheme="light",
        proxy={"server": PROXY},
        args=["--ignore-certificate-errors", "--no-first-run"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://github.com/login", wait_until="domcontentloaded", timeout=90000)
    print("WINDOW READY: please sign in to GitHub in the opened window", flush=True)

    ok = False
    for i in range(160):  # up to ~8 minutes
        try:
            st = login_state(page)
            if st["login"] == "zhouhangyu1234":
                ok = True
                print("LOGIN DETECTED as", st["login"], flush=True)
                break
        except Exception:
            pass
        page.wait_for_timeout(3000)

    if not ok:
        print("LOGIN TIMEOUT - no session detected", flush=True)
        ctx.close()
        sys.exit(1)

    page.goto(JOB, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(9000)
    print("JOB PAGE LOADED", flush=True)

    for name, out, maxh in TARGETS:
        summ = page.locator("summary.js-check-step-summary").filter(has_text=name)
        if summ.count() == 0:
            print("MISS", name, flush=True)
            continue
        for attempt in range(2):
            try:
                summ.first.click(timeout=10000, force=(attempt == 1))
            except Exception as e:
                print("  click err", name, e.__class__.__name__, flush=True)
            page.wait_for_timeout(3500)
            r = rects(page, [name]).get(name)
            if r and r["open"]:
                break
        r = rects(page, [name]).get(name)
        print(("open  " if r and r["open"] else "STILL CLOSED ") + name, r and round(r["bottom"] - r["top"]), flush=True)

    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(2000)
    allr = rects(page, [t[0] for t in TARGETS])
    total_h = page.evaluate("() => document.body.scrollHeight")
    print("total_h", total_h, flush=True)

    for name, out, maxh in TARGETS:
        r = allr.get(name)
        if not r or not r["open"]:
            print("SKIP", name, flush=True)
            continue
        top = max(0, r["top"] - 8)
        height = min(maxh, total_h - top, r["bottom"] - top + 30)
        page.screenshot(path=OUT + "\\" + out, full_page=True,
                        clip={"x": 0, "y": top, "width": 1440, "height": max(320, height)})
        print("saved", out, round(height), "px", flush=True)

    ctx.close()
print("DONE", flush=True)
