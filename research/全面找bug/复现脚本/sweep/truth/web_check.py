import json, sys, time, re
from playwright.sync_api import sync_playwright
URL = sys.argv[1]
S = "/tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/sweep/truth/web"
def txt(page, sel):
    return page.evaluate(f"() => Array.from(document.querySelectorAll({json.dumps(sel)})).map(e => e.innerText).join('\\n')")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = b.new_context(viewport={"width": 1366, "height": 900}).new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(3)
    print("document.title:", page.title())
    print("h1:", page.evaluate("() => (document.querySelector('.vt-header h1')||{}).innerText"))
    btn = page.locator("#vt-tr-btn")
    print("btn disabled before:", btn.is_disabled(), "| info:", txt(page, ".vt-tr-info")[:200])
    btn.click()
    t0 = time.time()
    while time.time() - t0 < 120:
        md = txt(page, ".vt-md")
        if "一键全部文字校正完成" in md: break
        time.sleep(1)
    time.sleep(3)
    print("title during/after:", page.title())
    print("btn disabled after:", btn.is_disabled(), "| info:", txt(page, ".vt-tr-info")[:300])
    btn.scroll_into_view_if_needed(); page.screenshot(path=S + "/after_use.png")
    # 换到「没文字」的声音
    v = page.locator("#vt-voice input, .vt-voice input").first
    print("voice input count", page.locator("#vt-voice input").count())
    body = page.evaluate("() => document.body.innerText")
    eng = sorted(set(re.findall(r"\b(?:Error|Traceback|None|null|undefined|NaN|True|False|Exception)\b", body)))
    print("english tokens visible:", eng)
    print("page errors:", errs)
    b.close()
