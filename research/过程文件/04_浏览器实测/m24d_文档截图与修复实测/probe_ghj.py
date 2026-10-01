"""Reproduce: error in ③ → verify in ⑤ → generate in ③ does nothing?"""
import time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:7877/"


def bars(pg):
    return pg.evaluate("""() => [...document.querySelectorAll('.vt-prog')].map(e => ({vis: e.offsetParent !== null,
        st: e.dataset.status, pct: e.dataset.pct, run: (e.dataset.run || '').slice(0, 6)}))""")


def gen_btn_state(pg):
    return pg.evaluate("""() => [...document.querySelectorAll('button')].filter(b => /生成/.test(b.innerText) && b.offsetParent !== null)
        .map(b => b.innerText.trim().slice(0, 14) + (b.disabled ? ' [disabled]' : ''))""")


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 1000}, locale="zh-CN")
    pg.on("console", lambda m: print("CONSOLE", m.type, m.text[:200]) if m.type in ("error", "warning") else None)
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(3500)
    v = pg.get_by_label("声音名称（新建请直接输入名字）")
    v.click(); v.fill("我的声音"); v.press("Enter"); pg.keyboard.press("Escape"); pg.mouse.click(5, 5)
    pg.wait_for_timeout(2500)
    pg.get_by_role("tab", name="③ 生成讲课音频").click(); pg.wait_for_timeout(1000)
    pg.get_by_placeholder("大家好，今天我们来学习……").fill("…… ！！ ——"); pg.mouse.click(5, 5)
    pg.get_by_role("button", name="生成", exact=True).click()
    for i in range(30):
        time.sleep(1)
        bs = [x for x in bars(pg) if x["vis"]]
        if bs and bs[0]["st"] == "error":
            break
    print("after g:", bars(pg), gen_btn_state(pg))
    pg.get_by_role("tab", name="⑤ 鉴别").click(); pg.wait_for_timeout(1000)
    pg.get_by_role("button", name="开始鉴别").click()
    for i in range(120):
        time.sleep(1)
        bs = [x for x in bars(pg) if x["vis"]]
        if bs and bs[0]["st"] == "done":
            break
    print("after h:", bars(pg))
    pg.get_by_role("tab", name="③ 生成讲课音频").click(); pg.wait_for_timeout(1000)
    print("on ③:", bars(pg), gen_btn_state(pg))
    pg.get_by_placeholder("大家好，今天我们来学习……").fill("同学们好，今天讲一个新的例子。请大家先想一想。"); pg.mouse.click(5, 5)
    pg.locator("label", has_text="完美：每句最多试 20 次").first.click(); pg.wait_for_timeout(500)
    btn = pg.get_by_role("button", name="生成", exact=True)
    print("gen button count:", btn.count(), "visible:", btn.is_visible() if btn.count() else None)
    btn.click()
    for i in range(40):
        time.sleep(1)
        if i % 4 == 0:
            print(f"t={i}", [x for x in bars(pg) if x["vis"]], pg.evaluate("""() => [...document.querySelectorAll('.vt-bar-box')]
                .filter(e => e.offsetParent !== null).map(e => e.innerText.trim().slice(0, 200))"""))
    b.close()
