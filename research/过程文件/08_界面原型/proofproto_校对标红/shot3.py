import os, glob
from playwright.sync_api import sync_playwright
P = os.path.dirname(os.path.abspath(__file__))
exe = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe[-1] if exe else None, args=["--no-proxy-server"])
    pg = b.new_page(viewport={"width": 1280, "height": 3600})
    pg.goto("http://127.0.0.1:7880/", wait_until="networkidle")
    pg.wait_for_timeout(3000)
    pg.screenshot(path=os.path.join(P, "df.png"), full_page=True)
    b.close()
print("ok")
