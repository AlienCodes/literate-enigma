"""母本优先：真实浏览器（gradio 4.24、和整合包同版本的 Python 3.9 + pypinyin + jieba）里看一遍。

两步（工作文件夹随便给一个临时的，跑完自己删掉）：
1. 准备：PYTHONPATH=. /tmp/gsv39/bin/python research/文字校正/母本优先/浏览器实测.py setup <工作文件夹>
   用老师修缮以前的句子建一个声音：同一批素材按原来的顺序 314 句（其中 40 句和母本不一样），片段 id 全换掉（像重新准备过素材）；
   其中一句老师自己改过（和母本不一样）；后面接一段「新讲的课」（另一个视频：母本里没有的话中间夹着和母本只差一个词的句子，
   第二轮检查加的）；然后跑一次「自动查错字」（第二个识别引擎是假的，把一句对的「定语」听成「定于」）。
2. 打开网页（同一个 Python 跑 voicetwin.webui.launcher，工作文件夹里有 config.yaml），再：
   PYTHONPATH=. /tmp/gsv39/bin/python research/文字校正/母本优先/浏览器实测.py check <网址> <工作文件夹>
检查：说明里写着「母本最优先」；还没点一键校正，「修改建议」那一列就有「按母本：」；和母本矛盾的「定语 → 定于」没有出现；
点一行看得到「按母本改成」「母本里的原句」；老师自己改过的那一行看得到「和母本不一样、程序没有动的地方」；
点「📝 一键全部文字校正」以后结果里写着在母本里找到了几句，40 句全部改得和母本一模一样、对的句子一个字都没动；网页没有脚本错误。
第二轮加的：新讲的课里和母本只差一个词的句子，「修改建议」写「按母本（没把握，请听录音）」，一键校正以后一个字都没动。
"""

import csv
import json
import sys
import time
import unittest.mock as um
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
D = ROOT / "research" / "文字校正" / "老师的母本"
VOICE = "我的声音"


#: 新讲的课：母本里没有的话，中间夹着和母本只差一个词的句子（第二轮检查）
NEW_LECTURE = ["今天我们来学习一下名词性从句里面的主语从句。", "在状语从句中， as主要被翻译为正如。",
               "主语从句就是在整个复合句当中充当主语的那个从句。",
               "而which在定语从句中，如果去做宾语这个句子成分的话，那么它可以被省略。",
               "好，下面我们做几道选择题来巩固一下刚才讲的内容。",
               "首先，as这个关系代词，它最经常出现在限定性定语从句中，经常会作为限定定语从句的引导词而出现。"]
NEAR = (1, 3, 5)  # 上面和母本只差一个词的几句


def rows():
    """同一批素材按原来的顺序，一直到有 40 句和母本不一样（第二轮：读音不像听错的地方要靠前后的句子证明是同一批录音）。"""
    orig = list(csv.DictReader(open(D / "母本_原文.csv", encoding="utf-8-sig")))
    clean = {r["id"]: r["text"] for r in csv.DictReader(open(D / "母本_修缮后.csv", encoding="utf-8-sig"))}
    ok = [(r["text"], clean[r["id"]]) for r in orig if r["keep"] == "1" and r["drop_reason"] != "老师删除"]
    out, n = [], 0
    for t, c in ok:
        out.append((t, c))
        n += int(t != c)
        if n >= 40:
            break
    return out


