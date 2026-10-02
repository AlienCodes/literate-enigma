"""v18.4 真实浏览器（gradio 4.24、和整合包同版本的 Python 3.9）里点一遍：
1. 没确认训练素材：训练页说明、点「开始训练」不开始；
2. 确认训练素材以后：训练 → 自动挑选最像的模型（推理服务是真实的 api_v2.py）走完；
3. 引擎坏了：点「重新挑选最佳模型」很快报出原因，「详细过程」里有问题报告、logs 里有报告文件。
截图放在 shots/。"""
import json
import shutil
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

B = Path(__file__).resolve().parent
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:7941/"
SHOTS = B / "shots"
SHOTS.mkdir(exist_ok=True)
WORK = B / "work"
VOICE = WORK / "ws" / "老师的声音"
RESULTS = []


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


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL)
        page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=90000)
        time.sleep(2)
        title = page.evaluate("() => document.querySelector('.vt-header h1').innerText")
        check("网页标题仍是 v18", "VoiceTwin v18" in title and "18.4" not in title, title)

        # ① 没确认训练素材
        page.get_by_role("tab", name="② 训练模型").click()
        time.sleep(2)
        plan = wait_text(page, "body", ["还没有确认训练素材"], 20)
        check("训练页说明「还没有确认训练素材」", "还没有确认训练素材" in plan and "确认训练素材" in plan)
        page.screenshot(path=str(SHOTS / "01_train_tab_not_confirmed.png"))
        page.get_by_role("button", name="开始训练").click()
        bar = wait_text(page, ".vt-bar-box", ["还没有确认训练素材"], 30)
        check("点「开始训练」不开始，告诉老师先确认", "还没有确认训练素材" in bar and "✅ 确认训练素材" in bar, bar[:120])
        check("真的没开始（没有训练列表）", not (VOICE / "exports" / "gptsovits" / "train.list").exists())
        check("这种提示不生成问题报告", not list((VOICE / "logs").glob("问题报告_*.txt")))
        page.screenshot(path=str(SHOTS / "02_click_train_not_confirmed.png"))

        # ② 确认训练素材 → 训练 + 自动挑选
        page.get_by_role("tab", name="① 准备素材").click()
        time.sleep(1)
        page.get_by_role("button", name="✅ 确认训练素材").click()
        t = wait_text(page, "body", ["训练素材已确认"], 60)
        check("确认训练素材成功", "训练素材已确认" in t)
        page.get_by_role("tab", name="② 训练模型").click()
        time.sleep(2)
        plan = text_of(page, "body")
        check("确认以后训练页不再提醒", "还没有确认训练素材" not in plan)
        page.get_by_role("button", name="开始训练").click()
        md = wait_text(page, "body", ["训练完成（", "没有完成"], 600)
        page.screenshot(path=str(SHOTS / "03_trained.png"), full_page=False)
        ok_sel = "已经自动挑出最像你的版本" in md and "挑选最像你的模型」这一步没成功" not in md
        check("训练完成，并且自动挑选成功（推理服务是真实的 api_v2.py）", ok_sel,
              [ln for ln in md.splitlines() if "训练完成" in ln or "挑选" in ln][:4])
        models = json.loads((VOICE / "models.json").read_text(encoding="utf-8"))["gptsovits"]
        check("models.json 里有挑选结果", bool(models.get("selection", {}).get("results")) and bool(models.get("selected")))
        api_log = (VOICE / "logs" / "gptsovits_api.log").read_text(encoding="utf-8", errors="replace")
        check("引擎记录里没有 500 错误（只算停止时的 exit）",
              all("/control?command=exit" in ln for ln in api_log.splitlines() if " 500 " in ln))

        # ③ 引擎坏了 → 很快报出原因 + 问题报告
        tts = WORK / "GSV" / "GPT_SoVITS" / "TTS_infer_pack" / "TTS.py"
        shutil.move(str(tts), str(tts) + ".bak")
        try:
            t0 = time.time()
            page.get_by_role("button", name="重新挑选最佳模型").click()
            bar = wait_text(page, ".vt-bar-box", ["没有完成"], 180)
            took = time.time() - t0
            check("引擎起不来时很快报错（不再等 10 分钟）", "没有完成" in bar and took < 120, f"{took:.0f} 秒")
            md = text_of(page, "body")
            check("出错说明里写着问题报告文件", "已自动生成问题报告" in md and "问题报告_" in md)
            # 每个页面下面都有一个「详细过程」，点现在这一页（看得见的）那个
            page.evaluate("""() => { const s = Array.from(document.querySelectorAll('span'))
                .filter(e => e.innerText.trim() === '详细过程（出问题时可以复制给帮你的人）' && e.offsetParent !== null);
                if (s.length) s[0].click(); }""")
            time.sleep(1.5)
            logs = page.evaluate("() => Array.from(document.querySelectorAll('textarea')).map(t => t.value).join('\\n')")
            check("「详细过程」里有问题报告：原因、自动诊断出的线索",
                  "📋 问题报告" in logs and "原因：" in logs and "自动诊断出的线索" in logs,
                  [ln for ln in logs.splitlines() if "原因：" in ln or "引擎报错" in ln][:3])
            reports = sorted((VOICE / "logs").glob("问题报告_*.txt"))
            body = reports[-1].read_text(encoding="utf-8-sig") if reports else ""
            check("logs 里有完整的问题报告（含引擎记录、电脑情况）",
                  bool(reports) and "【合成引擎的记录" in body and "【电脑情况】" in body and "ModuleNotFoundError" in body)
            page.screenshot(path=str(SHOTS / "04_engine_broken_report.png"), full_page=True)
        finally:
            shutil.move(str(tts) + ".bak", str(tts))

        # ④ 引擎修好以后：③ 生成讲课音频（推理服务是真实的 api_v2.py）
        page.get_by_role("tab", name="③ 生成讲课音频").click()
        time.sleep(1.5)
        page.get_by_label("讲稿").fill("大家好，今天我们讲定语从句。Let's begin.")
        before = set((VOICE / "outputs").glob("*.wav"))
        page.get_by_role("button", name="生成", exact=True).click()
        t = wait_text(page, "body", ["生成好了", "没有完成"], 600)
        new_wavs = set((VOICE / "outputs").glob("*.wav")) - before
        check("生成讲课音频走完，存下了音频文件", bool(new_wavs) and "没有完成" not in t,
              [ln for ln in t.splitlines() if "生成好了" in ln or "没有完成" in ln][:3])
        page.screenshot(path=str(SHOTS / "05_generated.png"))
        check("网页上没有脚本错误", not errors, errors[:3])
        browser.close()
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    out = [f"{'PASS' if ok else 'FAIL'} {n}" + (f" — {d}" if d else "") for n, ok, d in RESULTS]
    out.append(f"合计：{passed}/{len(RESULTS)} 通过")
    (B / "check_结果.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(out[-1])


if __name__ == "__main__":
    main()
