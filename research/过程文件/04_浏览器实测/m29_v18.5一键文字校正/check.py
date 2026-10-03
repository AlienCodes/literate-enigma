"""v18.5 真实浏览器（gradio 4.24、和整合包同版本的 Python 3.9 + pypinyin + jieba）里点一遍「一键全部文字校正」：
1. 按钮和标准库说明在「检查完了」那里；
2. 点一次：老师修缮前的 1004 句里需要改的 123 句全部改好（和逐句修缮一样）；标准库能证明的自动查错字建议
   （威驰 → which）一起采用，证明不了的（多一个「到」）不自动采用、还是红色有建议，结果说明里写着「没有把握」；
   改过的字「文字」列绿色、「可能有错」列蓝色，红灯（没保存）；
3. 「⬇️ 下载改好的文字（txt）」浏览器自动下载，里面是改好的文字；
4. 保存修改 → 确认训练素材 → 训练页不再提醒，训练用的是改好的字；
5. 上传一个 txt 母本，再点一次也能用。截图放在 shots/。"""
import csv
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

B = Path(__file__).resolve().parent
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:7951/"
SHOTS = B / "shots"
SHOTS.mkdir(exist_ok=True)
WORK = B / "work"
VOICE = WORK / "ws" / "我的声音"
REPO = Path("/home/user/literate-enigma")
CLEAN = {r["id"]: r["text"] for r in csv.DictReader(open(REPO / "research/文字校正/老师的母本/母本_修缮后.csv",
                                                           encoding="utf-8-sig"))}
ORIG = {r["id"]: r["text"] for r in csv.DictReader(open(REPO / "research/文字校正/老师的母本/母本_原文.csv",
                                                          encoding="utf-8-sig"))}
NEED = {i for i in ORIG if ORIG[i] != CLEAN[i]}
RESULTS = []
LIGHT_DIRTY_MARK = "vt-light-dirty"


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)


def text_of(page, sel):
    return page.evaluate(f"() => Array.from(document.querySelectorAll({json.dumps(sel)})).map(e => e.innerText).join('\\n')")


def wait_text(page, sel, needles, timeout=60):
    t0 = time.time()
    while time.time() - t0 < timeout:
        t = text_of(page, sel)
        if any(n in t for n in needles):
            return t
        time.sleep(0.5)
    return text_of(page, sel)


