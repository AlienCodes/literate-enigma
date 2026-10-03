"""Real browser: after 「删除这一行」 (takes a few seconds: re-counts all material), a text edit made right after
is silently dropped (the hidden clip-action button's click event uses gradio's default trigger_mode='once')."""
import sys, time
from playwright.sync_api import sync_playwright
from pwlib import *
URL, VD = sys.argv[1], sys.argv[2]
DEL_ROW, EDIT_ROW, WAIT = int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
ID = lambda n: f"0006_9498bb_{n:04d}"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    page = b.new_page(viewport={"width": 1366, "height": 900})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(3)
    click_cell(page, ID(DEL_ROW), C["menu"], ".vt-menu-btn")
    time.sleep(0.4)
    menu_item(page, "删除这一行")
    time.sleep(0.3)
    menu_item(page, "确定删除")
    t0 = time.time()
    time.sleep(WAIT)
    click_cell(page, ID(EDIT_ROW), C["text"], dbl=True)
    page.wait_for_selector(".vt-editor-text", timeout=5000)
    page.keyboard.press("End")
    page.keyboard.insert_text("（删除后马上改的）")
    page.keyboard.press("Enter")
    print(f"edit committed {time.time() - t0:.2f}s after confirming the delete")
    shown = td_rect(page, ID(EDIT_ROW), C["text"])
    print("cell right after Enter:", (shown or [0, 0, ""])[2][-12:])
    time.sleep(8); idle(page)
    d = draft(VD); m = manifest(VD)
    print("row deleted:", bool(m[ID(DEL_ROW)].get("deleted")))
    print("edit in draft:", "删除后马上改的" in d.get(ID(EDIT_ROW), {}).get("text", ""))
    shown = td_rect(page, ID(EDIT_ROW), C["text"])
    print("cell after the table refreshed:", (shown or [0, 0, ""])[2][-12:])
    print("clip_msg:", text_of(page, ".vt-clip-msg")[:100])
    print("page errors:", errs)
    page.screenshot(path="shot_drop2.png")
    b.close()