def setup(work: Path):
    import numpy as np
    import soundfile as sf

    work.mkdir(parents=True, exist_ok=True)
    (work / "config.yaml").write_text("workspace: ./ws\nbackend: dummy\nspeaker_encoder: mfcc\nprepare:\n  asr:\n"
                                      "    engine: none\nsimilarity:\n  model_dir: ./sv\n", encoding="utf-8")
    import os

    os.chdir(work)
    from voicetwin import workflows as wf
    from voicetwin.config import load_config
    from voicetwin.data import proofcheck as pc
    from voicetwin.data import review

    cfg = load_config()
    project = wf.Project(cfg, VOICE).ensure()
    batch = rows()
    sr = 16000
    tt = np.arange(int(3.0 * sr)) / sr
    wav = (0.1 * np.sin(2 * np.pi * 150 * tt) * (0.5 - 0.5 * np.cos(2 * np.pi * 3 * tt))).astype(np.float32)
    recs, truth = [], {}
    items = [(t, c, "第1课") for t, c in batch] + [(t, t, "新课") for t in NEW_LECTURE]
    for k, (t, c, src) in enumerate(items):
        rid = f"0300_beefee_{k:04d}"
        sf.write(str(project.clips_dir / f"{rid}.wav"), wav, sr)
        recs.append({"id": rid, "path": f"clips/{rid}.wav", "text": t, "lang": "zh", "duration": 3.0, "voiced": 2.5,
                     "keep": True, "split": "train", "asr_done": True, "source": src})
        truth[rid] = c
    project.save_manifest(recs)
    project.export_csv(recs)
    diff_ids = [recs[k]["id"] for k, (t, c) in enumerate(batch) if t != c]
    near_ids = [recs[len(batch) + k]["id"] for k in NEAR]
    # 老师自己改过的一句：把母本里的「介词」打成了「介绍词」（这一句另外还有别的识别错）
    k = next(i for i, (t, c) in enumerate(batch) if t != c and "借词" in t and t.count("借词") == 1)
    rid_typed = recs[k]["id"]
    review.set_draft(project, rid_typed, text=recs[k]["text"].replace("借词", "介绍词"))
    # 第二个识别引擎把一句对的「定语」听成「定于」（和母本矛盾）
    kw = next(i for i, (t, c) in enumerate(batch) if t == c and "定语" in t)
    rid_wrong = recs[kw]["id"]
    heard = {rid_wrong: recs[kw]["text"].replace("定语", "定于", 1)}

    class FakeRunner(pc._EngineRunner):
        def recognize(self, rec, lang):
            return heard.get(rec["id"], rec["text"]), None, pc.ENGINE_FUNASR

    with um.patch.object(pc, "_EngineRunner", FakeRunner):
        pc.find_suspects(project, cfg)
    (work / "truth.json").write_text(json.dumps({"truth": truth, "typed": rid_typed, "wrong": rid_wrong,
                                                 "diff": diff_ids, "near": near_ids},
                                                ensure_ascii=False), encoding="utf-8")
    print("ok", len(recs), rid_typed, rid_wrong)


RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)


