"""Real browser: start 「📝 一键全部文字校正」, reload the page mid-run, then (a) just wait / (b) click the button again
to re-attach. Check the status line at the top of the page and the button after it finishes."""
import sys, time, re
from playwright.sync_api import sync_playwright
from pwlib import *
URL, MODE = sys.argv[1], sys.argv[2]
def status(page):
    return page.evaluate("""() => { const all = Array.from(document.querySelectorAll('.vt-md')); const s = all.find(x => /素材|后台正在|新声音/.test(x.innerText)); return s ? s.innerText.replace(/\\n+/g, ' ').slice(0, 160) : ''; }""")
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=CHROME)
    page = br.new_page(viewport={"width": 1366, "height": 900})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(2)
    page.locator("#vt-tr-btn").click()
    time.sleep(2.5)
    page.reload()
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(2)
    print("top status right after reload:", status(page))
    btn = page.locator("#vt-tr-btn")
    print("button after reload:", btn.inner_text(), "enabled:", btn.is_enabled())
    if MODE == "reclick":
        btn.click()
        time.sleep(2)
    t0 = time.time()
    sys.path.insert(0, "/home/user/literate-enigma")
    import os
    os.chdir("work_big")
    from voicetwin.webui.tasks import current_task  # (not shared with the server process; just wait on the page)
    while time.time() - t0 < 200:
        body = text_of(page, "body")
        if "一键全部文字校正完成" in body:
            break
        if MODE == "wait" and time.time() - t0 > 40:
            break
        time.sleep(1)
    time.sleep(15)
    print("result line:", [l for l in text_of(page, "body").split("\n") if "校正完成" in l][:1])
    print(f"after {time.time()-t0:.0f}s top status:", status(page))
    print("top banner:", [l for l in text_of(page, "body").split("\n") if "上次的" in l or "后台正在" in l][:3])
    print("button:", btn.inner_text(), "enabled:", btn.is_enabled())
    print("page errors:", errs)
    page.screenshot(path=f"shot_reload_textfix_{MODE}.png", full_page=False)
    br.close()
