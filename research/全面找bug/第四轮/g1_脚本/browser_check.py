"""第四轮 g1：真实浏览器（gradio 4.24、Chromium）里点一遍修好的几处。用法：python3 check.py <仓库> <工作文件夹> <网址>"""
import json
import os
import shutil
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO, WORK, URL = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, REPO)
os.chdir(WORK)
from voicetwin.config import load_config  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review  # noqa: E402
try:
    from voicetwin.webui.app import _edit_key  # noqa: E402
except ImportError:  # 修以前的代码（对照用）
    import re as _re

    from voicetwin.utils.textutil import clean_transcript as _ct

    def _edit_key(t):
        return _re.sub(r"\s+", "", _ct(str(t or "")))

cfg = load_config()
project = wf.Project(cfg, "我的声音")
VOICE = project.root
IDS = [r["id"] for r in project.load_manifest()]
RES = []
SHOTS = Path(__file__).resolve().parent / "shots"
LOG = Path(__file__).resolve().parent / "webui.log"
SHOTS.mkdir(exist_ok=True)


def check(name, ok, detail=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)


def draft():
    p = VOICE / "review_draft.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def rejected():
    p = VOICE / "review_rejected.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


FIND = """(a) => { const rows = document.querySelectorAll('#vt-clips tbody.tbody tr');
  for (const tr of rows) { const tds = Array.from(tr.children).filter(x => x.tagName === 'TD');
    if (tds[1] && tds[1].innerText.trim() === a[0]) { const td = tds[a[1]]; const el = a[2] ? td.querySelector(a[2]) : td;
      if (!el) return null; const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
      return {x: r.x + r.width / 2, y: r.y + r.height / 2, text: el.innerText, cls: el.className || '',
              bg: cs.backgroundColor, color: cs.color, html: td.innerHTML}; } }
  return null; }"""


SCROLL = """(want) => { const sc = Array.from(document.querySelectorAll('#vt-clips *')).find(
    (e) => e.scrollHeight > e.clientHeight + 20 && /(auto|scroll)/.test(getComputedStyle(e).overflowY));
  if (!sc) return 'no-scroller';
  const nos = Array.from(document.querySelectorAll('#vt-clips tbody.tbody tr')).map(
    (tr) => Number((Array.from(tr.children).filter(x => x.tagName === 'TD')[0] || {}).innerText)).filter(x => x > 0);
  const up = nos.length && want < Math.min.apply(null, nos);
  sc.scrollTop = Math.max(0, sc.scrollTop + (up ? -1 : 1) * sc.clientHeight * 0.4); return 'ok'; }"""


def cell(page, rid, col, sel=None):
    for _ in range(40):
        c = page.evaluate(FIND, [rid, col, sel])
        if c is not None:
            if c["y"] < 40 or c["y"] > 960:  # 在表格里，但不在屏幕上：把页面滚过去
                page.evaluate(FIND.replace("const r = el.getBoundingClientRect()", "el.scrollIntoView({block: 'center'}); const r = el.getBoundingClientRect()"), [rid, col, sel])
                page.wait_for_timeout(200)
                c = page.evaluate(FIND, [rid, col, sel])
            return c
        if sel and page.evaluate(FIND, [rid, col, None]) is not None:
            return None  # 这一行在，只是没有这个东西
        page.evaluate(SCROLL, IDS.index(rid) + 1)
        page.wait_for_timeout(150)
    return None


HIT = """(a) => { const el = document.elementFromPoint(a[0], a[1]); const tr = el && el.closest ? el.closest('tr') : null;
  if (!tr) return ''; const tds = Array.from(tr.children).filter(x => x.tagName === 'TD');
  return tds[1] ? tds[1].innerText.trim() : ''; }"""


def click(page, rid, col, sel=None, double=False):
    """点那一行的那一格（先确认鼠标下面真的是这一行：表格是虚拟滚动的，滚动以后同一个位置可能是别的行）。"""
    for _ in range(20):
        c = cell(page, rid, col, sel)
        if c and page.evaluate(HIT, [c["x"], c["y"]]) == rid:
            (page.mouse.dblclick if double else page.mouse.click)(c["x"], c["y"])
            return c
        page.wait_for_timeout(200)
    raise RuntimeError(f"找不到第 {rid} 行的格子")


def msg(page):
    return page.evaluate("() => (document.querySelector('.vt-clip-msg') || {}).innerText || ''")


