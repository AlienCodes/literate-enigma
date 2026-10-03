import json, sys, time
from playwright.sync_api import sync_playwright
URL = sys.argv[1]
S = "/tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/sweep/truth/web"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = b.new_context(viewport={"width": 1366, "height": 900}, accept_downloads=True).new_page()
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(2)
    page.locator("#vt-dl-txt-btn").click()
    t0 = time.time(); found = ""
    while time.time() - t0 < 30:
        found = page.evaluate("() => Array.from(document.querySelectorAll('.vt-md')).map(e=>e.innerText).filter(t=>t.includes('存成 txt')).join('|')")
        if found: break
        time.sleep(0.5)
    print("RENDERED:", found)
    page.locator("#vt-dl-txt-btn").scroll_into_view_if_needed(); page.screenshot(path=S + "/download_md.png")
    b.close()
