import time, sys
from playwright.sync_api import sync_playwright
def wait_text(pg, t, s):
    t0=time.time()
    while time.time()-t0 < s:
        if pg.get_by_text(t, exact=False).count(): return True
        time.sleep(1)
    return False
mode = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 1000})
    pg.goto("http://127.0.0.1:7871/", wait_until="networkidle"); pg.wait_for_timeout(1500)
    if mode == "typed":
        v = pg.get_by_label("声音名称（新建请直接输入名字）"); v.click(); v.fill("我的声音"); v.press("Enter"); pg.keyboard.press("Escape")
        pg.mouse.click(5,5)
    pg.get_by_role("button", name="载入片段列表").click(); pg.wait_for_timeout(3000)
    print(mode, "count shown:", wait_text(pg, "一共", 20))
    pg.get_by_role("button", name="保存修改").click()
    print(mode, "saved:", wait_text(pg, "已保存", 60))
    b.close()
