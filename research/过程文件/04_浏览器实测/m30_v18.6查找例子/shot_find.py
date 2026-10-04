"""给《快速上手》拍「查找 / 替换」的截图（v18.6：例子是「借词 → 介词」）：查找栏 + 结果 + 找到的几句。
另外检查查找框上面写的是「例如：借词」「例如：介词」。"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL, OUT = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = browser.new_page(viewport={"width": 1280, "height": 1000}, device_scale_factor=2)
    page.goto(URL)
    page.wait_for_function("() => document.querySelectorAll('#vt-clips tbody.tbody tr td').length > 20", timeout=60000)
    time.sleep(1.5)
    q = page.locator("#vt-find-q textarea, #vt-find-q input").first
    q.fill("借词")
    page.locator("#vt-find-r textarea, #vt-find-r input").first.fill("介词")
    labels = page.locator(".vt-find-bar").inner_text()
    assert "查找（例如：借词）" in labels and "替换成（例如：介词）" in labels, labels
    print("PASS 查找框上面的例子：借词 / 介词")
    q.press("Enter")
    page.wait_for_function("() => (document.querySelector('#vt-find-status') || {}).innerText?.includes('找到 5 处')", timeout=15000)
    time.sleep(0.8)
    page.get_by_role("button", name="⬇ 下一处", exact=True).click()
    page.wait_for_function("() => (document.querySelector('#vt-find-status') || {}).innerText?.includes('现在是第 2 处')", timeout=15000)
    time.sleep(1.0)
    bar = page.locator(".vt-find-bar").bounding_box()
    page.evaluate("y => window.scrollTo(0, y)", bar["y"] + page.evaluate("() => scrollY") - 10)
    time.sleep(0.6)
    bar = page.locator(".vt-find-bar").bounding_box()
    tbl = page.locator("#vt-clips").bounding_box()
    page.screenshot(path=OUT, clip={"x": bar["x"] - 4, "y": bar["y"] - 4, "width": bar["width"] + 8,
                                    "height": tbl["y"] + tbl["height"] - bar["y"] + 8})
    browser.close()
print("ok")
