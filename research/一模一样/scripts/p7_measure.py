"""「一模一样」P7 的几项实测（开发机，不需要显卡）：

1. VoiceTwin 自己的 1A（gsv_scripts/get_text_mixed.py）用测试模式（VOICETWIN_TEXT_DRYRUN=1、替身的 LangSegmenter /
   clean_text，不算 BERT）处理老师的 1004 句（母本_修缮后.csv 里 keep=1 的），分 1 路和 2 路：用了多久、写出几句、
   几句夹着英文（替身按英文字母切，和 measure_mixed.py 的数法一样，应该是 559 句）。真的 LangSegmenter 和 BERT 开发机上没有，
   所以这里只量程序本身（读写、合并、分路），不代表老师电脑上的速度。
2. 网页预览每次都要算的素材指纹：1004 个录音文件的「名字|大小|修改时间」（_clip_signature）要多久。
3. 「一模一样」的训练计划：老师的素材（984 条、32.8 分钟）在不同每批条数下的轮数和保存间隔（和标准的比较）。

在仓库根目录运行：python research/一模一样/scripts/p7_measure.py"""
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from fake_gptsovits import build_fake_root  # noqa: E402

from voicetwin.backends import gptsovits as gsv  # noqa: E402
from voicetwin.utils.textutil import count_cjk, en_words  # noqa: E402

rows = [r for r in csv.DictReader(open(ROOT / "research/文字校正/老师的母本/母本_修缮后.csv", encoding="utf-8-sig"))
        if r["keep"] == "1"]
tmp = Path(tempfile.mkdtemp(prefix="p7_"))
try:
    root = build_fake_root(tmp / "GSV")
    lst = tmp / "train.list"
    lines = []
    for r in rows:
        lang = "zh" if count_cjk(r["text"]) else "en"
        lines.append(f"{r['id']}.wav|vt|{lang}|{r['text']}")
    lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"老师的素材：{len(rows)} 句；夹着英文的中文句子（measure_mixed.py 的数法）："
          f"{sum(1 for r in rows if count_cjk(r['text']) and en_words(r['text']))} 句")
    for parts in (1, 2):
        opt = tmp / f"opt{parts}"
        env = dict(os.environ, inp_text=str(lst), opt_dir=str(opt), all_parts=str(parts), version="v2ProPlus",
                   is_half="True", exp_name="vt", VOICETWIN_TEXT_DRYRUN="1",
                   PYTHONPATH=os.pathsep.join([str(root), str(root / "GPT_SoVITS")]))
        t0 = time.perf_counter()
        procs = [subprocess.Popen([sys.executable, "-s", str(gsv.MIXED_SCRIPT)], cwd=str(root),
                                  env=dict(env, i_part=str(i)), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                 for i in range(parts)]
        outs = [p.communicate()[0].decode("utf-8", "replace") for p in procs]
        secs = time.perf_counter() - t0
        written = sum(len([x for x in (opt / f"2-name2text-{i}.txt").read_text(encoding="utf-8").split("\n") if x.strip()])
                      for i in range(parts))
        en_lines = sum(int(ln.split()[1]) for o in outs for ln in o.splitlines() if ln.startswith("VT_EN_LINES"))
        codes = [p.returncode for p in procs]
        print(f"{parts} 路：退出码 {codes}，写出 {written}/{len(rows)} 句，夹着英文 {en_lines} 句，用了 {secs:.2f} 秒"
              "（测试模式，不算 BERT）")

    wav_dir = tmp / "clips"
    wav_dir.mkdir()
    names = [f"{r['id']}.wav" for r in rows]
    for n in names:
        (wav_dir / n).write_bytes(b"RIFF" + b"\0" * 1000)
    best = None
    for _ in range(5):
        t0 = time.perf_counter()
        gsv._clip_signature(names, wav_dir)
        dt = time.perf_counter() - t0
        best = dt if best is None else min(best, dt)
    print(f"素材指纹（{len(names)} 个录音文件的名字、大小、修改时间）：最快 {best * 1000:.1f} 毫秒（5 次里最快的）")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("训练计划（老师的素材 984 条、32.8 分钟、8 GB 显卡）：")
std = gsv.plan_training(984, 32.8, 7.96, 6.8)
print(f"  标准：每批 {std['batch_size']} 条，音色 {std['sovits_epochs']} 轮每 {std['sovits_save_every']} 轮存，"
      f"语气 {std['gpt_epochs']} 轮每 {std['gpt_save_every']} 轮存")
for b in (4, 5, 6, 8, 12):
    p = gsv.plan_training(984, 32.8, 7.96, 6.8, mode="identical", probe_batch=b)
    s_upd = p["sovits_epochs"] * -(-984 // b)
    g_upd = p["gpt_epochs"] * -(-984 // b)
    print(f"  一模一样，实测每批 {b} 条：音色 {p['sovits_epochs']} 轮每 {p['sovits_save_every']} 轮存"
          f"（{p['sovits_epochs'] // p['sovits_save_every']} 个），语气 {p['gpt_epochs']} 轮每 {p['gpt_save_every']} 轮存"
          f"（{p['gpt_epochs'] // p['gpt_save_every']} 个）；按每轮 ⌈984/b⌉ 步算，音色 {s_upd} 步、语气 {g_upd} 步")
