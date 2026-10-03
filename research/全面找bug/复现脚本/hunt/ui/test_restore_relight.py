"""Real browser: after 一键全部文字校正 was used (button gray), restore a row that had been deleted before.
No new material was added, yet after reloading the page the button is lit again and the lock note is gone."""
import sys, time
from playwright.sync_api import sync_playwright
from pwlib import *
URL, CID, Q = sys.argv[1], "and-revised_db6f95_0018", "将相同对象的句子成分合编"
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=CHROME)
    page = br.new_page(viewport={"width": 1366, "height": 900})
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(3)
    btn = page.locator("#vt-tr-btn")
    print("button at start (used -> gray):", btn.is_enabled(), "| lock note:", "每批素材只能用一次" in text_of(page, ".vt-tr-info"))
    print("scrolled:", scroll_to_no(page, 661, 1004))
    r = td_rect(page, CID, C["menu"], ".vt-menu-btn"); time.sleep(0.3); r = td_rect(page, CID, C["menu"], ".vt-menu-btn")
    page.mouse.click(r[0], r[1])
    if False: click_cell(page, CID, C["menu"], ".vt-menu-btn")
    time.sleep(0.5)
    menu_item(page, "撤销删除")
    time.sleep(6); idle(page)
    print("clip_msg:", text_of(page, ".vt-clip-msg")[:60])
    print("button right after restore:", btn.is_enabled())
    page.reload()
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(3)
    print("button after reload (no new material was added):", btn.is_enabled(), "| lock note:", "每批素材只能用一次" in text_of(page, ".vt-tr-info"))
    br.close()
