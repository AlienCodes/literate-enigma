"""Real browser: are table actions sent in quick succession silently dropped (hidden button, trigger_mode='once')?"""
import sys, time, json
from playwright.sync_api import sync_playwright
from pwlib import *
URL = sys.argv[1]
VD = sys.argv[2]
which = sys.argv[3] if len(sys.argv) > 3 else "ACDE"
ID = lambda n: f"0006_9498bb_{n:04d}"

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    page = b.new_page(viewport={"width": 1366, "height": 900})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(3)
    if "C" in which:
        # C: two different rows' blue "采用" buttons clicked 300 ms apart
        d0 = draft(VD)
        click_cell(page, ID(1), C["suggest"], ".vt-sug-btn")
        time.sleep(0.3)
        click_cell(page, ID(3), C["suggest"], ".vt-sug-btn")
        time.sleep(4); idle(page)
        d = draft(VD)
        print("C adopt row1 in draft:", ID(1) in d, "| adopt row3 in draft:", ID(3) in d)
        print("C clip_msg:", text_of(page, ".vt-clip-msg")[:120])
    if "A" in which:
        # A: delete a row via the menu, then 1 s later click "采用" on another row
        click_cell(page, ID(5), C["menu"], ".vt-menu-btn")
        time.sleep(0.4)
        menu_item(page, "删除这一行")
        time.sleep(0.3)
        menu_item(page, "确定删除")
        t0 = time.time()
        time.sleep(1.0)
        click_cell(page, ID(7), C["suggest"], ".vt-sug-btn")
        time.sleep(0.2)
        print("A row7 button right after the click:", (td_rect(page, ID(7), C["suggest"]) or [0, 0, "?"])[2])
        time.sleep(8); idle(page)
        print("A row7 button after the table refreshed:", (td_rect(page, ID(7), C["suggest"]) or [0, 0, "?"])[2])
        d = draft(VD); m = manifest(VD)
        print("A row5 deleted:", bool(m[ID(5)].get("deleted")), "| adopt row7 in draft:", ID(7) in d)
        print("A clip_msg:", text_of(page, ".vt-clip-msg")[:120])
    if "D" in which:
        # D: editing row 9's text, then directly click "采用" on row 11 (the edit is sent ~200 ms after the adopt)
        click_cell(page, ID(9), C["text"], dbl=True)
        page.wait_for_selector(".vt-editor-text", timeout=5000)
        page.keyboard.press("End")
        page.keyboard.insert_text("（老师改的）")
        time.sleep(0.3)
        click_cell(page, ID(11), C["suggest"], ".vt-sug-btn")
        time.sleep(5); idle(page)
        d = draft(VD)
        print("D edit row9 in draft:", ID(9) in d and "老师改的" in d.get(ID(9), {}).get("text", ""), "| adopt row11 in draft:", ID(11) in d)
        print("D clip_msg:", text_of(page, ".vt-clip-msg")[:120])
    if "E" in which:
        # E: editing row 13's text, then directly click 「保存修改」
        click_cell(page, ID(13), C["text"], dbl=True)
        page.wait_for_selector(".vt-editor-text", timeout=5000)
        page.keyboard.press("End")
        page.keyboard.insert_text("（E改的）")
        time.sleep(0.3)
        btn = page.locator("button", has_text="保存修改").last
        btn.scroll_into_view_if_needed()
        btn.click()
        time.sleep(6); idle(page)
        d = draft(VD); m = manifest(VD)
        print("E saved in manifest:", "E改的" in m[ID(13)]["text"], "| still unsaved draft:", ID(13) in d and "E改的" in d[ID(13)].get("text", ""))
        print("E review_md:", text_of(page, ".vt-md")[:0], page.evaluate("() => { const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.trim() === '保存修改'); let n = b; for (let i=0;i<6;i++){ n = n.parentElement; } return ''; }"))
        md = page.evaluate("""() => { const all = Array.from(document.querySelectorAll('.vt-md')); return all.map(x => x.innerText).filter(t => t.includes('已保存') || t.includes('没有需要保存')).join(' || ').slice(0, 300); }""")
        print("E messages:", md)
        print("E clip_msg:", text_of(page, ".vt-clip-msg")[:160])
    print("JS errors:", errs[:5])
    page.screenshot(path="shot_drop.png")
    b.close()
