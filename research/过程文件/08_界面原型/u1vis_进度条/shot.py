import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

port = int(sys.argv[1])
out = sys.argv[2]
url = f"http://127.0.0.1:{port}/"
for _ in range(90):
    try:
        urllib.request.urlopen(url, timeout=2)
        break
    except Exception:
        time.sleep(1)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    for theme, w in (("light", 900), ("dark", 900), ("light", 375)):
        page = b.new_page(viewport={"width": w, "height": 900})
        page.goto(url + ("?__theme=dark" if theme == "dark" else ""))
        page.wait_for_selector(".vt-prog")
        time.sleep(1.5)
        sw = page.evaluate("document.documentElement.scrollWidth")
        cw = page.evaluate("document.documentElement.clientWidth")
        title = page.evaluate("document.title")
        anim = page.evaluate("getComputedStyle(document.querySelector('.vt-running .vt-fill')).animationName")
        bg = page.evaluate("getComputedStyle(document.querySelector('.vt-running .vt-fill')).backgroundColor")
        stall_bg = page.evaluate("getComputedStyle(document.querySelector('.vt-stall .vt-fill')).backgroundColor")
        err_bg = page.evaluate("getComputedStyle(document.querySelector('.vt-error .vt-fill')).backgroundColor")
        stop_bg = page.evaluate("getComputedStyle(document.querySelector('.vt-stopped .vt-fill')).backgroundColor")
        print(theme, w, "scrollWidth", sw, "clientWidth", cw, "title", title, "anim", anim,
              "colors", bg, stall_bg, err_bg, stop_bg)
        page.screenshot(path=f"{out}_{theme}_{w}.png", full_page=True)
        page.close()
    b.close()
