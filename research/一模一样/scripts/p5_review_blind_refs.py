"""P5 审查意见 5 的复现：盲听测试用「一模一样」生成时，有没有拿盲听里当「真人」播放的录音当参考（主参考、辅助参考）。

测试引擎、高显存档、测试声音（conftest 的讲课录音，30 段里验证集 3 段）、盲听 12 段（验证集不够，要用训练集的录音）。
记下每次请求发给引擎的 ref_audio / aux_ref_audio_paths，和盲听答案里的「真人」录音比。
用法：python p5_review_blind_refs.py（不联网、不用模型；临时文件夹用完删掉）。
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

from conftest import make_cfg, make_lecture  # noqa: E402

from voicetwin import workflows as wf  # noqa: E402
from voicetwin.backends import base  # noqa: E402
from voicetwin.eval import sv_models  # noqa: E402
from voicetwin.synth import engine as eng  # noqa: E402

N_BLIND = 12
sv_models.download = lambda cfg, progress=None, keys=None: []  # 不下载声纹模型
eng._vram_tier = lambda: "high"

work = Path(tempfile.mkdtemp(prefix="p5_blind_"))
try:
    make_lecture(work / "lect" / "第1课.wav")
    cfg = make_cfg(work / "ws")
    wf.run_prepare(cfg, "测试声音", [str(work / "lect")])
    wf.review_confirm(cfg, "测试声音")
    project = wf.open_project(cfg, "测试声音", must_exist=True)

    used = []  # (要读的文字, 主参考, [辅助参考])
    cls = type(base.get_backend("dummy", cfg, project))
    for name in ("synthesize", "synthesize_many"):
        fn = getattr(cls, name, None)
        if fn is None:
            continue

        def wrap(fn=fn):
            def inner(self, req, *a, **k):
                used.append((req.text, Path(str(req.ref_audio)).stem, [Path(str(x)).stem for x in req.aux_refs or []]))
                return fn(self, req, *a, **k)
            return inner

        setattr(cls, name, wrap())

    res = wf.build_blind_test(cfg, project.voice, n=N_BLIND, quality="identical", seed=1)
    ans = json.loads(Path(res["answer_path"]).read_text(encoding="utf-8"))
    real = {it["clip"] for it in ans["items"] if it["truth"] == "真人"}
    recs = {r["id"]: r for r in project.load_manifest()}
    bank = json.loads((project.root / "refs_bank.json").read_text(encoding="utf-8"))
    in_bank = sorted({e["id"] for e in bank.get("entries") or []} & real)
    main_hits = sorted({m for _, m, _ in used if m in real})
    aux_hits = sorted({a for _, _, aux in used for a in aux if a in real})
    print(f"盲听 {N_BLIND} 段：当「真人」播放的录音 {len(real)} 段，其中训练集的 "
          f"{sum(1 for i in real if recs[i].get('split') != 'val')} 段；参考录音库里本来就有的 {len(in_bank)} 段")
    print(f"发给引擎的请求 {len(used)} 次；主参考是「真人」录音的 {len(main_hits)} 段，辅助参考是「真人」录音的 "
          f"{len(aux_hits)} 段")
finally:
    shutil.rmtree(work, ignore_errors=True)
