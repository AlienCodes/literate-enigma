import sys, time
from playwright.sync_api import sync_playwright
sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
from browser_check import state  # noqa
URL, F = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = b.new_page(viewport={"width": 1366, "height": 900})
    page.goto(URL); page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000); time.sleep(4)
    print("before:", {k: v for k, v in state(page).items() if k != "info"})
    page.locator("#vt-tr-files input[type=file]").set_input_files(F)
    time.sleep(3)
    print("after upload:", state(page)["box_text"])
    page.locator("#vt-tr-btn").click()
    for _ in range(60):
        time.sleep(2)
        s = state(page)
        if s["btn_disabled"] and "已经用过" in s["info"]:
            break
    time.sleep(3)
    s = state(page)
    print("after click (no reload):", {k: (v[:120] if isinstance(v, str) else v) for k, v in s.items()})
    page.screenshot(path=sys.argv[3])
    b.close()
