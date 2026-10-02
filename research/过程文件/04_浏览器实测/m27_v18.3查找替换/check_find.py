"""v18.3 真实浏览器（gradio 4.24）里把「查找 / 替换」逐项点一遍，截图放在 shots/。"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

B = Path(__file__).resolve().parent
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:7931/"
SHOTS = B / "shots"
SHOTS.mkdir(exist_ok=True)
VOICE = B / "ws" / "老师的声音"
RESULTS = []


def manifest():
    return [json.loads(x) for x in (VOICE / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]


def draft():
    p = VOICE / "review_draft.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)


ROWS_JS = """() => Array.from(document.querySelectorAll('#vt-clips tbody.tbody tr')).map(tr => {
  const tds = Array.from(tr.children).filter(x => x.tagName === 'TD');
  return tds.map(td => ({text: td.innerText.trim(), html: td.innerHTML, bg: getComputedStyle(td).backgroundColor}));
}).filter(r => r.length >= 8 && r[1].text)"""


def rows(page):
    return page.evaluate(ROWS_JS)


def by_id(page):
    return {r[1]["text"]: r for r in rows(page)}


def status(page):
    return page.evaluate("() => { const e = document.querySelector('#vt-find-status'); return e ? e.innerText : ''; }")


def seq(page):
    return page.evaluate("() => { const e = document.querySelector('#vt-find-status'); return e ? (e.dataset.seq || '') : ''; }")


LAST = {"seq": None}


def mark(page):
    """点按钮之前记下查找结果的编号：等到它变了（程序回话了）才算数。"""
    LAST["seq"] = seq(page)


def wait_status(page, pred, timeout=15):
    t0 = time.time()
    s = ""
    while time.time() - t0 < timeout:
        s = status(page)
        if pred(s) and (LAST["seq"] is None or seq(page) != LAST["seq"]):
            LAST["seq"] = None
            time.sleep(0.4)  # 表格和状态是同一次更新，等表格画好
            return s
        time.sleep(0.2)
    print("  (timeout) status:", s)
    return s


def wait_rows(page, pred, timeout=15):
    t0 = time.time()
    r = []
    while time.time() - t0 < timeout:
        r = rows(page)
        if pred(r):
            return r
        time.sleep(0.2)
    print("  (timeout) rows:", [x[1]["text"] for x in r])
    return r


def box(page, elem_id):
    return page.locator(f"#{elem_id} textarea, #{elem_id} input").first


def btn(page, name):
    return page.get_by_role("button", name=name, exact=True)


def cur_in_view(page):
    return page.evaluate("""() => { const e = document.querySelector('#vt-clips tbody.tbody .vt-find-cur');
        if (!e) return null; const r = e.getBoundingClientRect();
        return r.top >= 0 && r.bottom <= window.innerHeight; }""")


def main():
    recs = manifest()
    ids = [r["id"] for r in recs]
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL)
        page.wait_for_function("() => document.querySelectorAll('#vt-clips tbody.tbody tr td').length > 20", timeout=60000)
        time.sleep(1.5)
        title = page.evaluate("() => document.querySelector('.vt-header h1').innerText")
        check("标题仍是 v18", "VoiceTwin v18" in title and "18.3" not in title, title.split("\n")[0])

        # ① 查找框在表格上面
        pos = page.evaluate("""() => { const q = document.querySelector('#vt-find-q'), t = document.querySelector('#vt-clips');
            return q && t ? [q.getBoundingClientRect().top + scrollY, t.getBoundingClientRect().top + scrollY] : null; }""")
        check("查找框在表格上面", pos and pos[0] < pos[1], str(pos))
        labels = page.locator(".vt-find-bar").inner_text()
        check("查找栏有：查找 / 替换成 / 上一处 / 下一处 / 替换这一处 / 全部替换 / 撤销 / 关闭",
              all(x in labels for x in ("查找", "替换成", "上一处", "下一处", "替换这一处", "全部替换", "撤销刚才的替换", "关闭查找")),
              labels.replace("\n", " / "))
        n_all = len(rows(page))  # 表格只画看得见的几行

        # ② 输入「艾子」按回车 = 查找
        box(page, "vt-find-q").fill("艾子")
        mark(page)
        box(page, "vt-find-q").press("Enter")
        s = wait_status(page, lambda s: "找到" in s)
        check("按回车就查找：找到 5 处（3 句）、现在是第 1 处", "找到 5 处" in s and "在 3 句里" in s and "现在是第 1 处" in s, s)
        rr = wait_rows(page, lambda r: len(r) == 3)
        check("表格只列出这 3 句，行号不变（1、6、30）", [r[0]["text"] for r in rr] == ["1", "6", "30"],
              str([r[0]["text"] for r in rr]))
        r1 = rr[0]
        check("找到的字黄色、现在这一处橙色（只有 1 个橙色）",
              r1[4]["html"].count("vt-find-cur") == 1 and r1[4]["html"].count('class="vt-find"') == 1
              and sum(r[4]["html"].count("vt-find-cur") for r in rr) == 1)
        bg = page.evaluate("() => { const e = document.querySelector('#vt-clips tbody.tbody .vt-find-cur'); return e ? getComputedStyle(e).backgroundColor : ''; }")
        bgy = page.evaluate("() => { const e = document.querySelector('#vt-clips tbody.tbody .vt-find'); return e ? getComputedStyle(e).backgroundColor : ''; }")
        check("颜色：橙色 #f97316、黄色 #fde047", bg == "rgb(249, 115, 22)" and bgy == "rgb(253, 224, 71)", f"{bg} / {bgy}")
        cnt = page.locator(".vt-md").filter(has_text="用来训练的句子").first.inner_text()
        check("上方提示：正在查找「艾子」", "正在查找「艾子」" in cnt, cnt.split("\n")[-1][:80])
        page.locator(".vt-find-bar").scroll_into_view_if_needed()
        page.screenshot(path=str(SHOTS / "01_find.png"))

        # ③ 下一处 / 上一处；到最后一句时表格滚过去
        mark(page)
        btn(page, "⬇ 下一处").click()
        s = wait_status(page, lambda s: "现在是第 2 处" in s)
        r1 = by_id(page)[ids[0]]
        check("⬇ 下一处：第 2 处（第 1 句里的第二个变橙色）", "现在是第 2 处" in s
              and r1[4]["html"].index("vt-find-cur") > r1[4]["html"].index('class="vt-find"'), s)
        mark(page)
        btn(page, "⬆ 上一处").click()
        mark(page)
        btn(page, "⬆ 上一处").click()
        s = wait_status(page, lambda s: "现在是第 5 处" in s)
        check("从第 2 处按两次 ⬆：转到最后一处（第 5 处，第 30 条）", "现在是第 5 处" in s and "第 30 条" in s, s)
        time.sleep(0.6)
        check("表格滚到橙色的那一处（看得见）", cur_in_view(page) is True)
        mark(page)
        btn(page, "⬇ 下一处").click()
        s = wait_status(page, lambda s: "现在是第 1 处" in s)
        check("最后一处再按 ⬇：回到第 1 处", "现在是第 1 处" in s, s)

        # ④ 替换这一处
        box(page, "vt-find-r").fill("as")
        mark(page)
        btn(page, "替换这一处").click()
        s = wait_status(page, lambda s: "换好了" in s)
        check("替换这一处：第 1 条换好了（没保存）", "第 1 条换好了" in s and "没保存" in s, s)
        r1 = by_id(page)[ids[0]]
        check("这一句换上的 as 是绿色、红灯、还有一处黄色", "vt-green" in r1[4]["html"] and "vt-light-dirty" in r1[7]["html"]
              and r1[4]["html"].count("vt-find") == 1, r1[4]["text"][:30])
        check("自动跳到下一处（现在是第 1 处 = 原来的第 2 处），一共还剩 4 处", "找到 4 处" in s and "现在是第 1 处" in s, s)
        check("硬盘上没改（要保存才生效）", "艾子" in manifest()[0]["text"])
        page.screenshot(path=str(SHOTS / "02_replace_one.png"))
        # ⑤ 撤销刚才的替换
        mark(page)
        btn(page, "↩️ 撤销刚才的替换").click()
        s = wait_status(page, lambda s: "撤销" in s)
        check("↩️ 撤销：改回去，又是 5 处", "1 句改回去了" in s and "找到 5 处" in s and ids[0] not in draft(), s)

        # ⑥ 全部替换：先问；点取消什么都不做
        dialogs = []
        page.once("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
        mark(page)
        btn(page, "全部替换").click()
        time.sleep(1.5)
        check("点「全部替换」先弹出确认，说清楚一共几处", dialogs and "确定把所有的「艾子」都换成「as」" in dialogs[0]
              and "一共 5 处" in dialogs[0], dialogs[0].replace("\n", " ") if dialogs else "没弹出")
        check("点取消：一个字都没换", not draft() and "找到 5 处" in status(page))
        page.once("dialog", lambda d: (dialogs.append(d.message), d.accept()))
        mark(page)
        btn(page, "全部替换").click()
        s = wait_status(page, lambda s: "已经把" in s)
        check("点确定：已经把 5 处换成 as（3 句，没保存）", "已经把 5 处「艾子」换成「as」（3 句" in s and "没保存" in s, s)
        rr = wait_rows(page, lambda r: len(r) == 3)
        check("换好的 3 句还列在表格里，换上的字绿色、都是红灯",
              len(rr) == 3 and all("vt-green" in r[4]["html"] and "vt-light-dirty" in r[7]["html"] for r in rr)
              and not any("艾子" in r[4]["text"] for r in rr), str([r[4]["text"][:12] for r in rr]))
        check("状态：现在没有「艾子」了", "现在没有「艾子」了" in s, s)
        page.locator(".vt-find-bar").scroll_into_view_if_needed()
        page.screenshot(path=str(SHOTS / "03_replace_all.png"))

        # ⑦ 查找时删除一句：变紫色，还在表格里
        page.evaluate("""(id) => { for (const tr of document.querySelectorAll('#vt-clips tbody.tbody tr')) {
            const tds = Array.from(tr.children).filter(x => x.tagName === 'TD');
            if (tds[1] && tds[1].innerText.trim() === id) { tds[7].querySelector('.vt-menu-btn').click(); return; } } }""", ids[5])
        page.wait_for_selector(".vt-menu", timeout=3000)
        page.locator(".vt-menu button", has_text="删除这一行").click()
        page.locator(".vt-menu button", has_text="确定删除").click()
        rr = wait_rows(page, lambda r: any(x[1]["text"] == ids[5] and x[4]["bg"] == "rgb(233, 213, 255)" for x in r))
        check("查找时删除第 6 条：整行紫色、没有消失", any(x[1]["text"] == ids[5] and x[4]["bg"] == "rgb(233, 213, 255)" for x in rr)
              and len(rr) == 3, str([x[0]["text"] for x in rr]))

        # ⑧ 保存修改：写进硬盘
        page.get_by_role("button", name="保存修改", exact=True).first.click()
        t0 = time.time()
        while time.time() - t0 < 30 and "艾子" in manifest()[0]["text"]:
            time.sleep(0.3)
        m = manifest()
        check("点「保存修改」：硬盘上换好了（删除的那句没换）", m[0]["text"].count("as") >= 2 and "艾子" not in m[0]["text"]
              and "艾子" in m[5]["text"] and "艾子" not in m[-1]["text"], m[-1]["text"])
        rr = wait_rows(page, lambda r: any("vt-light-saved" in x[7]["html"] for x in r))
        check("保存以后变绿灯", "vt-light-saved" in by_id(page)[ids[0]][7]["html"])

        # ⑨ 英文只找整个单词
        box(page, "vt-find-q").fill("as")
        mark(page)
        btn(page, "🔍 查找").click()
        s = wait_status(page, lambda s: "找到" in s and "「as」" in s)
        r7 = by_id(page).get(ids[6])
        check("找 as（勾着）：He has … 里只有单独的 as 黄色，has 不算", r7 is not None and r7[4]["html"].count("vt-find") == 1, s)
        page.locator(".vt-find-bar label", has_text="英文只找整个单词").click()
        mark(page)
        btn(page, "🔍 查找").click()
        time.sleep(0.3)
        s2 = wait_status(page, lambda x: x != s and "找到" in x)
        r7 = by_id(page).get(ids[6])
        check("去掉勾再找：has 里的 as 也找到了", r7 is not None and r7[4]["html"].count("vt-find") == 2, s2)
        page.locator(".vt-find-bar label", has_text="英文只找整个单词").click()
        box(page, "vt-find-q").fill("没有这个词")
        mark(page)
        btn(page, "🔍 查找").click()
        s = wait_status(page, lambda s: "没有找到" in s)
        check("找不到：说清楚，告诉怎么看全部", "没有找到「没有这个词」" in s and "关闭查找" in s, s)

        # ⑩ 关闭查找：全部句子都回来，查找框清空
        mark(page)
        btn(page, "✖ 关闭查找").click()
        rr = wait_rows(page, lambda r: len(r) >= n_all and ids[2] in [x[1]["text"] for x in r])
        time.sleep(0.5)
        q = box(page, "vt-find-q").input_value()
        shown = [x[1]["text"] for x in rows(page)]
        check("✖ 关闭查找：表格显示全部（没找到的第 2、3 条也回来了），查找框清空",
              ids[1] in shown and ids[2] in shown and len(shown) == n_all and q == "" and status(page) == "",
              f"{len(rows(page))} 行，查找框={q!r}")
        cnt = page.locator(".vt-md").filter(has_text="用来训练的句子").first.inner_text()
        check("上方不再显示「正在查找」", "正在查找" not in cnt)

        # ⑪ 查找时刷新网页：查找框是空的，表格就显示全部（不会只剩几行还不知道为什么）
        box(page, "vt-find-q").fill("as")
        mark(page)
        btn(page, "🔍 查找").click()
        wait_status(page, lambda s: "找到" in s)
        page.reload()
        page.wait_for_function("() => document.querySelectorAll('#vt-clips tbody.tbody tr td').length > 20", timeout=60000)
        time.sleep(1.5)
        shown = [x[1]["text"] for x in rows(page)]
        check("查找时刷新网页：查找框空的、表格显示全部", ids[2] in shown and box(page, "vt-find-q").input_value() == ""
              and status(page) == "", str(len(shown)))

        # ⑫ 手机宽度
        page.set_viewport_size({"width": 375, "height": 800})
        time.sleep(1.0)
        page.locator(".vt-find-bar").scroll_into_view_if_needed()
        page.screenshot(path=str(SHOTS / "04_mobile.png"))
        check("网页没有脚本错误", not errors, "; ".join(errors[:3]))
        browser.close()
    bad = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(bad)} / {len(RESULTS)} 项通过")
    (B / "check_result.json").write_text(json.dumps(RESULTS, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit(1 if bad else 0)


main()
