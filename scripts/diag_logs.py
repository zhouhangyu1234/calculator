# Diagnose why expanded step logs are empty.
import json
from playwright.sync_api import sync_playwright

PROFILE = r"C:\Users\pc\AppData\Local\Temp\wblogin"
JOB = "https://github.com/zhouhangyu1234/calculator/actions/runs/40523974508/job/122258717179"
PROXY = "http://127.0.0.1:57667"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PROFILE, channel="msedge", headless=True,
        viewport={"width": 1440, "height": 1000},
        proxy={"server": PROXY},
        args=["--ignore-certificate-errors", "--no-first-run"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    responses = []
    page.on("response", lambda r: responses.append((r.status, r.url[:160])) if "logs" in r.url else None)

    page.goto(JOB, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(8000)

    st = page.evaluate("() => { const m = document.querySelector('meta[name=\"user-login\"]'); return m ? m.content : null; }")
    print("login:", st)

    # expand one step
    summ = page.locator("summary.js-check-step-summary").filter(has_text="List Docker images").first
    summ.click(force=True)
    page.wait_for_timeout(8000)

    info = page.evaluate("""
    () => {
        for (const d of document.querySelectorAll('details.js-checks-log-details')) {
            if ((d.innerText || '').includes('List Docker images')) {
                return {
                    open: d.open,
                    htmlLen: d.innerHTML.length,
                    textLen: (d.innerText || '').length,
                    text: (d.innerText || '').slice(0, 400),
                    logUrl: d.querySelector('check-step') ? d.querySelector('check-step').getAttribute('data-log-url') : null,
                };
            }
        }
        return null;
    }
    """)
    print("step info:", json.dumps(info, ensure_ascii=False, indent=1)[:1200])

    # try fetching the log url from within the page
    if info and info.get("logUrl"):
        res = page.evaluate("""
        async (u) => {
            const r = await fetch(u, { credentials: 'include', headers: { 'Accept': 'text/html' } });
            const t = await r.text();
            return { status: r.status, len: t.length, head: t.slice(0, 300) };
        }
        """, info["logUrl"])
        print("in-page fetch:", json.dumps(res, ensure_ascii=False)[:800])

    print("log-related responses:", responses[:10])
    ctx.close()
print("DONE")
