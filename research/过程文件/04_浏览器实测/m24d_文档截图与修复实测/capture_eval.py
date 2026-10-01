"""驱动真实的 VoiceTwin v0.1.6 网页（gradio 4.24，端口 7877，假装有 RTX 4070），截取快速上手和手册要用的截图。

用法：python3 capture_docs.py [步骤...]   步骤：a b c d e f g h i  （不写 = 全部）
"""
import os
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, "shots")
os.makedirs(OUT, exist_ok=True)
URL = "http://127.0.0.1:7877/"
ONLY = set(sys.argv[1:])
SP = os.path.dirname(D)

MAP_JS = r"""
(maps) => {
  const esc = (p) => p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const conv = (s) => {
    for (const [prefix, win] of maps) {
      s = s.replace(new RegExp(esc(prefix) + '([^\\s）)，。"\'<]*)', 'g'), (m, tail) => win + tail.replace(/\//g, '\\'));
    }
    return s;
  };
  document.querySelectorAll('textarea, input[type=text]').forEach(t => { if (t.value.includes('/tmp/')) t.value = conv(t.value); });
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n; while ((n = walker.nextNode())) { if (n.nodeValue.includes('/tmp/')) n.nodeValue = conv(n.nodeValue); }
}
"""
MAPS = [[os.path.join(D, "D:\\讲课素材"), "D:\\讲课素材"],
        [os.path.join(D, "ws"), "D:\\VoiceTwin\\workspace"],
        [os.path.join(D, "fakepy"), "D:\\GPT-SoVITS\\runtime\\python.exe"],
        [os.path.join(D, "GSV"), "D:\\GPT-SoVITS"],
        [D, "D:\\VoiceTwin"]]


def step(k):
    return not ONLY or k in ONLY


def unmap(page):
    page.evaluate(MAP_JS, MAPS)


def union(page, locators, pad):
    boxes = []
    for lc in locators:
        try:
            b = lc.bounding_box()
        except Exception:
            b = None
        if b and b["width"] > 0 and b["height"] > 0:
            boxes.append(b)
    if not boxes:
        raise RuntimeError("nothing to shoot")
    x0 = min(b["x"] for b in boxes) - pad
    y0 = min(b["y"] for b in boxes) - pad
    x1 = max(b["x"] + b["width"] for b in boxes) + pad
    y1 = max(b["y"] + b["height"] for b in boxes) + pad
    return x0, y0, x1, y1


def shot(page, name, locators, pad=12, full_width=False):
    """截下若干组件的并集（整页坐标）。"""
    unmap(page)
    page.wait_for_timeout(300)
    sy = page.evaluate("window.scrollY")
    x0, y0, x1, y1 = union(page, locators, pad)
    if full_width:
        x0, x1 = 0, 1280
    clip = {"x": max(0, x0), "y": max(0, y0 + sy), "width": min(1280, x1) - max(0, x0), "height": y1 - y0}
    page.screenshot(path=os.path.join(OUT, name), clip=clip, full_page=True)
    print("saved", name, {k: int(v) for k, v in clip.items()}, flush=True)


def bar(page):
    return page.locator(".vt-prog:visible").first


def bar_state(page):
    b = bar(page)
    try:
        if not b.count():
            return None, None, -1, None
        return (b.get_attribute("data-status"), b.get_attribute("data-level"),
                int(b.get_attribute("data-pct") or 0), b.get_attribute("data-run"))
    except Exception:
        return None, None, -1, None


def wait_bar(page, timeout_s, mid=None, mid_pct=20, old_run=None):
    t0 = time.time()
    took = False
    while time.time() - t0 < timeout_s:
        st, level, pct, run = bar_state(page)
        if old_run is not None and run == old_run:
            time.sleep(0.3)
            continue
        if st == "running" and mid and not took and pct >= mid_pct:
            try:
                bar(page).scroll_into_view_if_needed(timeout=2000)
                shot(page, mid, [bar(page)], pad=8)
                took = True
            except Exception as exc:  # 进度条正好在重新渲染：下一轮再截
                print("  mid shot retry:", exc, flush=True)
        if st in ("done", "error", "stopped"):
            print(f"  bar -> {st} {level} {pct}% ({time.time() - t0:.0f}s)", flush=True)
            return st
        time.sleep(0.4)
    print("  bar timeout", flush=True)
    return None


