"""真实浏览器（gradio 4.24）里把校对表的新功能逐项点一遍，截图放在 shots/。"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

B = Path(__file__).resolve().parent
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:7901/"
SHOTS = B / "shots"
SHOTS.mkdir(exist_ok=True)
MANIFEST = B / "ws" / "老师的声音" / "manifest.jsonl"
RESULTS = []


def manifest():
    return [json.loads(x) for x in MANIFEST.read_text(encoding="utf-8").splitlines() if x.strip()]


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)


ROW_JS = """(id) => {
  const rows = document.querySelectorAll('#vt-clips tbody.tbody tr');
  for (const tr of rows) {
    const tds = Array.from(tr.children).filter(x => x.tagName === 'TD');
    if (tds[1] && tds[1].innerText.trim() === id) {
      return tds.map(td => ({text: td.innerText.trim(), html: td.innerHTML,
                             bg: getComputedStyle(td).backgroundColor}));
    }
  }
  return null;
}"""


def row(page, cid):
    return page.evaluate(ROW_JS, cid)


class Cell:
    """按 id 找到真正表格里的格子（每次都重新找：表格重画以后格子是新的）。"""

    def __init__(self, page, cid, col):
        self.page, self.cid, self.col = page, cid, col

    def handle(self, sub=None):
        # 先滚到这一行，等表格重画，再按 id 重新找（gradio 的表格滚动时会拿同一个格子显示别的行）
        self.page.evaluate("""([id, col]) => {
          for (const tr of document.querySelectorAll('#vt-clips tbody.tbody tr')) {
            const tds = Array.from(tr.children).filter(x => x.tagName === 'TD');
            if (tds[1] && tds[1].innerText.trim() === id) { tds[col].scrollIntoView({block: 'nearest'}); return; }
          } }""", [self.cid, self.col])
        time.sleep(0.25)
        h = self.page.evaluate_handle("""([id, col]) => {
          for (const tr of document.querySelectorAll('#vt-clips tbody.tbody tr')) {
            const tds = Array.from(tr.children).filter(x => x.tagName === 'TD');
            if (tds[1] && tds[1].innerText.trim() === id) return tds[col];
          }
          return null; }""", [self.cid, self.col]).as_element()
        assert h is not None, f"找不到 {self.cid} 第 {self.col} 列"
        if sub:
            h = h.query_selector(sub)
            assert h is not None, f"{self.cid} 第 {self.col} 列里没有 {sub}"
        return h

    def dblclick(self):
        self.handle().dblclick()

    def click(self):
        self.handle().click()

    def locator(self, sub):
        outer = self

        class _Sub:
            def click(self_inner):
                outer.handle(sub).click()

        return _Sub()


def cell(page, cid, col):
    return Cell(page, cid, col)


def wait_row(page, cid, pred, what, timeout=15):
    t0 = time.time()
    r = None
    while time.time() - t0 < timeout:
        r = row(page, cid)
        if r and pred(r):
            return r
        time.sleep(0.2)
    print("  (timeout) last row:", json.dumps([c["text"] for c in r] if r else None, ensure_ascii=False))
    return None


def main():
    recs = manifest()
    ids = [r["id"] for r in recs]
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL)
        page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=60000)
        page.wait_for_function("() => document.querySelectorAll('#vt-clips tbody.tbody tr td').length > 20", timeout=60000)
        time.sleep(1.5)
        # 顶部模型型号：圆角长方形
        radius = page.evaluate("() => { const e = document.querySelector('.vt-model'); return e ? getComputedStyle(e).borderRadius : ''; }")
        title = page.evaluate("() => document.querySelector('.vt-header h1').innerText")
        check("标题仍是 v18、模型型号是圆角长方形", "VoiceTwin v18" in title and radius == "8px", f"{title!r} radius={radius}")
        page.locator(".vt-header").first.screenshot(path=str(SHOTS / "01_header.png"))
        page.locator("#vt-clips").scroll_into_view_if_needed()
        page.screenshot(path=str(SHOTS / "02_table.png"), full_page=False)
        heads = page.evaluate("() => Array.from(document.querySelectorAll('#vt-clips thead.thead th')).map(t => t.innerText.trim())")
        check("表头：没有丢弃原因 / 保留 / 状态，最右边是选项", heads[-1] == "选项" and "修改建议" in heads
              and not any(h.startswith(("丢弃原因", "保留", "状态")) for h in heads), json.dumps(heads, ensure_ascii=False))

        r5 = row(page, ids[4])
        check("英文的 let's 原样显示（不是 &#x27;）", r5 and "let's" in r5[4]["text"] and "&#" not in r5[4]["text"],
              r5 and r5[4]["text"])
        a = ids[0]
        r = row(page, a)
        check("第 1 条：红字 2 处、修改建议是蓝色小按钮", r and r[5]["html"].count("vt-red") == 2 and "艾子 → as" in r[6]["text"]
              and "vt-sug-blue" in r[6]["html"], r and r[6]["text"])
        empty_ok = page.evaluate("""() => Array.from(document.querySelectorAll('#vt-clips tbody.tbody tr')).every(tr => {
            const tds = Array.from(tr.children).filter(x => x.tagName === 'TD');
            return tds[5].innerText.trim() !== '' || !tds[6].querySelector('.vt-sug-btn'); })""")
        check("「可能有错」空着的行没有建议按钮", empty_ok)

        # ① 双击文字：大编辑框，整句话完整显示（自动换行，不超出）
        cell(page, a, 4).dblclick()
        page.wait_for_selector(".vt-editor textarea", timeout=5000)
        info = page.evaluate("""() => { const ta = document.querySelector('.vt-editor textarea');
            const r = ta.getBoundingClientRect(); return {value: ta.value, sh: ta.scrollHeight, ch: ta.clientHeight,
            sw: ta.scrollWidth, cw: ta.clientWidth, w: r.width, h: r.height,
            lh: parseFloat(getComputedStyle(ta).lineHeight)}; }""")
        full = recs[0]["text"]
        check("双击「文字」打开编辑框，内容是整句话", info["value"] == full, info["value"][:20])
        check("编辑框自动换行、整句都看得见（没有被挡住）", info["sh"] <= info["ch"] + 2 and info["sw"] <= info["cw"] + 2
              and info["h"] > info["lh"] * 1.5, json.dumps(info, ensure_ascii=False))
        page.screenshot(path=str(SHOTS / "03_editor.png"))
        # 正在用输入法选字时按回车：不算改好
        page.evaluate("""() => { const ta = document.querySelector('.vt-editor textarea');
            ta.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', keyCode: 229, isComposing: true, bubbles: true})); }""")
        time.sleep(0.4)
        check("输入法选字时的回车不会关掉编辑框", page.locator(".vt-editor").count() == 1)
        s2 = full.rindex("艾子")
        fixed = full[:s2] + "as" + full[s2 + 2:]
        page.locator(".vt-editor textarea").fill(fixed)
        page.keyboard.press("Enter")
        r = wait_row(page, a, lambda r: "vt-light-dirty" in r[7]["html"], "dirty")
        check("改好按回车：这一行 🔴 没保存", r is not None)
        check("改过的字变蓝、没改的还是红", r and r[5]["html"].count("vt-blue") == 1 and r[5]["html"].count("vt-red") == 1,
              r and r[5]["text"])
        check("「文字」一列里改过的字是绿色", r and r[4]["html"].count("vt-green") == 1 and "as" in r[4]["text"])
        check("没改过的行「文字」没有绿色", (row(page, ids[2]) or [{}] * 8)[4].get("html", "x").count("vt-green") == 0)
        check("还剩一处建议：艾子 → as", r and "艾子 → as" in r[6]["text"], r and r[6]["text"])
        check("硬盘上还没改（没保存）", manifest()[0]["text"] == full)
        page.screenshot(path=str(SHOTS / "04_after_edit.png"))

        # ② 点蓝色小按钮采用建议 → 变红；再点 → 撤销、变回蓝色；再点 → 又采用
        cell(page, a, 6).locator(".vt-sug-blue").click()
        r = wait_row(page, a, lambda r: "vt-sug-red" in r[6]["html"], "adopted")
        check("点蓝色按钮：按建议改好、按钮变红，两处都变蓝、不再标红", r and r[4]["text"] == full.replace("艾子", "as")
              and r[5]["html"].count("vt-blue") == 2 and "vt-red" not in r[5]["html"], r and r[4]["text"])
        page.screenshot(path=str(SHOTS / "05_adopted.png"))
        time.sleep(0.8)  # 像人一样：看一眼再点
        cell(page, a, 6).locator(".vt-sug-red").click()
        r = wait_row(page, a, lambda r: "vt-sug-blue" in r[6]["html"], "unadopted")
        check("再点红色按钮：撤销建议，变回蓝色按钮", r and r[4]["text"] == full and r[5]["html"].count("vt-red") == 2)
        # 双击蓝色按钮：只采用一次（第二下点在 ⏳ 上，不算）
        time.sleep(0.8)
        cell(page, a, 6).handle(".vt-sug-blue").dblclick()
        r = wait_row(page, a, lambda r: "vt-sug-red" in r[6]["html"], "dbl")
        time.sleep(1.0)
        r = row(page, a)
        check("双击蓝色按钮：只采用一次（按钮是红的）", r and "vt-sug-red" in r[6]["html"])
        time.sleep(0.8)
        cell(page, a, 6).locator(".vt-sug-red").click()
        wait_row(page, a, lambda r: "vt-sug-blue" in r[6]["html"], "unadopted2")
        time.sleep(0.8)
        cell(page, a, 6).locator(".vt-sug-blue").click()
        r = wait_row(page, a, lambda r: "vt-sug-red" in r[6]["html"], "adopted again")
        check("再点蓝色按钮：又采用", r and r[4]["text"] == full.replace("艾子", "as"))

        # ③ 选项 → 只保存这一行 → 绿灯
        cell(page, a, 7).locator(".vt-menu-btn").click()
        page.wait_for_selector(".vt-menu", timeout=3000)
        mt = page.locator(".vt-menu").inner_text()
        check("选项菜单里有「保存这一行」和「删除这一行」", "保存这一行" in mt and "删除这一行" in mt, mt.replace("\n", " / "))
        page.screenshot(path=str(SHOTS / "06_menu.png"))
        page.locator(".vt-menu button", has_text="保存这一行").click()
        r = wait_row(page, a, lambda r: "vt-light-saved" in r[7]["html"], "saved", timeout=30)
        check("只保存这一行：变成 🟢 已保存", r is not None)
        m = manifest()
        check("硬盘上第 1 条保存了，别的行没动", m[0]["text"] == full.replace("艾子", "as")
              and m[1]["text"] == recs[1]["text"])

        # ④ 第 2 条采用建议，再点下面的「保存修改」（全部保存）→ 绿灯
        b = ids[1]
        cell(page, b, 6).locator(".vt-sug-blue").click()
        r = wait_row(page, b, lambda r: "vt-light-dirty" in r[7]["html"], "dirty2")
        check("第 2 条采用建议（英文按整词：smoker has → smokers have）",
              r and "smokers have" in r[4]["text"], r and r[4]["text"][:60])
        page.get_by_role("button", name="保存修改").click()
        r = wait_row(page, b, lambda r: "vt-light-saved" in r[7]["html"], "saved2", timeout=30)
        check("点「保存修改」：变成 🟢 已保存", r is not None and "smokers have" in manifest()[1]["text"])
        check("保存以后按钮还是红的（建议一直生效）", r and "vt-sug-red" in r[6]["html"])

        # ④b 双击屏幕最下面那一行：页面不跳，编辑框打开的就是这一行（以前第一下让页面跳了，第二下点到别的行）
        c3 = ids[2]
        h = cell(page, c3, 4).handle()
        bb = h.bounding_box()
        page.evaluate("(dy) => window.scrollBy(0, dy)", bb["y"] + bb["height"] - page.viewport_size["height"] + 2)
        time.sleep(0.5)
        bb = cell(page, c3, 4).handle().bounding_box()
        page.mouse.dblclick(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        page.wait_for_selector(".vt-editor textarea")
        check("双击屏幕最下面的一行：编辑框是这一行（页面没有跳）",
              page.locator(".vt-editor textarea").input_value() == recs[2]["text"],
              page.locator(".vt-editor textarea").input_value()[:20])
        page.keyboard.press("Escape")
        time.sleep(0.5)

        # ⑤ Esc 不改；改了点别处 = 改好；撤销这一行的修改
        c = ids[2]
        cell(page, c, 4).dblclick()
        page.wait_for_selector(".vt-editor textarea")
        page.locator(".vt-editor textarea").fill("随便改改")
        page.keyboard.press("Escape")
        time.sleep(1.0)
        r = row(page, c)
        check("按 Esc：不改", r and r[4]["text"] == recs[2]["text"] and "vt-light-dirty" not in r[7]["html"])
        cell(page, c, 4).dblclick()
        page.wait_for_selector(".vt-editor textarea")
        page.locator(".vt-editor textarea").fill(recs[2]["text"] + "（补一句）")
        page.mouse.click(5, 5)
        r = wait_row(page, c, lambda r: "vt-light-dirty" in r[7]["html"], "blur")
        check("改完点别的地方：也算改好（🔴 没保存）", r and r[4]["text"].endswith("（补一句）"))
        cell(page, c, 7).locator(".vt-menu-btn").click()
        page.locator(".vt-menu button", has_text="撤销这一行的修改").click()
        r = wait_row(page, c, lambda r: "vt-light-dirty" not in r[7]["html"] and r[4]["text"] == recs[2]["text"], "revert")
        check("撤销这一行的修改：回到原样", r is not None)

        # ⑥a 程序判断不能用的行：灰色「⚪ 不用」，不写原因；选项里有「这一条也要用」
        u = ids[3]
        r = row(page, u)
        check("程序判断不能用的行：灰色「不用」、不写原因", r and "vt-flag-unused" in r[7]["html"] and "语速" not in r[7]["text"]
              and r[4]["bg"] == "rgb(229, 231, 235)", r and r[7]["html"])
        cell(page, u, 7).locator(".vt-menu-btn").click()
        check("灰色「不用」的行：选项里有「这一条也要用」", "这一条也要用" in page.locator(".vt-menu").inner_text())
        page.locator(".vt-menu button", has_text="这一条也要用").click()
        r = wait_row(page, u, lambda r: "vt-flag-unused" not in r[7]["html"] and "vt-light-dirty" in r[7]["html"], "use")
        check("点「这一条也要用」：不再灰色，🔴 没保存", r is not None and r[4]["bg"] != "rgb(229, 231, 235)")
        # ⑥ 删除：先确认；取消不删；确定后整行变灰；选项里变成「撤销删除」
        d = ids[4]
        cell(page, d, 7).locator(".vt-menu-btn").click()
        page.locator(".vt-menu button", has_text="删除这一行").click()
        page.wait_for_selector(".vt-menu-danger")
        check("删除前会再问一次", "确定要删除" in page.locator(".vt-menu").inner_text())
        page.screenshot(path=str(SHOTS / "07_confirm.png"))
        page.locator(".vt-menu button", has_text="取消").click()
        page.locator(".vt-menu button", has_text="关闭").click()
        time.sleep(0.6)
        check("点取消：没有删除", not manifest()[4].get("deleted"))
        cell(page, d, 7).locator(".vt-menu-btn").click()
        page.locator(".vt-menu button", has_text="删除这一行").click()
        page.locator(".vt-menu button", has_text="确定删除").click()
        r = wait_row(page, d, lambda r: "vt-flag-del" in r[7]["html"], "deleted", timeout=30)
        check("删除后这一行还在、变灰", r is not None and r[4]["bg"] == "rgb(229, 231, 235)", r and r[4]["bg"])
        check("硬盘上标成删除（不用来训练）", manifest()[4].get("deleted") is True and manifest()[4]["keep"] is False)
        page.screenshot(path=str(SHOTS / "08_deleted_gray.png"))
        cell(page, d, 4).dblclick()
        time.sleep(1.0)
        check("灰色的行双击不能改（提示先撤销删除）", page.locator(".vt-editor").count() == 0)
        cell(page, d, 7).locator(".vt-menu-btn").click()
        menu_text = page.locator(".vt-menu").inner_text()
        check("灰色行的选项里是「撤销删除」", "撤销删除" in menu_text and "删除这一行" not in menu_text, menu_text)
        page.locator(".vt-menu button", has_text="撤销删除").click()
        r = wait_row(page, d, lambda r: "vt-flag-del" not in r[7]["html"], "restored", timeout=30)
        check("撤销删除：这一行回来了（不再灰色）", r is not None and not manifest()[4].get("deleted")
              and r[4]["bg"] != "rgb(229, 231, 235)")

        # ⑦ 双击「语言」切换；没有「保留」「丢弃原因」两列
        heads2 = page.evaluate("() => Array.from(document.querySelectorAll('#vt-clips thead.thead th')).map(t => t.innerText.trim()).join('|')")
        check("没有「保留」「丢弃原因」两列", "保留" not in heads2 and "丢弃原因" not in heads2, heads2)
        lang_before = r[2]["text"]
        cell(page, d, 2).dblclick()
        r = wait_row(page, d, lambda r: r[2]["text"] != lang_before, "lang")
        check("双击「语言」：中文/英文切换，🔴 没保存", r and "vt-light-dirty" in r[7]["html"])
        cell(page, d, 2).dblclick()
        r = wait_row(page, d, lambda r: r[2]["text"] == lang_before, "lang back")
        check("再双击一次：改回来，不再是红灯", r and "vt-light-dirty" not in r[7]["html"])

        # ⑧ 表格滚到下面改字：表格不会跳回最上面
        scroller = """() => { const els = Array.from(document.querySelectorAll('#vt-clips *'));
            const s = els.find(e => e.scrollHeight > e.clientHeight + 20 && /(auto|scroll)/.test(getComputedStyle(e).overflowY));
            return s; }"""
        page.evaluate(f"() => {{ const s = ({scroller})(); if (s) s.scrollTop = s.scrollHeight; }}")
        time.sleep(0.8)
        last = ids[-2]
        top_before = page.evaluate(f"() => {{ const s = ({scroller})(); return s ? s.scrollTop : -1; }}")
        cell(page, last, 4).dblclick()
        page.wait_for_selector(".vt-editor textarea")
        page.locator(".vt-editor textarea").fill(manifest()[-2]["text"] + "改")
        page.keyboard.press("Enter")
        r = wait_row(page, last, lambda r: "vt-light-dirty" in r[7]["html"], "bottom edit")
        time.sleep(0.5)
        top_after = page.evaluate(f"() => {{ const s = ({scroller})(); return s ? s.scrollTop : -1; }}")
        check("在表格下面改字：表格没有跳回最上面", r is not None and top_after > 0 and abs(top_after - top_before) < 120,
              f"scrollTop {top_before} → {top_after}")
        page.screenshot(path=str(SHOTS / "09_bottom_edit.png"))

        # ⑧b 选项按钮在屏幕最下面：菜单往上开、整个看得见；滚动页面时菜单跟着走、不会自己关掉
        h = cell(page, ids[-3], 7).handle(".vt-menu-btn")
        bb = h.bounding_box()
        page.evaluate("(dy) => window.scrollBy(0, dy)", bb["y"] - (page.viewport_size["height"] - 40))
        time.sleep(0.6)
        h = cell(page, ids[-3], 7).handle(".vt-menu-btn")
        page.evaluate("(el) => el.click()", h)
        page.wait_for_selector(".vt-menu", timeout=3000)
        mb = page.evaluate("() => { const r = document.querySelector('.vt-menu').getBoundingClientRect(); return {top: r.top, bottom: r.bottom, vh: innerHeight}; }")
        check("选项在屏幕最下面：菜单整个看得见（往上开）", mb["top"] >= 0 and mb["bottom"] <= mb["vh"], str(mb))
        page.evaluate("() => window.scrollBy(0, -120)")
        time.sleep(0.6)
        check("滚动页面：菜单还在", page.locator(".vt-menu").count() == 1)
        page.keyboard.press("Escape")
        time.sleep(0.3)
        check("按 Esc：菜单关掉", page.locator(".vt-menu").count() == 0)

        # ⑨ 刷新网页：没保存的修改还在
        page.reload()
        page.wait_for_function("() => document.querySelectorAll('#vt-clips tbody.tbody tr td').length > 20", timeout=60000)
        time.sleep(1.5)
        page.evaluate(f"() => {{ const s = ({scroller})(); if (s) s.scrollTop = s.scrollHeight; }}")
        time.sleep(0.8)
        r = wait_row(page, last, lambda r: "vt-light-dirty" in r[7]["html"], "after reload")
        check("刷新网页以后，没保存的修改还在（红灯）", r is not None and r[4]["text"].endswith("改"))
        count_md = page.locator(".vt-md").filter(has_text="一共").first.inner_text()
        check("上方提示还有几条没保存", "没有保存" in count_md, count_md[-60:])

        # ⑩ 手机宽度
        page.set_viewport_size({"width": 375, "height": 800})
        time.sleep(1.0)
        page.locator("#vt-clips").scroll_into_view_if_needed()
        page.screenshot(path=str(SHOTS / "10_mobile.png"))
        page.set_viewport_size({"width": 1280, "height": 900})
        check("网页没有脚本错误", not errors, "; ".join(errors[:3]))
        browser.close()
    bad = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(bad)} / {len(RESULTS)} 项通过")
    (B / "check_result.json").write_text(json.dumps(RESULTS, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit(1 if bad else 0)


main()