def wait_msg(page, needle, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        m = msg(page)
        if needle in m:
            return m
        page.wait_for_timeout(200)
    return msg(page)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        ctx = browser.new_context(viewport={"width": 1500, "height": 1000}, accept_downloads=True, locale="en-US")
        page = ctx.new_page()
        errors, downloads = [], []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("download", lambda d: downloads.append(d.suggested_filename))
        sent = []

        def on_req(r):
            if "/queue/join" in r.url and r.post_data and "action" in r.post_data:
                try:
                    sent.append([x for x in json.loads(r.post_data).get("data", []) if isinstance(x, str) and "action" in x])
                except Exception:
                    pass
        page.on("request", on_req)
        page.goto(URL)
        page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
        page.wait_for_timeout(1500)
        page.locator("#vt-clips").scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        # 0) 网页上显示出来的字和存的字：按同样的方法整理以后一样（不会冤枉成「被改过了」）
        recs = {r["id"]: r for r in project.load_manifest()}
        bad = []
        for rid in IDS[6:11]:
            c = cell(page, rid, 4)
            if not c or _edit_key(c["text"]) != _edit_key(recs[rid]["text"]):
                bad.append((rid, c and c["text"], recs[rid]["text"]))
        check("markdown 样子的句子：网页上显示的字整理后和存的一样", not bad, str(bad))
        rid = IDS[6]
        c = click(page, rid, 4, double=True)
        page.wait_for_selector(".vt-editor-text")
        page.keyboard.press("End")
        page.keyboard.type("吧")
        page.keyboard.press("Enter")
        m = wait_msg(page, "改好了")
        check("这种句子照常能改（没有被当成「被改过了」）", "改好了" in m and draft().get(rid, {}).get("text", "").endswith("吧"), m[:80])

        # 1) 编辑框开着的时候这一句被改过（另一个网页 / 一键校正）：按回车不把旧句子存回去，也不记撤销
        r0 = IDS[0]
        c = click(page, r0, 4, double=True)
        page.wait_for_selector(".vt-editor-text")
        before = page.evaluate("() => document.querySelector('.vt-editor-text').value")
        review.adopt_suggestion(project, r0)  # 后台把这一句改了
        page.keyboard.press("End")
        page.keyboard.type("吧")
        page.keyboard.press("Enter")
        m = wait_msg(page, "没有存上")
        d0 = draft().get(r0, {}).get("text")
        check("编辑框里是旧的句子", before == "我们今天学习定语从句。", before)
        check("按回车：提示「没有存上」，刚改好的字还在", "没有存上" in m and d0 == "我们今天学习状语从句。", f"{m[:60]} / {d0}")
        check("没有记成老师撤销的改法", not rejected().get(r0), str(rejected()))
        page.wait_for_timeout(800)
        c = cell(page, r0, 4)
        check("表格里显示的是改过以后的句子", c and "状语" in c["text"], c and c["text"])
        click(page, r0, 4, double=True)
        page.wait_for_selector(".vt-editor-text")
        page.keyboard.press("End")
        page.keyboard.type("呢")
        page.keyboard.press("Enter")
        m = wait_msg(page, "改好了")
        check("再双击、在新的句子上改：存上了", draft().get(r0, {}).get("text") == "我们今天学习状语从句。呢", str(draft().get(r0)))
        page.screenshot(path=str(SHOTS / "1_stale_edit.png"))

        # 2) 被拒绝的「采用」：一句说明（没有 ❌ / ValueError），⏳ 放回「采用」，还能再点
        r1 = IDS[1]
        b = click(page, r1, 6, ".vt-sug-btn")
        m = wait_msg(page, "没有改")
        page.wait_for_timeout(1500)
        b2 = cell(page, r1, 6, ".vt-sug-btn")
        check("拒绝时是 ⚠️ 说明，不是 ❌ / 英文", m.startswith("⚠️") and "❌" not in m and "ValueError" not in m, m[:80])
        check("按钮放回「采用」、不再是 ⏳", b2 and b2["text"] == "采用" and "vt-sug-busy" not in b2["cls"], str(b2 and (b2["text"], b2["cls"])))
        n_log = LOG.read_text(encoding="utf-8", errors="replace").count("校对表「adopt」没有改")
        click(page, r1, 6, ".vt-sug-btn")
        page.wait_for_timeout(2500)
        n_log2 = LOG.read_text(encoding="utf-8", errors="replace").count("校对表「adopt」没有改")
        b3 = cell(page, r1, 6, ".vt-sug-btn")
        check("再点一次：后台又处理了一次，按钮又放回来", n_log2 == n_log + 1 and b3["text"] == "采用"
              and "vt-sug-busy" not in b3["cls"], f"{n_log}->{n_log2} {b3 and b3['text']}")
        page.screenshot(path=str(SHOTS / "2_refused_adopt.png"))

        # 3) 连着点两行的「采用」：两行都变成红的「已采用」
        r2, r3 = IDS[2], IDS[3]
        b = click(page, r2, 6, ".vt-sug-btn")
        b = click(page, r3, 6, ".vt-sug-btn")
        page.wait_for_timeout(3000)
        print("送出去的操作：", *sent[-4:], sep="\n  ")
        s2, s3 = cell(page, r2, 6, ".vt-sug-btn"), cell(page, r3, 6, ".vt-sug-btn")
        check("连着点两行：都变成「已采用」", s2["text"] == "已采用" and s3["text"] == "已采用"
              and "vt-sug-red" in s2["cls"] and "vt-sug-red" in s3["cls"], f"{s2['text']} {s3['text']}")
        check("两行的字都改好了", "介词" in draft().get(r2, {}).get("text", "") and draft().get(r3, {}).get("text", "").startswith("as"))

        # 4) 草稿文件一时读不了：说明「等几秒再点一次」，按钮能再点；文件好了再点就采用上了
        r4 = IDS[4]
        dp = VOICE / "review_draft.json"
        keep = dp.read_bytes()
        dp.unlink()
        dp.mkdir()
        b = click(page, r4, 6, ".vt-sug-btn")
        m = wait_msg(page, "等几秒")
        page.wait_for_timeout(1500)
        b2 = cell(page, r4, 6, ".vt-sug-btn")
        check("文件读不了：提示等几秒再点（⚠️ 说明，不是 ❌ 和英文技术细节）", "等几秒" in m and m.startswith("⚠️")
              and "技术细节" not in m, m[:80])
        check("按钮放回「采用」（能照提示再点）", b2["text"] == "采用" and "vt-sug-busy" not in b2["cls"], b2["text"])
        dp.rmdir()
        dp.write_bytes(keep)
        click(page, r4, 6, ".vt-sug-btn")
        page.wait_for_timeout(2500)
        b3 = cell(page, r4, 6, ".vt-sug-btn")
        check("文件好了以后再点：采用上了", b3["text"] == "已采用" and "介词" in draft().get(r4, {}).get("text", ""), b3["text"])

        # 5) 下载改好的文字：失败时不再自动下载上一次的旧文件
        page.click("#vt-dl-txt-btn")
        page.wait_for_timeout(2500)
        n1 = len(downloads)
        check("第一次下载成功", n1 == 1, str(downloads))
        keep = dp.read_bytes()
        dp.unlink()
        dp.mkdir()
        page.click("#vt-dl-txt-btn")
        page.wait_for_timeout(3000)
        body = page.evaluate("() => document.body.innerText")
        check("下载失败：提示没有完成，也没有又下载旧文件", "没有完成" in body and len(downloads) == n1, str(downloads))
        dp.rmdir()
        dp.write_bytes(keep)

        # 6) 确认训练素材：页面顶部的「当前声音状态」跟着变
        top0 = page.evaluate("() => document.body.innerText.split('\\n').find(l => l.includes('① 素材')) || ''")
        page.get_by_role("button", name="✅ 确认训练素材").click()
        page.wait_for_timeout(4000)
        top1 = page.evaluate("() => document.body.innerText.split('\\n').find(l => l.includes('① 素材')) || ''")
        check("确认前顶部说去确认", "确认训练素材" in top0, top0)
        check("确认以后顶部说去训练", "去「② 训练模型」点「开始训练」" in top1 and "确认训练素材" not in top1, top1)

        # 7) 灰色的行里查找：橙色看得见，行号照样不显示；灰色行的「采用」按钮还是蓝色
        page.fill("#vt-find-q textarea, #vt-find-q input", "借词")
        page.get_by_role("button", name="🔍 查找").click()
        page.wait_for_timeout(3000)
        r5 = IDS[5]
        cur = cell(page, r5, 4, ".vt-find-cur")
        num = cell(page, r5, 0, "*") or cell(page, r5, 0)
        sug = cell(page, r5, 6, ".vt-sug-btn")
        check("灰色的行：现在这一处是橙色", cur and cur["bg"] == "rgb(249, 115, 22)", str(cur and (cur["bg"], cur["color"])))
        check("灰色的行：行号照样不显示", num and num["color"] == "rgba(0, 0, 0, 0)", str(num and num["color"]))
        check("灰色的行：「采用」按钮是蓝色", sug and sug["bg"] == "rgb(37, 99, 235)", str(sug and sug["bg"]))
        page.screenshot(path=str(SHOTS / "7_find_grey.png"))

        # 8) gradio 的临时文件在工作文件夹的 __gradio_cache 里，网页照样能播放
        click(page, IDS[5], 3)  # 查找时表格只列出找到的句子：点灰色的那一行
        page.wait_for_timeout(2500)
        src = page.evaluate("""() => { const xs = Array.from(document.querySelectorAll('[src],[href]')).map(
            (e) => e.getAttribute('src') || e.getAttribute('href') || '').filter((u) => u.includes('file=') && u.includes('.wav'));
          return xs.length ? new URL(xs[xs.length - 1], location.href).href : ''; }""")
        cache = WORK / "ws" / "__gradio_cache"
        files = [str(x.relative_to(cache)) for x in cache.rglob("*") if x.is_file()] if cache.exists() else []
        ok = False
        if src:
            r = page.request.get(src)
            ok = r.status == 200 and len(r.body()) > 1000
        check("点一行能听：音频从工作文件夹的 __gradio_cache 发出来", ok and files and "__gradio_cache" in src, f"{src[-80:]} / {files[:3]}")
        check("网页脚本没有报错", not errors, str(errors[:3]))
        browser.close()
    print(f"\n{sum(ok for _, ok in RES)}/{len(RES)} 通过")


main()