def wait_new_done(page, old_runs, timeout_s):
    """等任意一个可见的进度条出现新的（run 不在 old_runs 里）完成 / 出错状态，返回它的序号。"""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        states = page.evaluate("""() => [...document.querySelectorAll('.vt-prog')].filter(e => e.offsetParent !== null)
            .map(e => [e.dataset.status, e.dataset.run])""")
        for i, (st, run) in enumerate(states):
            if run not in old_runs and st in ("done", "error", "stopped"):
                print(f"  bar #{i} -> {st} ({time.time() - t0:.0f}s)", flush=True)
                return i
        time.sleep(0.4)
    print("  wait_new_done timeout", flush=True)
    return None


def runs(page):
    return set(page.evaluate("() => [...document.querySelectorAll('.vt-prog')].map(e => e.dataset.run)"))


def md(page, text):
    return page.locator(".vt-md").filter(has_text=text).first


def block(locator):
    return locator.locator("xpath=ancestor-or-self::div[contains(@class,'block')][1]")


def real_table(page, text):
    return page.locator("table").filter(has_text=text).nth(1)


def tab(page, name):
    t = page.get_by_role("tab", name=name)
    t.click()
    page.wait_for_timeout(1200)
    sel = page.evaluate("() => [...document.querySelectorAll('button[role=tab][aria-selected=true]')].map(e => e.innerText)")
    if name not in "".join(sel):
        t.click()
        page.wait_for_timeout(1200)


def top(page):
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)



import glob
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = b.new_context(viewport={"width": 1280, "height": 1000}, device_scale_factor=2, locale="zh-CN")
    pg = ctx.new_page()
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(4000)
    v = pg.get_by_label("声音名称（新建请直接输入名字）")
    v.click(); v.fill("我的声音"); v.press("Enter"); pg.keyboard.press("Escape"); pg.mouse.click(5, 5)
    pg.wait_for_timeout(2500)
    tab(pg, "④ 试试像不像（可选）")
    wav = sorted(glob.glob(os.path.join(D, "ws", "我的声音", "outputs", "*_未去杂音.wav")))[-1]
    inputs = pg.locator("input[type=file]")
    target = None
    for i in range(inputs.count()):
        el = inputs.nth(i)
        if el.evaluate("e => { const t = e.closest('.block'); return !!t && t.offsetParent !== null && /音频/.test(t.innerText) && !/语速/.test(t.innerText); }"):
            target = el
            break
    print("file input found:", target is not None)
    target.set_input_files(wav)
    pg.wait_for_timeout(2500)
    pg.get_by_label("对应文字（可选，填了会检查错字）").fill("第四课：生成器表达式。大家好，欢迎回来。上节课我们学习了列表推导式，今天我们来学习生成器表达式。它的写法和列表推导式几乎一样，只是把中括号换成了小括号。那么它们有什么区别呢？最大的区别在于，生成器不会一次性把所有结果都放进内存。Let's look at a quick example. 好，我们一起来看一个例子。")
    pg.get_by_role("button", name="评估", exact=True).click()
    res = None
    panel = pg.locator("div[role=tabpanel]:visible").first
    t0 = time.time()
    while time.time() - t0 < 300:
        texts = pg.evaluate("""() => { const p = [...document.querySelectorAll('div[role=tabpanel]')].find(e => e.offsetParent !== null);
            return p ? [...p.querySelectorAll('.prose')].map(e => e.innerText.trim().slice(0, 80)) : []; }""")
        if len(texts) >= 2 and texts[-1] and "上传任意一段音频" not in texts[-1]:
            print("prose in panel:", texts)
            res = panel.locator(".prose").last
            break
        time.sleep(1)
    pg.wait_for_timeout(2000)
    top(pg)
    intro = pg.get_by_text("上传任意一段音频", exact=False).first
    print("result found:", res is not None, (res.inner_text()[:200] if res is not None else ""))
    shot(pg, "07_evaluate.png", [intro, pg.get_by_role("button", name="评估", exact=True)] + ([res] if res is not None else []), pad=12)
    b.close()
print("DONE")
