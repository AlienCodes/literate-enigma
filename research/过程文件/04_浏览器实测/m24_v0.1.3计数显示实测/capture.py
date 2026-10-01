"""驱动真实的 VoiceTwin 网页界面（gradio 4.44），截取使用手册需要的截图。"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

M = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(M, "shots")
os.makedirs(OUT, exist_ok=True)
URL = "http://127.0.0.1:7871/"

MAP_JS = """
(maps) => {
  const conv = (s) => {
    for (const [prefix, win] of maps) {
      const esc = prefix.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
      s = s.replace(new RegExp(esc + '([^\\\\s）)，。"]*)', 'g'), (m, tail) => win + tail.replace(/\\//g, '\\\\'));
    }
    return s;
  };
  document.querySelectorAll('textarea').forEach(t => { t.value = conv(t.value); });
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n; while ((n = walker.nextNode())) { if (n.nodeValue.includes('/tmp/')) n.nodeValue = conv(n.nodeValue); }
}
"""
MAPS = [[os.path.join(M, "ws"), "D:\\VoiceTwin\\workspace"],
        [os.path.join(M, "fakepy"), "D:\\GPT-SoVITS\\runtime\\python.exe"],
        [os.path.join(M, "GSV"), "D:\\GPT-SoVITS"],
        [M, "D:\\VoiceTwin"]]


def union_box(page, selectors_or_handles, pad=10):
    boxes = []
    for h in selectors_or_handles:
        b = h.bounding_box()
        if b:
            boxes.append(b)
    x0 = min(b["x"] for b in boxes) - pad
    y0 = min(b["y"] for b in boxes) - pad
    x1 = max(b["x"] + b["width"] for b in boxes) + pad
    y1 = max(b["y"] + b["height"] for b in boxes) + pad
    return {"x": max(0, x0), "y": max(0, y0), "width": x1 - max(0, x0), "height": y1 - max(0, y0)}


def block(page, locator):
    """组件外层容器（gradio 的 .block）。"""
    return locator.element_handle().evaluate_handle("e => e.closest('.block') || e").as_element()


def shot(page, name, handles, pad=10):
    page.evaluate(MAP_JS, MAPS)
    page.evaluate("window.scrollTo(0, 0)")  # bounding_box 是相对视口的，先回到顶部
    page.wait_for_timeout(400)
    clip = union_box(page, handles, pad)
    page.screenshot(path=os.path.join(OUT, name), clip=clip, full_page=True)
    print("saved", name, {k: int(v) for k, v in clip.items()})


def wait_text(page, text, timeout_s):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if page.get_by_text(text, exact=False).count() > 0:
            return True
        time.sleep(2)
    raise TimeoutError(text)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 1000}, device_scale_factor=2)
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(1500)

    # ---------- ① 准备素材：填写
    voice = pg.get_by_label("声音名称（新建请直接输入名字）")
    voice.click()
    voice.fill("我的声音")
    voice.press("Enter")
    pg.keyboard.press("Escape")
    pg.get_by_placeholder("例如 D:\\讲课视频").fill("D:\\讲课素材")
    pg.mouse.click(5, 5)
    pg.wait_for_timeout(500)
    title = pg.get_by_text("声音分身 VoiceTwin").first
    start_btn = pg.get_by_role("button", name="开始准备素材")
    shot(pg, "01_prepare_form.png", [title.element_handle(), start_btn.element_handle()], pad=16)

    # ---------- ① 准备素材：运行
    start_btn.click()
    wait_text(pg, "素材准备完成：保留", 1200)
    pg.wait_for_timeout(1500)
    log_block = block(pg, pg.get_by_label("运行日志"))
    summary = pg.get_by_text("素材准备完成：保留").first.element_handle().evaluate_handle(
        "e => e.closest('.prose') || e.closest('.block') || e").as_element()
    shot(pg, "02_prepare_done.png", [log_block, summary], pad=12)

    # ---------- 校对表
    pg.get_by_role("button", name="载入片段列表").click()
    pg.wait_for_timeout(2500)
    heading = pg.get_by_text("校对文字（可选，但能明显提升效果）").first
    cells = pg.locator("table tbody tr")
    print("rows:", cells.count())
    cells.nth(2).locator("td").nth(4).click()
    pg.wait_for_timeout(2500)
    pg.keyboard.press("Escape")
    audio_block = block(pg, pg.get_by_text("试听选中的片段").first)
    shot(pg, "03_proofread.png", [heading.element_handle(), audio_block], pad=12)

    # ---------- ② 训练
    pg.get_by_role("tab", name="② 训练模型").click()
    pg.wait_for_timeout(800)
    pg.get_by_role("button", name="开始训练").click()
    wait_text(pg, "训练完成，最佳模型", 1800)
    pg.wait_for_timeout(1500)
    intro = pg.get_by_text("GPT-SoVITS").first
    train_log = block(pg, pg.get_by_label("训练日志"))
    done = pg.get_by_text("训练完成，最佳模型").first.element_handle().evaluate_handle(
        "e => e.closest('.prose') || e").as_element()
    shot(pg, "04_train_done.png", [intro.element_handle(), train_log, done], pad=12)

    # ---------- ③ 生成：填写
    pg.get_by_role("tab", name="③ 生成讲课音频").click()
    pg.wait_for_timeout(800)
    script = ("# 第四课：生成器表达式\n\n"
              "大家好，欢迎回来。上节课我们学习了列表推导式，今天我们来学习生成器表达式。\n\n"
              "生成器表达式的写法和列表推导式几乎一样，只是把中括号换成了小括号。那么它们有什么区别呢？[停顿=1.5]\n\n"
              "最大的区别在于，生成器不会一次性把所有结果都放进内存。\n\n"
              "Let's look at a quick example.")
    pg.get_by_placeholder("大家好，今天我们来学习……").fill(script)
    pg.mouse.click(5, 5)
    gen_btn = pg.get_by_role("button", name="生成")
    tip = pg.get_by_text("粘贴讲稿或上传讲稿文件").first
    shot(pg, "05_generate_form.png", [tip.element_handle(), gen_btn.element_handle()], pad=14)

    # ---------- ③ 生成：结果
    gen_btn.click()
    wait_text(pg, "✅ 完成：", 900)
    pg.wait_for_timeout(2500)
    result_block = block(pg, pg.get_by_text("结果", exact=True).first)
    table = pg.get_by_text("✅ 完成：").first.element_handle().evaluate_handle(
        "e => e.closest('.prose') || e").as_element()
    shot(pg, "06_generate_done.png", [result_block, table], pad=12)

    # ---------- ④ 评估
    outputs = os.path.join(M, "ws", "我的声音", "outputs")
    wavs = sorted(f for f in os.listdir(outputs) if f.endswith(".wav"))
    pg.get_by_role("tab", name="④ 评估相似度").click()
    pg.wait_for_timeout(800)
    pg.locator("input[type=file]").nth(3).set_input_files(os.path.join(outputs, wavs[-1]))
    pg.wait_for_timeout(1500)
    pg.get_by_role("button", name="评估").click()
    wait_text(pg, "声纹相似度", 300)
    pg.wait_for_timeout(1000)
    ev_intro = pg.get_by_text("上传任意一段音频").first
    ev_out = block(pg, pg.get_by_text("声纹相似度").first)
    shot(pg, "07_evaluate.png", [ev_intro.element_handle(), ev_out], pad=12)
    b.close()
print("done")