def draft():
    p = VOICE / "review_draft.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        ctx = browser.new_context(viewport={"width": 1366, "height": 900}, accept_downloads=True)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL)
        page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
        time.sleep(2)
        title = page.evaluate("() => document.querySelector('.vt-header h1').innerText")
        check("网页标题仍是 v18", "VoiceTwin v18" in title and "18.5" not in title, title)
        btn = page.locator("#vt-tr-btn")
        check("「📝 一键全部文字校正」按钮在", btn.is_visible() and "一键全部文字校正" in btn.inner_text())
        info = wait_text(page, ".vt-tr-info", ["标准库"], 20)
        check("按钮下面写着标准库（母本 1005 句 + 术语 + 对照表）", "你的母本 1005 句" in info and "对照表" in info, info[:80])
        btn.scroll_into_view_if_needed()
        page.screenshot(path=str(SHOTS / "01_buttons.png"))

        # ① 一键全部文字校正
        t0 = time.time()
        btn.click()
        md = wait_text(page, "body", ["一键全部文字校正完成", "没有完成"], 300)
        took = time.time() - t0
        check("一键全部文字校正走完", "一键全部文字校正完成" in md and "没有完成" not in md, f"{took:.0f} 秒")
        d = draft()
        exact = sum(1 for i in NEED if i in d and d[i]["text"] == CLEAN[i])
        check("需要改的 123 句全部改得和逐句修缮一样（存成没保存的修改）", exact == len(NEED) == 123, f"{exact}/{len(NEED)}")
        extra = [i for i in d if i not in NEED]
        vetted = [i for i in extra if "威驰" not in d[i]["text"] and d[i]["text"] == ORIG[i]]
        check("标准库能证明的自动查错字建议一起采用了（威驰 → which，只多了那一句）", len(extra) == 1 and vetted == extra,
              str([(i, d[i]["text"][:30]) for i in extra[:3]]))
        rec2 = {json.loads(ln)["id"]: json.loads(ln) for ln in
                (VOICE / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()}[list(ORIG)[2]]
        sys.path.insert(0, str(REPO))
        from voicetwin.data import review as _rv

        info2 = _rv.analyze(rec2, rec2["text"])
        check("证明不了的建议（多一个「到」）没有自动采用：还是红色、有建议，结果说明写着没有把握",
              list(ORIG)[2] not in d and info2["edits"] and not info2["sure"] and "没有把握" in md,
              str(info2["edits"]))
        summary = [ln for ln in md.splitlines() if "一共改了" in ln or "直接改好" in ln or "全部采用" in ln]
        check("结果说明写着改了多少处、下一步点保存修改", bool(summary) and "保存修改" in md and "确认训练素材" in md,
              " / ".join(summary[:3]))
        page.screenshot(path=str(SHOTS / "02_done.png"), full_page=False)

        # 表格：只看可能有错的 → 第一处改过的行：绿色 / 蓝色 / 红灯
        page.get_by_label("只看可能有错的").check()
        time.sleep(3)
        html = page.evaluate("() => document.querySelector('#vt-clips').innerHTML")
        check("「文字」列改过的字是绿色", 'class="vt-green"' in html)
        check("「可能有错」列改过的地方是蓝色", 'class="vt-blue"' in html)
        check("改过的行亮红灯（没保存）", LIGHT_DIRTY_MARK in html)
        page.screenshot(path=str(SHOTS / "03_table_marks.png"), full_page=False)

        # ② 下载改好的文字
        with page.expect_download(timeout=30000) as dl_info:
            page.locator("#vt-dl-txt-btn").click()
        dl = dl_info.value
        path = dl.path()
        body = Path(path).read_bytes().decode("utf-8-sig")
        lines = body.splitlines()
        check("浏览器自动下载了改好的文字（txt）", dl.suggested_filename.startswith("改好的文字_") and len(lines) > 900,
              f"{dl.suggested_filename}，{len(lines)} 行")
        check("下载的文字里是改好的（没有「借词」「关系带词」）", "借词" not in body and "关系带词" not in body and "介词" in body)
        page.screenshot(path=str(SHOTS / "04_download.png"))

        # ③ 保存修改 → 确认训练素材
        page.get_by_role("button", name="保存修改").click()
        t0 = time.time()
        while draft() and time.time() - t0 < 60:
            time.sleep(0.5)
        saved = {json.loads(ln)["id"]: json.loads(ln)["text"] for ln in
                 (VOICE / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()}
        check("保存修改以后校对表里是改好的文字", not draft() and all(saved[i] == CLEAN[i] for i in NEED))
        page.get_by_role("button", name="✅ 确认训练素材").click()
        t = wait_text(page, "body", ["训练素材已确认"], 60)
        check("确认训练素材成功", "训练素材已确认" in t)
        page.get_by_role("tab", name="② 训练模型").click()
        time.sleep(2)
        check("训练页不再提醒（可以训练了）", "还没有确认训练素材" not in text_of(page, "body"))
        sys.path.insert(0, str(REPO))
        from voicetwin.config import load_config
        from voicetwin.data.exporters import gptsovits_list_text
        from voicetwin import workflows as wf
        import os

        os.chdir(WORK)
        listing = gptsovits_list_text(wf.Project(load_config(), "我的声音"), "我的声音")
        check("训练用的文字是改好的（训练列表里没有「借词」「定语从剧」）",
              "借词" not in listing and "定语从剧" not in listing and "介词" in listing)

        # ④ 上传一个 txt 母本，再点一次
        page.get_by_role("tab", name="① 准备素材").click()
        time.sleep(1)
        txt = WORK / "新讲稿.txt"
        txt.write_text("今天我们来讲状语从句。状语从句就是在句子里做状语的从句。\n", encoding="utf-8")
        page.locator("#vt-tr-files input[type=file]").set_input_files(str(txt))
        time.sleep(2)
        btn.click()
        md = wait_text(page, "body", ["一键全部文字校正完成", "没有完成"], 300)
        info = wait_text(page, ".vt-tr-info", ["新讲稿.txt"], 20)
        check("上传 txt 母本以后再点一次也能用，按钮下面写着上传的文件", "新讲稿.txt" in info and "没有完成" not in md, info[-60:])
        check("改好、保存过的句子不会再被改（这次没有新的没保存的修改）", not draft(), str(list(draft())[:3]))
        page.screenshot(path=str(SHOTS / "05_uploaded.png"))
        check("网页上没有脚本错误", not errors, errors[:3])
        browser.close()
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    out = [f"{'PASS' if ok else 'FAIL'} {n}" + (f" — {d}" if d else "") for n, ok, d in RESULTS]
    out.append(f"合计：{passed}/{len(RESULTS)} 通过")
    (B / "check_结果.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(out[-1])


if __name__ == "__main__":
    main()
