import json, sys, time
from playwright.sync_api import sync_playwright
URL = sys.argv[1]
S = "/tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/sweep/truth/web"
def txt(page, sel):
    return page.evaluate(f"() => Array.from(document.querySelectorAll({json.dumps(sel)})).map(e => e.innerText).join('\\n')")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = b.new_context(viewport={"width": 1366, "height": 900}).new_page()
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(2)
    inp = page.get_by_label("声音名称（新建请直接输入名字）")
    inp.click(); inp.fill("没文字"); inp.press("Enter")
    time.sleep(5)
    print("voice now:", inp.input_value())
    btn = page.locator("#vt-tr-btn")
    print("btn disabled:", btn.is_disabled())
    print("tr_info:", txt(page, ".vt-tr-info")[:300])
    print("clips_count:", page.evaluate("() => Array.from(document.querySelectorAll('.vt-md')).map(e=>e.innerText).filter(t=>t.includes('用来训练的句子')).join('|')")[:600])
    btn.scroll_into_view_if_needed(); page.screenshot(path=S + "/notext_voice.png")
    b.close()