def run_check(url: str, work: Path):
    from playwright.sync_api import sync_playwright

    info = json.loads((work / "truth.json").read_text(encoding="utf-8"))
    voice_dir = work / "ws" / VOICE

    def text_of(page, sel):
        return page.evaluate(f"() => Array.from(document.querySelectorAll({json.dumps(sel)}))"
                             ".map(e => e.innerText).join('\\n')")

    # 表格是虚拟滚动的（只画看得见的几行）：一点一点往下滚，边滚边找 / 边收集
    scroller = """(dy) => { const t = document.querySelector('#vt-clips tbody.tbody');
      let el = t; while (el && !(el.scrollHeight > el.clientHeight + 5 && getComputedStyle(el).overflowY !== 'visible')) {
        el = el.parentElement; }
      if (!el) return -1; if (dy === 0) { el.scrollTop = 0; } else { el.scrollTop += dy; }
      return el.scrollTop + el.clientHeight >= el.scrollHeight - 2 ? 1 : 0; }"""

    def rows_now(page):
        return page.evaluate("""() => Array.from(document.querySelectorAll('#vt-clips tbody.tbody tr'))
          .map(tr => Array.from(tr.querySelectorAll('td')).map(td => td.innerText))""")

    def scan(page):
        """整张表每一行（按 id）：[各格文字]。"""
        seen = {}
        page.evaluate(scroller, 0)
        time.sleep(0.6)
        for _ in range(200):
            for cells in rows_now(page):
                if len(cells) > 1:
                    seen[cells[1].strip()] = cells
            if page.evaluate(scroller, 250) != 0:
                time.sleep(0.6)
                for cells in rows_now(page):
                    if len(cells) > 1:
                        seen[cells[1].strip()] = cells
                break
            time.sleep(0.4)
        return seen

    def click_row(page, rid):
        page.evaluate(scroller, 0)
        time.sleep(0.6)
        for _ in range(200):
            loc = page.locator("#vt-clips tbody.tbody tr", has_text=rid)
            if loc.count():
                loc.first.locator("td").nth(1).click()
                time.sleep(2.5)
                return text_of(page, ".vt-diff")
            if page.evaluate(scroller, 250) != 0 and not page.locator("#vt-clips tbody.tbody tr", has_text=rid).count():
                return ""
            time.sleep(0.4)
        return ""

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        ctx = browser.new_context(viewport={"width": 1366, "height": 900}, locale="en-US")
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(url)
        page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
        time.sleep(2)
        body = text_of(page, "body")
        check("说明里写着「母本最优先」", "母本最优先" in body)
        rows_seen = scan(page)
        sug = {rid: cells[6] for rid, cells in rows_seen.items() if len(cells) > 6}
        n_m = sum(1 for rid in info["diff"] if "按母本：" in sug.get(rid, ""))
        check("还没点一键校正，和母本不一样的 40 句「修改建议」那一列都有「按母本：」的建议（老师改过的那句除外）",
              n_m >= len(info["diff"]) - 1, f"{n_m} / {len(info['diff'])} 句；整张表看到 {len(rows_seen)} 行")
        check("和母本矛盾的「定语 → 定于」没有出现", not any("→ 定于" in x for x in sug.values()))
        n_u = sum(1 for rid in info["near"] if "按母本（没把握，请听录音）" in sug.get(rid, ""))
        check("新讲的课里和母本只差一个词的句子：「修改建议」写「按母本（没把握，请听录音）」", n_u == len(info["near"]),
              f"{n_u} / {len(info['near'])} 句")
        panel = click_row(page, info["diff"][0])
        check("点一行看得到「按母本改成」和「母本里的原句」", "按母本改成" in panel and "母本里的原句" in panel, panel[:80])
        panel = click_row(page, info["typed"])
        check("老师自己改过的那一行：看得到「和母本不一样、程序没有动的地方」",
              "和母本不一样、程序没有动的地方" in panel and "介绍词" in panel, panel[-120:])
        page.screenshot(path=str(work / "母本优先_自动查错字以后.png"), full_page=False)
        page.get_by_role("button", name="📝 一键全部文字校正").click()
        t0 = time.time()
        while time.time() - t0 < 120 and "母本最优先：在你的母本里找到了" not in text_of(page, "body"):
            time.sleep(1)
        check("一键校正的结果说明在母本里找到了几句", "母本最优先：在你的母本里找到了" in text_of(page, "body"))
        time.sleep(2)
        draft = json.loads((voice_dir / "review_draft.json").read_text(encoding="utf-8"))
        manifest = {}
        for ln in (voice_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
            if ln.strip():
                r = json.loads(ln)
                manifest[r["id"]] = r
        from voicetwin.utils.textutil import clean_transcript

        wrong = [rid for rid in info["diff"] if rid != info["typed"]
                 and clean_transcript(draft.get(rid, {}).get("text", manifest[rid]["text"])) != clean_transcript(info["truth"][rid])]
        check("和母本不一样的句子全部改得和母本一模一样（老师自己改过的那句除外）", not wrong, f"不一样的 {len(wrong)} 句")
        same_changed = [rid for rid in info["truth"] if rid not in info["diff"] and rid not in info["near"] and rid in draft]
        check("对的句子一个字都没动", not same_changed, f"{len(same_changed)} 句")
        near_changed = [rid for rid in info["near"] if rid in draft]
        check("新讲的课里和母本只差一个词的句子一个字都没动", not near_changed, f"{len(near_changed)} 句")
        check("老师自己打的「介绍词」没被改", "介绍词" in draft.get(info["typed"], {}).get("text", ""))
        panel = click_row(page, info["typed"])  # 第二轮：一键校正改了这一行别的字以后，说明照样看得到
        check("一键校正以后，老师改过的那一行照样看得到「和母本不一样、程序没有动的地方」",
              "和母本不一样、程序没有动的地方" in panel and "介绍词" in panel, panel[-120:])
        page.screenshot(path=str(work / "母本优先_一键校正以后.png"), full_page=False)
        check("网页没有脚本错误", not errors, "; ".join(errors[:3]))
        browser.close()
    passed = sum(1 for _n, ok, _d in RESULTS if ok)
    out = [f"母本优先浏览器实测（{time.strftime('%Y-%m-%d %H:%M')}）：{passed} / {len(RESULTS)} 通过"]
    out += [("通过 " if ok else "没通过 ") + n + (f"（{d}）" if d else "") for n, ok, d in RESULTS]
    (Path(__file__).resolve().parent / "浏览器实测结果.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(out[0])


if __name__ == "__main__":
    if sys.argv[1] == "setup":
        setup(Path(sys.argv[2]).resolve())
    else:
        run_check(sys.argv[2], Path(sys.argv[3]).resolve())
