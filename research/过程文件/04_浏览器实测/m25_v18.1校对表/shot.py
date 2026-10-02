"""给《快速上手》拍校对表的截图。"""
import json
import re
import sys
import time
from pathlib import Path

B = Path(__file__).resolve().parent
src = (B / "check.py").read_text(encoding="utf-8")
src = src[:src.index("def main():")]
exec(compile(src, "check_helpers", "exec"))
URL, OUT = sys.argv[1], sys.argv[2]

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = browser.new_page(viewport={"width": 1280, "height": 1000}, device_scale_factor=2)
    page.goto(URL)
    page.wait_for_function("() => document.querySelectorAll('#vt-clips tbody.tbody tr td').length > 20", timeout=60000)
    time.sleep(1.5)
    ids = [r["id"] for r in manifest()]
    cell(page, ids[0], 6).locator(".vt-sug-blue").click()
    wait_row(page, ids[0], lambda r: "vt-sug-red" in r[6]["html"], "a")
    cell(page, ids[0], 7).locator(".vt-menu-btn").click()
    page.locator(".vt-menu button", has_text="保存这一行").click()
    wait_row(page, ids[0], lambda r: "vt-light-saved" in r[7]["html"], "b", timeout=30)
    time.sleep(1.0)  # 等表格重画完
    cell(page, ids[2], 4).dblclick()
    page.wait_for_selector(".vt-editor textarea")
    _v = page.locator(".vt-editor textarea").input_value(); assert _v == manifest()[2]["text"], (_v, manifest()[2]["text"])
    page.locator(".vt-editor textarea").fill(manifest()[2]["text"].replace("百分之五十", "50%"))
    page.keyboard.press("Enter")
    wait_row(page, ids[2], lambda r: "vt-light-dirty" in r[7]["html"], "c")
    time.sleep(1.0)
    cell(page, ids[4], 7).locator(".vt-menu-btn").click()
    page.locator(".vt-menu button", has_text="删除这一行").click()
    page.locator(".vt-menu button", has_text="确定删除").click()
    wait_row(page, ids[4], lambda r: "vt-flag-del" in r[7]["html"], "d", timeout=30)
    page.evaluate("() => { const s = Array.from(document.querySelectorAll('#vt-clips *')).find(e => e.scrollHeight > e.clientHeight + 20 && /(auto|scroll)/.test(getComputedStyle(e).overflowY)); if (s) s.scrollTop = 0; }")
    time.sleep(0.5)
    cell(page, ids[2], 7).locator(".vt-menu-btn").click()
    page.wait_for_selector(".vt-menu")
    time.sleep(0.4)
    box = page.locator("#vt-clips").bounding_box()
    menu = page.locator(".vt-menu").bounding_box()
    bottom = max(box["y"] + min(box["height"], 470), menu["y"] + menu["height"] + 8)
    page.screenshot(path=OUT, clip={"x": box["x"] - 4, "y": box["y"] - 4, "width": box["width"] + 8,
                                    "height": bottom - box["y"] + 8})
    browser.close()
print("ok")
