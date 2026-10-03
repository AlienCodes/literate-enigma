"""独立复现：正确的英文语法词（whose/why/he/way/she/my/one）会不会被标红、被建议换成中文音译。
用法：python repro.py <ROOT>   ROOT = 仓库（当前代码）或旧版本解压目录。不联网、不加载模型。"""
import sys, tempfile, shutil, re, collections
from pathlib import Path
ROOT = sys.argv[1]
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/tests")  # conftest helpers (same tree)
import numpy as np, soundfile as sf
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix as tf, proofcheck as pc
import voicetwin
print("code from:", Path(voicetwin.__file__).parent)
HERE = Path(__file__).resolve().parent
tmp = Path(tempfile.mkdtemp(dir=str(HERE)))
try:
    # 1) 只看规则：老师自己改好的母本 (= 正确文字)
    m = [x for _, x in tf.builtin_mother()]
    recs = [{"id": f"m{i}", "text": t} for i, t in enumerate(m)]
    vocab = pc.english_vocab(recs) if hasattr(pc, "english_vocab") else pc.voice_vocab(recs)
    freq = pc._frequent_caps(recs)
    cnt = collections.Counter(); n = 0
    for t in m:
        sus = pc.build_suspect(t, None, None, lang="zh", frequent=freq, vocab=vocab)
        if sus:
            n += 1
            for s, e in sus["spans"]:
                cnt[t[s:e]] += 1
    print(f"[rules on mother] flagged {n} of {len(m)}; top: {cnt.most_common(8)}")
    # 也测一个全新的声音（素材里只出现一次，不在 voice_vocab）：靠母本词表
    lone = pc.english_vocab([]) if hasattr(pc, "english_vocab") else frozenset()
    print("   mother vocab has whose/why/he/way/she/my/one:", {w: (w in lone) for w in "whose why he way she my one".split()})

    # 2) 端到端：假的 FunASR 听成中文音译
    texts = ["今天我们来讲whose引导的定语从句", "那这个比较特殊的先行词就是way。", "在这个定语从句里面，谓语是give,而主语是he。",
             "关系副词主要有三个，when,where和why。", "she是主格，her是宾格", "my是形容词性物主代词"]
    heard = ["今天我们来讲户字引导的定语从句", "那这个比较特殊的先行词就是位", "在这个定语从句里面谓语是给而主语是喜",
             "关系副词主要有三个文威尔和外", "需是主格喝是宾格", "麦是形容词性物主代词"]
    cfg = make_cfg(tmp / "ws", prepare={"asr": {"engine": "faster-whisper"}})
    project = wf.Project(cfg, "v").ensure()
    rs = []
    (project.root / "clips").mkdir(parents=True, exist_ok=True)
    for k, t in enumerate(texts):
        rid = f"c{k:03d}"; rel = f"clips/{rid}.wav"
        sf.write(str(project.root / rel), np.zeros(1600 + k, dtype=np.float32), 16000)
        rs.append({"id": rid, "path": rel, "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"})
    project.save_manifest(rs)
    answers = {f"c{k:03d}": h for k, h in enumerate(heard)}

    class Fake:
        def __init__(self, name, cfg):
            self.name = name; self.label = "假" + name; self.diff = name != pc.ENGINE_WHISPER_WORDS; self.model_id = "fake"
        def applies(self, rec): return True
        def load(self): pass
        def recognize(self, wav, lang): return answers.get(wav, ""), None
        def close(self): pass
    pc._has = lambda mname: mname in {"funasr", "modelscope", "torch"}
    pc._make_checker = Fake
    pc._load_wav16 = lambda project, rec: rec["id"]
    res = pc.find_suspects(project, cfg)
    print(f"[auto check] flagged={res['flagged']} checked={res['checked']}")
    for r in project.load_manifest():
        sus = r.get("suspect") or {}
        info = review.analyze(r, r["text"])
        print(f"   {r['id']} red={[r['text'][s:e] for s, e in info['red']]} alt={sus.get('alt')!r}")
    out = wf.run_transcript_fix(cfg, "v", once=True)
    print("[one-click]", out.get("adopted"))
    draft = review.load_draft(project)
    for r in project.load_manifest():
        shown = review.current_values(r, draft.get(r["id"]))["text"]
        info = review.analyze(r, shown)
        print(f"   {r['id']} text={shown!r} red={[shown[s:e] for s, e in info['red']]} changed={shown != r['text']}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
