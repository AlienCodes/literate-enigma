"""Real browser: start 「📝 一键全部文字校正」 on voice A, switch the 声音名称 dropdown to voice B while it runs.
When A finishes, the button/info under it are computed for A but shown while B is selected."""
import sys, time
from playwright.sync_api import sync_playwright
from pwlib import *
URL, A, B = sys.argv[1], "我的声音", "第二个声音"
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=CHROME)
    page = br.new_page(viewport={"width": 1366, "height": 900})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(3)
    dd = page.locator("input[aria-label^='声音名称'], .wrap input").first
    def voice_value():
        return page.evaluate("() => { const i = Array.from(document.querySelectorAll('input')).find(x => (x.getAttribute('aria-label')||'').startsWith('声音名称')); return i ? i.value : null; }")
    print("voice at start:", voice_value())
    btn = page.locator("#vt-tr-btn")
    print("textfix button enabled for A before:", btn.is_enabled())
    btn.click()
    time.sleep(1.5)
    # switch to voice B
    inp = page.locator("input[aria-label^='声音名称']")
    inp.click()
    page.locator("ul.options li", has_text=B).first.click()
    time.sleep(3)
    print("voice now:", voice_value(), "| button enabled (B, never used):", btn.is_enabled(), "| label:", btn.inner_text())
    # wait for A's textfix to finish
    t0 = time.time()
    while time.time() - t0 < 300:
        body = text_of(page, "body")
        if "一键全部文字校正完成" in body or "没有完成" in body:
            break
        time.sleep(1)
    time.sleep(4); idle(page)
    print("voice after A finished:", voice_value())
    print("button enabled now (B never used, should be True):", btn.is_enabled())
    print("info under button:", text_of(page, ".vt-tr-info")[:90].replace("\n", " "))
    import os, sys as _s
    _s.path.insert(0, "/home/user/literate-enigma")
    os.chdir("work_big")
    from voicetwin.config import load_config
    from voicetwin import workflows as wf
    cfg = load_config()
    print("server side: textfix_used(A) =", wf.textfix_used(cfg, A), " textfix_used(B) =", wf.textfix_used(cfg, B))
    print("page errors:", errs)
    page.screenshot(path="shot_switch.png")
    br.close()
