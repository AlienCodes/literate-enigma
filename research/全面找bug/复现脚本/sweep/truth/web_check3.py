import json, sys, time, re
from playwright.sync_api import sync_playwright
URL = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    for loc in ("en-US", "zh-CN"):
        page = b.new_context(viewport={"width": 1366, "height": 900}, locale=loc).new_page()
        page.goto(URL)
        page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
        time.sleep(3)
        words = {}
        # 所有标签页都看一遍
        tabs = page.locator("button[role=tab]")
        for i in range(tabs.count()):
            try:
                tabs.nth(i).click(); time.sleep(1.5)
            except Exception:
                pass
            body = page.evaluate("() => document.body.innerText")
            for w in re.findall(r"[A-Za-z][A-Za-z' ]{2,}[A-Za-z]", body):
                words.setdefault(w.strip(), set()).add(i)
        print("==", loc, page.title())
        print(sorted(words))
        page.close()
    b.close()
