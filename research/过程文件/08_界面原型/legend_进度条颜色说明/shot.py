from playwright.sync_api import sync_playwright
import os
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1124, "height": 800}, device_scale_factor=2)
    pg.goto("file://" + os.path.abspath("legend.html"))
    pg.wait_for_timeout(800)
    pg.screenshot(path="11_progress_states.png", full_page=True)
    b.close()
