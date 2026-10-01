"""驱动真实的 VoiceTwin 网页界面（gradio 4.44），截取使用手册需要的截图。"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

M = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(M, "shots")
os.makedirs(OUT, exist_ok=True)
URL = "http://127.0.0.1:7870/"

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
    voice = pg.get_by_label("声音名称（新建请直接输入名字）")
    voice.click(); voice.fill("我的声音"); voice.press("Enter"); pg.keyboard.press("Escape")
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
