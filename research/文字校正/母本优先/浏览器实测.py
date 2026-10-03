"""母本优先：真实浏览器（gradio 4.24、和整合包同版本的 Python 3.9 + pypinyin + jieba）里看一遍。

两步（工作文件夹随便给一个临时的，跑完自己删掉）：
1. 准备：PYTHONPATH=. /tmp/gsv39/bin/python research/文字校正/母本优先/浏览器实测.py setup <工作文件夹>
   用老师修缮以前的句子建一个声音：40 句和母本不一样 + 20 句对的，片段 id 全换掉（像重新准备过素材）；
   其中一句老师自己改过（和母本不一样）；然后跑一次「自动查错字」（第二个识别引擎是假的，把一句对的「定语」听成「定于」）。
2. 打开网页（同一个 Python 跑 voicetwin.webui.launcher，工作文件夹里有 config.yaml），再：
   PYTHONPATH=. /tmp/gsv39/bin/python research/文字校正/母本优先/浏览器实测.py check <网址> <工作文件夹>
检查：说明里写着「母本最优先」；还没点一键校正，「修改建议」那一列就有「按母本：」；和母本矛盾的「定语 → 定于」没有出现；
点一行看得到「按母本改成」「母本里的原句」；老师自己改过的那一行看得到「和母本不一样、程序没有动的地方」；
点「📝 一键全部文字校正」以后结果里写着在母本里找到了几句，40 句全部改得和母本一模一样、对的 20 句一个字都没动；网页没有脚本错误。
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


def rows():
    orig = list(csv.DictReader(open(D / "母本_原文.csv", encoding="utf-8-sig")))
    clean = {r["id"]: r["text"] for r in csv.DictReader(open(D / "母本_修缮后.csv", encoding="utf-8-sig"))}
    ok = [(r["text"], clean[r["id"]]) for r in orig if r["keep"] == "1" and r["drop_reason"] != "老师删除"]
    diff = [x for x in ok if x[0] != x[1]][:40]
    same = [x for x in ok if x[0] == x[1] and "定语" in x[0]][:20]
    return diff, same


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
    diff, same = rows()
    sr = 16000
    tt = np.arange(int(3.0 * sr)) / sr
    wav = (0.1 * np.sin(2 * np.pi * 150 * tt) * (0.5 - 0.5 * np.cos(2 * np.pi * 3 * tt))).astype(np.float32)
    recs, truth = [], {}
    for k, (t, c) in enumerate(diff + same):
        rid = f"0300_beefee_{k:04d}"
        sf.write(str(project.clips_dir / f"{rid}.wav"), wav, sr)
        recs.append({"id": rid, "path": f"clips/{rid}.wav", "text": t, "lang": "zh", "duration": 3.0, "voiced": 2.5,
                     "keep": True, "split": "train", "asr_done": True, "source": "第1课"})
        truth[rid] = c
    project.save_manifest(recs)
    project.export_csv(recs)
    # 老师自己改过的一句：把母本里的「介词」打成了「介绍词」（这一句另外还有别的识别错）
    k = next(i for i, (t, c) in enumerate(diff) if "借词" in t and t.count("借词") == 1)
    rid_typed = recs[k]["id"]
    review.set_draft(project, rid_typed, text=recs[k]["text"].replace("借词", "介绍词"))
    # 第二个识别引擎把一句对的「定语」听成「定于」（和母本矛盾）
    rid_wrong = recs[len(diff)]["id"]
    heard = {rid_wrong: recs[len(diff)]["text"].replace("定语", "定于", 1)}

    class FakeRunner(pc._EngineRunner):
        def recognize(self, rec, lang):
            return heard.get(rec["id"], rec["text"]), None, pc.ENGINE_FUNASR

    with um.patch.object(pc, "_EngineRunner", FakeRunner):
        pc.find_suspects(project, cfg)
    (work / "truth.json").write_text(json.dumps({"truth": truth, "typed": rid_typed, "wrong": rid_wrong,
                                                 "diff": [r["id"] for r in recs[:len(diff)]]},
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

    def click_row(page, rid):
        page.evaluate("""(rid) => { const rows = Array.from(document.querySelectorAll('#vt-clips tbody.tbody tr'));
          const r = rows.find(tr => tr.innerText.includes(rid)); if (r) { r.scrollIntoView(); } }""", rid)
        time.sleep(0.5)
        cell = page.locator("#vt-clips tbody.tbody tr", has_text=rid).first.locator("td").nth(1)
        cell.click()
        time.sleep(2.5)
        return text_of(page, ".vt-diff")

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
        table = text_of(page, "#vt-clips tbody.tbody")
        check("还没点一键校正，「修改建议」那一列就有「按母本：」的建议", table.count("按母本：") >= 30, f"{table.count('按母本：')} 处")
        check("和母本矛盾的「定语 → 定于」没有出现", "定语 → 定于" not in table and "→ 定于" not in table)
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
        manifest = {r["id"]: r for r in json.loads((voice_dir / "manifest.json").read_text(encoding="utf-8"))}
        from voicetwin.utils.textutil import clean_transcript

        wrong = [rid for rid in info["diff"] if rid != info["typed"]
                 and clean_transcript(draft.get(rid, {}).get("text", manifest[rid]["text"])) != clean_transcript(info["truth"][rid])]
        check("和母本不一样的句子全部改得和母本一模一样（老师自己改过的那句除外）", not wrong, f"不一样的 {len(wrong)} 句")
        same_changed = [rid for rid in info["truth"] if rid not in info["diff"] and rid in draft]
        check("对的句子一个字都没动", not same_changed, f"{len(same_changed)} 句")
        check("老师自己打的「介绍词」没被改", "介绍词" in draft.get(info["typed"], {}).get("text", ""))
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
