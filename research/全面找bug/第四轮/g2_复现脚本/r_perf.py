# textfix#2：大上传的保存 / 每次刷新说明用时（g2 修改后；复查时修正：每行去掉换行符，不然「（第k遍）」单独成一行，
# 剩下的句子和程序自带的母本一模一样，现在会算成「程序里已经有」，测不到大文件）
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
import sys, tempfile, time
sys.path.insert(0, str(ROOT) + "/tests")
from conftest import make_cfg
from pathlib import Path
from voicetwin import workflows as wf
from voicetwin.data import transcript_fix as tf
lines = [r.rstrip("\n").split("\t")[-1] for r in open(str(ROOT) + "/voicetwin/data/lexicon/core_corpus.tsv", encoding="utf-8") if r.strip() and not r.startswith("#")]
with tempfile.TemporaryDirectory() as d:
    cfg = make_cfg(Path(d) / "ws")
    project = wf.Project(cfg, "v").ensure()
    project.save_manifest([{"id": "c0", "path": "clips/c0.wav", "text": "这个句子完全没有错误我们继续", "lang": "zh", "duration": 3.0, "keep": True, "split": "train"}])
    for reps in (9, 7):  # 9 份超过上限（不存）；7 份能用
        f = Path(d) / f"讲稿合集{reps}.txt"
        f.write_text("\n".join(f"{x}（第{k}遍）" for k in range(reps) for x in lines), encoding="utf-8")
        t0 = time.time()
        try:
            info = tf.save_transcripts(project, [str(f)], refuse_useless=True)
            print(f"{reps} 份 {f.stat().st_size / 1e6:.2f} MB：存好 {time.time() - t0:.1f} 秒，chars {info['chars']} / room {info['room']}")
        except ValueError as exc:
            print(f"{reps} 份 {f.stat().st_size / 1e6:.2f} MB：没存（{time.time() - t0:.1f} 秒）：{str(exc)[:60]}")
    for k in range(3):
        t0 = time.time(); tf.transcript_info(project); print(f"transcript_info 第 {k + 1} 次 {time.time() - t0:.2f} 秒")
