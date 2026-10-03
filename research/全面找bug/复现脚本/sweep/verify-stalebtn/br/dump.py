import time
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = b.new_page(viewport={"width": 1366, "height": 900})
    page.goto("http://127.0.0.1:8617/")
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(3)
    print(page.evaluate("""() => Array.from(document.querySelectorAll('#vt-clips tbody.tbody tr')).map(tr =>
        Array.from(tr.children).filter(x => x.tagName === 'TD').map(td => td.innerText.trim().slice(0,20)).join(' | '))"""))
    b.close()
