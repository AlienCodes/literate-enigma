"""verify (⑤) → generate (③) repeatedly; print what the ③ status box says right after clicking 生成."""
import sys
import time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:7877/"
BOX = """(i) => { const boxes = [...document.querySelectorAll('.vt-bar-box')].filter(e => e.offsetParent !== null);
  return boxes.map(e => { const p = e.querySelector('.vt-prog'); return (p ? `[${p.dataset.status} ${p.dataset.pct}% ${p.dataset.run}] ` : '[no bar] ') + e.innerText.trim().replace(/\\s+/g, ' ').slice(0, 120); }); }"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 1000}, locale="zh-CN")
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(3500)
    v = pg.get_by_label("声音名称（新建请直接输入名字）")
    v.click(); v.fill("我的声音"); v.press("Enter"); pg.keyboard.press("Escape"); pg.mouse.click(5, 5)
    pg.wait_for_timeout(2500)
    for rnd in range(int(sys.argv[1]) if len(sys.argv) > 1 else 3):
        pg.get_by_role("tab", name="⑤ 鉴别").click(); pg.wait_for_timeout(800)
        print(f"--- round {rnd}: ⑤ before:", pg.evaluate(BOX))
        pg.get_by_role("button", name="开始鉴别").click()
        t0 = time.time()
        while time.time() - t0 < 120:
            boxes = pg.evaluate(BOX)
            if boxes and boxes[0].startswith("[done"):
                break
            time.sleep(0.3)
        print(f"  verify done after {time.time() - t0:.1f}s:", boxes[:1])
        pg.get_by_role("tab", name="③ 生成讲课音频").click(); pg.wait_for_timeout(1000)
        pg.get_by_placeholder("大家好，今天我们来学习……").fill(f"第 {rnd} 轮测试：同学们好，今天讲一个新的例子。")
        pg.mouse.click(5, 5)
        pg.wait_for_timeout(400)
        print("  ③ before click:", pg.evaluate(BOX))
        pg.get_by_role("button", name="生成", exact=True).click()
        for i in range(12):
            time.sleep(1)
            boxes = pg.evaluate(BOX)
            if i in (0, 2, 5, 11):
                print(f"  t={i}:", boxes)
            if boxes and boxes[0].startswith("[done"):
                print(f"  generate done at t={i}")
                break
    b.close()
