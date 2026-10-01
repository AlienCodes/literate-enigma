import time, os
from playwright.sync_api import sync_playwright
def wait_text(pg, t, s):
    t0=time.time()
    while time.time()-t0 < s:
        if pg.get_by_text(t, exact=False).count(): return True
        time.sleep(2)
    return False
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 1000})
    pg.goto("http://127.0.0.1:7871/", wait_until="networkidle"); pg.wait_for_timeout(2000)
    pg.get_by_role("tab", name="② 训练模型").click(); pg.wait_for_timeout(800)
    pg.get_by_role("button", name="开始训练").click()
    print("train done:", wait_text(pg, "训练完成，最佳模型", 1500))
    pg.get_by_role("tab", name="③ 生成讲课音频").click(); pg.wait_for_timeout(800)
    pg.get_by_placeholder("大家好，今天我们来学习……").fill("大家好，欢迎回来。今天我们来学习生成器表达式。那么它和列表推导式有什么区别呢？")
    pg.mouse.click(5,5)
    pg.get_by_role("button", name="生成").click()
    print("generate done:", wait_text(pg, "✅ 完成：", 900))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ws", "我的声音", "outputs")
    wavs = sorted(f for f in os.listdir(out) if f.endswith(".wav"))
    pg.get_by_role("tab", name="④ 评估相似度").click(); pg.wait_for_timeout(800)
    pg.locator("input[type=file]").nth(3).set_input_files(os.path.join(out, wavs[-1])); pg.wait_for_timeout(1500)
    pg.get_by_role("button", name="评估").click()
    print("evaluate done:", wait_text(pg, "声纹相似度", 300))
    b.close()
