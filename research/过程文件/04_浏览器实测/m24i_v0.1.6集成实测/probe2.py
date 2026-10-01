import time

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 1000})
    pg.goto("http://127.0.0.1:7876/", wait_until="networkidle")
    pg.wait_for_timeout(3000)
    pg.get_by_role("tab", name="③ 生成讲课音频").click()
    pg.wait_for_timeout(800)
    pg.get_by_placeholder("大家好，今天我们来学习……").fill("大家好，欢迎回来。今天我们来学习生成器表达式。")
    pg.mouse.click(5, 5)
    pg.get_by_role("button", name="生成", exact=True).click()
    time.sleep(8)
    pg.get_by_role("tab", name="🩺 环境检查").click()
    time.sleep(6)
    tabs = pg.evaluate("""() => [...document.querySelectorAll('button[role=tab]')].map(e => e.innerText.trim() + (e.getAttribute('aria-selected') === 'true' ? ' *' : ''))""")
    print("tabs:", tabs)
    pg.get_by_role("tab", name="⑤ 鉴别").click()
    time.sleep(2)
    tabs = pg.evaluate("""() => [...document.querySelectorAll('button[role=tab]')].map(e => e.innerText.trim() + (e.getAttribute('aria-selected') === 'true' ? ' *' : ''))""")
    print("tabs after:", tabs)
    names = pg.evaluate("""() => [...document.querySelectorAll('button')].filter(e => e.offsetParent !== null).map(e => e.innerText.trim()).slice(0, 40)""")
    print("visible buttons:", names)
    pg.screenshot(path="<草稿目录>/integ_shots/_debug_tab5.png", full_page=False)
    b.close()
