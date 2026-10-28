# Try multiple ways to expand steps; also probe the raw log URLs.
import json
from playwright.sync_api import sync_playwright

JOB = "https://github.com/zhouhangyu1234/calculator/actions/runs/40523974508/job/122258717179"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, color_scheme="light")
    page = ctx.new_page()
    page.goto(JOB, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)

    # 1. collect data-log-url attributes
    urls = page.evaluate("""
    () => Array.from(document.querySelectorAll('check-step')).map(e => ({
        name: e.getAttribute('data-name'),
        logurl: e.getAttribute('data-log-url'),
        num: e.getAttribute('data-number'),
    }))
    """)
    for u in urls:
        print(u["num"], u["name"], "->", u["logurl"])

    # 2. keyboard Enter on summary
    summ = page.locator("summary.js-check-step-summary").filter(has_text="List Docker images").first
    summ.focus()
    page.keyboard.press("Enter")
    page.wait_for_timeout(3000)
    state = page.evaluate("""
    () => Array.from(document.querySelectorAll('details.js-checks-log-details')).map(d => ({
        name: (d.innerText||'').trim().split('\\n')[0], open: d.open
    }))
    """)
    print("after Enter:", json.dumps(state))

    # 3. JS click
    page.evaluate("""
    () => {
        for (const d of document.querySelectorAll('details.js-checks-log-details')) {
            if ((d.innerText||'').includes('List Docker images')) {
                const s = d.querySelector('summary');
                s.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
            }
        }
    }
    """)
    page.wait_for_timeout(3000)
    state = page.evaluate("""
    () => Array.from(document.querySelectorAll('details.js-checks-log-details')).map(d => ({
        name: (d.innerText||'').trim().split('\\n')[0], open: d.open
    }))
    """)
    print("after JS click:", json.dumps(state))

    # 4. probe raw logs endpoint of the first log-url found
    if urls and urls[0]["logurl"]:
        raw = "https://github.com" + urls[0]["logurl"]
        print("probe:", raw)
        try:
            resp = page.goto(raw, timeout=30000)
            print("status:", resp.status, "type:", resp.headers.get("content-type"))
            body = page.content()
            print("body head:", body[:500].replace("\n", " "))
        except Exception as e:
            print("probe failed:", e.__class__.__name__, str(e)[:200])

    browser.close()
print("DONE")
