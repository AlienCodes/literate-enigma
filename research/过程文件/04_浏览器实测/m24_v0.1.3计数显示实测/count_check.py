import time
from playwright.sync_api import sync_playwright
def wait_text(pg, t, s):
    t0=time.time()
    while time.time()-t0 < s:
        if pg.get_by_text(t, exact=False).count(): return
        time.sleep(2)
    raise TimeoutError(t)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 1000}, device_scale_factor=2)
    pg.goto("http://127.0.0.1:7871/", wait_until="networkidle"); pg.wait_for_timeout(1500)
    v = pg.get_by_label("声音名称（新建请直接输入名字）"); v.click(); v.fill("我的声音"); v.press("Enter"); pg.keyboard.press("Escape")
    pg.get_by_placeholder("例如 D:\\讲课视频").fill("D:\\讲课素材"); pg.mouse.click(5,5)
    pg.get_by_role("button", name="开始准备素材").click()
    wait_text(pg, "素材准备完成：保留", 900); wait_text(pg, "一共", 60); pg.wait_for_timeout(2000)
    count = pg.get_by_text("一共", exact=False).first
    print("COUNT:", count.inner_text())
    print("rows in table:", pg.locator("table tbody tr").count())
    count.scroll_into_view_if_needed(); pg.wait_for_timeout(500)
    box = count.bounding_box(); pg.screenshot(path="count.png", clip={"x":0,"y":max(0,box["y"]-60),"width":1280,"height":520})
    pg.get_by_role("button", name="保存修改").click(); wait_text(pg, "已保存", 120); pg.wait_for_timeout(1500)
    print("SAVED:", pg.get_by_text("已保存", exact=False).first.inner_text()[:80])
    print("COUNT after save:", pg.get_by_text("一共", exact=False).first.inner_text())
    b.close()
