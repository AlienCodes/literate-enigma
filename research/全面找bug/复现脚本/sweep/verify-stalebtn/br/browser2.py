"""Reporter's exact sequence in the real page: delete a row, run one-click (button grey), 撤销删除 that row."""
import time, re
exec(open("browser.py").read().split("with sync_playwright() as p:")[0])
ROW = "第1课_x_0005"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = b.new_page(viewport={"width": 1366, "height": 900})
    page.goto(URL); page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000); time.sleep(3)
    btn = page.locator("#vt-tr-btn")
    print("A load: disabled =", btn.is_disabled(), "| backend =", backend_used())
    menu_cell(page, ROW).click()
    page.locator(".vt-menu button", has_text="删除这一行").click()
    page.locator(".vt-menu button", has_text="确定删除").click()
    wait(lambda: manifest()[ROW].get("deleted") is True); time.sleep(2)
    btn.click()
    wait(lambda: "一键全部文字校正完成" in page.locator("body").inner_text(), 120); time.sleep(3)
    print("B after one-click: disabled =", btn.is_disabled(), "| backend =", backend_used())
    menu_cell(page, ROW).click()
    page.locator(".vt-menu button", has_text="撤销删除").click()
    wait(lambda: not manifest()[ROW].get("deleted")); time.sleep(3)
    print("C after 撤销删除: disabled =", btn.is_disabled(), "| backend =", backend_used(),
          "| info says locked:", "只能用一次" in page.locator(".prose.vt-tr-info").inner_text())
    btn.click(timeout=3000, trial=True) if not btn.is_disabled() else None
    page.reload(); page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000); time.sleep(3)
    print("D after reload: disabled =", page.locator("#vt-tr-btn").is_disabled())
    b.close()
