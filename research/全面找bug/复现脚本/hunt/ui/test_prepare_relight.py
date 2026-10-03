"""Real browser, the real path the teacher uses: voice B -> 一键全部文字校正 (button turns gray) -> 开始准备素材 with a
folder of new material (wav + srt) -> does the button light up again (the .then(textfix_btn) chain)?"""
import sys, time, os
from playwright.sync_api import sync_playwright
from pwlib import *
URL, B, FOLDER = sys.argv[1], "第二个声音", os.path.abspath("media1")
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=CHROME)
    page = br.new_page(viewport={"width": 1366, "height": 900})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(2)
    inp = page.locator("input[aria-label^='声音名称']")
    inp.click()
    page.locator("ul.options li", has_text=B).first.click()
    time.sleep(3)
    btn = page.locator("#vt-tr-btn")
    print("B button before:", btn.is_enabled())
    if btn.is_enabled():
        btn.click()
        t0 = time.time()
        while time.time() - t0 < 120 and "一键全部文字校正完成" not in text_of(page, "body"):
            time.sleep(1)
        time.sleep(3)
    print("B button after textfix (gray expected):", btn.is_enabled())
    page.get_by_label("或者填写电脑上的文件夹路径（推荐）").fill(FOLDER)
    page.get_by_role("button", name="开始准备素材").click()
    t0 = time.time()
    while time.time() - t0 < 400:
        body = text_of(page, "body")
        if "素材准备好了" in body or "素材准备没有完成" in body or "没有完成" in body:
            break
        time.sleep(1)
    time.sleep(6); idle(page)
    print(f"prepare finished after {time.time()-t0:.0f}s:", [l for l in text_of(page, '.vt-md').split('\n') if '素材准备' in l][:2])
    print("button after new material (should be enabled):", btn.is_enabled(), "| info:", text_of(page, ".vt-tr-info")[:50].replace("\n", " "))
    sys.path.insert(0, "/home/user/literate-enigma")
    os.chdir("work_big")
    from voicetwin.config import load_config
    from voicetwin import workflows as wf
    from voicetwin.data import transcript_fix as tf
    print("server: textfix_used(B) =", wf.textfix_used(load_config(), B), "new ids:", tf.textfix_new_ids(wf.Project(load_config(), B))[:6])
    print("page errors:", errs)
    page.screenshot(path="shot_prepare_relight.png")
    br.close()
