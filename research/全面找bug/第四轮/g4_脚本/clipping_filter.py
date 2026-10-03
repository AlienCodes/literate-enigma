"""第四轮 g4 / pipeline#6：「有爆音」过滤。

把测试用的讲课录音放大不同倍数再削顶（满格就截平），走一遍真的「准备素材」（假的引擎、mfcc 声纹、不识别），
看每段记下的 clip_src（原始录音里满格样本的比例）、clip_ratio（统一音量以后算的，修以前只看它）和被丢掉的条数。
运行：/tmp/gsv39/bin/python research/全面找bug/第四轮/g4_脚本/clipping_filter.py
"""
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from conftest import make_cfg, make_lecture  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402


def main():
    base = Path(tempfile.mkdtemp(prefix="vt_clip_"))
    try:
        for gain in (1.0, 1.5, 2.0, 2.5, 3.0, 6.0):
            src = base / f"in{gain}"
            p = make_lecture(src / "a.wav", repeats=1)
            wav, sr = sf.read(str(p), dtype="float32")
            x = np.clip(wav * gain, -1, 1)
            sf.write(str(p), x, sr, subtype="PCM_16")
            cfg = make_cfg(base / f"ws{gain}")
            res = wf.run_prepare(cfg, "v", [str(src)])
            rows = wf.open_project(cfg, "v").load_manifest()
            cs = [r.get("clip_src") or 0.0 for r in rows]
            print(f"放大 {gain} 倍：整段满格 {np.mean(np.abs(x) >= 0.995):.4f}；每段 clip_src {min(cs):.4f}~{max(cs):.4f}；"
                  f"clip_ratio 最大 {max(r['clip_ratio'] for r in rows)}；丢掉 {res['dropped']}；"
                  f"留下 {res['clips_kept']}/{len(rows)}")
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
