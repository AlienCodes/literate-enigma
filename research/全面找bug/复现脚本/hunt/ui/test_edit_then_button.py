"""Real browser: type a correction in the 「文字」 editor, then (without pressing Enter) click 「保存修改」 or
「✅ 确认训练素材」 directly. The editor commits on blur 200 ms later, so the button's handler runs before the edit exists."""
import sys, time, json
from playwright.sync_api import sync_playwright
from pwlib import *
URL, VD, ROW, BTN = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
ID = lambda n: f"0006_9498bb_{n:04d}"
sys.path.insert(0, "/home/user/literate-enigma")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    page = b.new_page(viewport={"width": 1366, "height": 900})
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(3)
    click_cell(page, ID(ROW), C["text"], dbl=True)
    page.wait_for_selector(".vt-editor-text", timeout=5000)
    page.keyboard.press("End")
    page.keyboard.insert_text("（直接点按钮）")
    time.sleep(0.5)
    btn = page.locator("button", has_text=BTN).last
    btn.scroll_into_view_if_needed()
    btn.click()
    time.sleep(10); idle(page)
    d = draft(VD); m = manifest(VD)
    print("button:", BTN)
    print("edit saved into manifest:", "直接点按钮" in m[ID(ROW)]["text"])
    print("edit left as unsaved draft (red light):", "直接点按钮" in d.get(ID(ROW), {}).get("text", ""))
    md = page.evaluate("""() => Array.from(document.querySelectorAll('.vt-md')).map(x => x.innerText).filter(t => /已保存|没有需要保存|训练素材已确认/.test(t)).join(' || ').slice(0, 300)""")
    print("message under the buttons:", md.replace("\n", " "))
    import os
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(VD))))
    from voicetwin.config import load_config
    from voicetwin import workflows as wf
    print("training blocker now:", wf.training_blocker_for(load_config(), "我的声音")[:120])
    page.screenshot(path=f"shot_edit_then_{ROW}.png")
    b.close()
