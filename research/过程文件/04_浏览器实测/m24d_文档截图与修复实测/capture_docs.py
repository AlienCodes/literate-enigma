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
MAPS = [[os.path.join(SP, "gsv39", "lib", "python3.9", "site-packages"), "D:\\GPT-SoVITS\\runtime\\Lib\\site-packages"],
        [os.path.join(SP, "gsv39"), "D:\\GPT-SoVITS\\runtime"],
        [os.path.join(D, "D:\\讲课素材"), "D:\\讲课素材"],
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


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = b.new_context(viewport={"width": 1280, "height": 1000}, device_scale_factor=2, locale="zh-CN")
    pg = ctx.new_page()
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(4000)
    if ONLY and "a" not in ONLY:  # 从中间开始时也要先选中声音
        v = pg.get_by_label("声音名称（新建请直接输入名字）")
        v.click()
        v.fill("我的声音")
        v.press("Enter")
        pg.keyboard.press("Escape")
        pg.mouse.click(5, 5)
        pg.wait_for_timeout(2500)

    # ------------------------------------------------------------ a: 首页（显卡状态 + 声音名称 + ① 表单）
    if step("a"):
        v = pg.get_by_label("声音名称（新建请直接输入名字）")
        v.click()
        v.fill("我的声音")
        v.press("Enter")
        pg.keyboard.press("Escape")
        pg.get_by_placeholder("例如 D:\\讲课视频").fill("D:\\讲课素材")
        pg.mouse.click(5, 5)
        pg.wait_for_timeout(1200)
        top(pg)
        shot(pg, "00_gpu_badge.png", [pg.locator(".vt-gpu").first, pg.get_by_role("button", name="🔄 重新检查显卡")], pad=10)
        shot(pg, "01_prepare_form.png", [pg.locator(".vt-header").first,
                                         pg.get_by_role("button", name="开始准备素材")], pad=14)

    # ------------------------------------------------------------ b: 准备素材（进度条 + 完成）
    if step("b"):
        pg.get_by_role("button", name="开始准备素材").click()
        wait_bar(pg, 1200, mid="02a_progress_running.png", mid_pct=25)
        pg.wait_for_timeout(2500)
        top(pg)
        shot(pg, "02_prepare_done.png", [bar(pg), md(pg, "素材准备好了")], pad=12)

    # ------------------------------------------------------------ c: 校对（数量 + 红字 + 建议）
    if step("c"):
        subprocess.run([sys.executable, os.path.join(D, "inject_typos.py")], check=True)
        pg.get_by_role("button", name="🔄 重新载入").click()
        pg.wait_for_timeout(3000)
        old = bar_state(pg)[3]
        pg.get_by_role("button", name="🔍 自动查找可能的错字").click()
        wait_bar(pg, 600, old_run=old)
        pg.wait_for_timeout(2500)
        print("  red spans:", pg.locator("table span[style*='#dc2626']").count())
        shot(pg, "03a_proofcheck_done.png", [bar(pg), md(pg, "检查完了")], pad=12)
        pg.get_by_label("只看可能有错的").check()
        pg.wait_for_timeout(3000)
        tbl = real_table(pg, "可能有错（红色）")
        tbl.locator("tbody tr").first.locator("td").nth(5).click()
        pg.wait_for_timeout(3000)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(500)
        top(pg)
        heading = pg.get_by_role("button", name="🔍 自动查找可能的错字")
        diff = pg.locator(".vt-diff").first
        adopt = pg.get_by_role("button", name="✅ 采用建议")
        parts = [md(pg, "📊"), heading, tbl, diff] + ([adopt] if adopt.count() and adopt.is_visible() else [])
        shot(pg, "03_proofread.png", parts, pad=12)

    # ------------------------------------------------------------ d: 训练
    if step("d"):
        tab(pg, "② 训练模型")
        top(pg)
        plan = md(pg, "电脑会自动这样训练")
        if not plan.count():
            plan = pg.get_by_text("电脑会自动这样训练", exact=False).first
        shot(pg, "04a_train_plan.png", [plan, pg.get_by_role("button", name="开始训练")], pad=12)
        pg.get_by_role("button", name="开始训练").click()
        wait_bar(pg, 2400, mid="04b_train_running.png", mid_pct=40)
        pg.wait_for_timeout(3000)
        top(pg)
        shot(pg, "04_train_done.png", [bar(pg), md(pg, "训练完成")], pad=12)

    # ------------------------------------------------------------ e: 生成（表单 + 完美档两个版本 + 结果表）
    if step("e"):
        tab(pg, "③ 生成讲课音频")
        script = ("# 第四课：生成器表达式\n\n"
                  "大家好，欢迎回来。上节课我们学习了列表推导式，今天我们来学习生成器表达式。\n\n"
                  "它的写法和列表推导式几乎一样，只是把中括号换成了小括号。那么它们有什么区别呢？[停顿=1.5]\n\n"
                  "最大的区别在于，生成器不会一次性把所有结果都放进内存。\n\n"
                  "Let's look at a quick example. 好，我们一起来看一个例子。")
        pg.get_by_placeholder("大家好，今天我们来学习……").fill(script)
        pg.mouse.click(5, 5)
        pg.wait_for_timeout(800)
        checked = pg.evaluate("""() => [...document.querySelectorAll('input[type=radio]:checked')]
            .filter(e => e.offsetParent !== null).map(e => e.closest('label') ? e.closest('label').innerText.trim() : e.value)""")
        print("  checked radios:", checked)
        top(pg)
        gen_btn = pg.get_by_role("button", name="生成", exact=True)
        intro = pg.get_by_label("讲稿")
        shot(pg, "05_generate_form.png", [block(intro), gen_btn,
                                          block(pg.get_by_label("只重新生成第几句（例如 3,5,8-10；留空 = 全部）"))], pad=14)
        speed = block(pg.locator("input[type=range]").first)
        shot(pg, "05b_speed_slider.png", [speed, pg.get_by_role("button", name="▶ 试听语速")], pad=10)
        old = bar_state(pg)[3]
        gen_btn.click()
        wait_bar(pg, 2400, mid="05c_generate_running.png", mid_pct=30, old_run=old)
        pg.wait_for_timeout(3000)
        top(pg)
        shot(pg, "06_generate_done.png", [bar(pg), md(pg, "生成好了"), block(pg.get_by_label("结果"))], pad=12)
        var = md(pg, "这次做了两个版本")
        if var.count():
            radio = block(pg.get_by_text("最终使用哪个版本", exact=False).first)
            shot(pg, "06c_two_versions.png", [var, block(pg.get_by_label("版本 A：未去杂音")), radio], pad=12)
        files = block(pg.get_by_text("下载（音频 / 字幕）", exact=False).first)
        shot(pg, "06b_download.png", [block(pg.get_by_label("结果")), files], pad=12)
        tbl = real_table(pg, "像你本人（%）")
        shot(pg, "06d_result_table.png", [tbl], pad=10)

    # ------------------------------------------------------------ f: ④ 试试像不像
    if step("f"):
        tab(pg, "④ 试试像不像（可选）")
        pg.get_by_role("button", name="📥 评估刚才生成的音频").click()
        pg.wait_for_timeout(1500)
        t0 = time.time()
        while time.time() - t0 < 300 and not pg.get_by_text("像你本人", exact=False).count():
            time.sleep(1)
        pg.wait_for_timeout(3000)
        top(pg)
        ev_res = pg.locator(".vt-md:visible").last
        shot(pg, "07_evaluate.png", [block(pg.get_by_label("音频")), pg.get_by_role("button", name="评估", exact=True), ev_res], pad=12)

    # ------------------------------------------------------------ g: ⑤ 鉴别 + 盲听
    if step("g"):
        tab(pg, "⑤ 鉴别")
        pg.get_by_role("button", name="开始鉴别").click()
        wait_bar(pg, 900)
        pg.wait_for_timeout(2500)
        top(pg)
        vt = real_table(pg, "综合 %")
        shot(pg, "08_verify.png", [pg.get_by_text("机器鉴别", exact=False).first, bar(pg), md(pg, "鉴别完成"), vt], pad=12)
        n = pg.get_by_label("用几句话（真人和生成的各这么多段）")
        try:
            n.fill("4")
            n.press("Enter")
        except Exception:
            pass
        old = runs(pg)
        pg.get_by_role("button", name="生成盲听测试").click()
        wait_new_done(pg, old, 900)
        pg.wait_for_timeout(3000)
        top(pg)
        parts = [pg.get_by_text("观众盲听测试", exact=False).first, md(pg, "盲听")]
        aud = pg.get_by_label("第 2 段是：")
        if aud.count():
            parts.append(block(aud))
        shot(pg, "08b_blind_test.png", parts, pad=12)

    # ------------------------------------------------------------ h: 环境检查
    if step("h"):
        tab(pg, "🩺 环境检查")
        t0 = time.time()
        while time.time() - t0 < 120 and not pg.get_by_text("共 ", exact=False).count():
            time.sleep(1)
        pg.wait_for_timeout(4000)
        top(pg)
        doc = pg.locator("table").filter(has_text="说明").filter(has_text="项目").nth(1)
        shot(pg, "10_doctor.png", [pg.get_by_role("button", name="🔄 重新检查（约 10~30 秒）"), doc], pad=12)

    # ------------------------------------------------------------ i: 声音库 + 出错时的红色进度条
    if step("i"):
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(4500)
        acc = pg.get_by_text("我的声音库（共", exact=False).first
        tbl = real_table(pg, "最后修改时间")
        if not tbl.is_visible():
            acc.click()
            pg.wait_for_timeout(1500)
        top(pg)
        shot(pg, "00b_voice_library.png", [acc, tbl], pad=12)
        tab(pg, "③ 生成讲课音频")
        pg.get_by_placeholder("大家好，今天我们来学习……").fill("…… ！！ ——")
        pg.mouse.click(5, 5)
        old = bar_state(pg)[3]
        pg.get_by_role("button", name="生成", exact=True).click()
        wait_bar(pg, 300, old_run=old)
        pg.wait_for_timeout(2000)
        top(pg)
        err = md(pg, "生成没有完成")
        shot(pg, "09_error_red.png", [bar(pg)] + ([err] if err.count() else []), pad=12)
    b.close()
print("DONE")
