# Inspect the DOM around the step rows to learn how to expand logs.
import json
from playwright.sync_api import sync_playwright

JOB = "https://github.com/zhouhangyu1234/calculator/actions/runs/40523974508/job/122258717179"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, color_scheme="light")
    page = ctx.new_page()
    page.goto(JOB, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)

    info = page.evaluate("""
    () => {
        const out = [];
        const walk = (el) => {
            const t = (el.childElementCount === 0 ? el.textContent : (el.innerText || '')).trim();
            if (t && (t.includes('Build Docker image') || t.includes('List Docker images')) && t.length < 200) {
                out.push({
                    tag: el.tagName,
                    cls: (el.className || '').toString().slice(0, 120),
                    role: el.getAttribute('role'),
                    tabindex: el.getAttribute('tabindex'),
                    text: t.slice(0, 90),
                    childCount: el.childElementCount,
                });
            }
            for (const c of el.children) walk(c);
        };
        walk(document.body);
        return out;
    }
    """)
    for e in info:
        print(json.dumps(e))
    print("total:", len(info))
    browser.close()
