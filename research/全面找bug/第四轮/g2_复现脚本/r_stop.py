# 复现 proofcheck#1：🔍 中途停止，一键校正去掉的标红和错的建议又回来了（按钮还是灰的）
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
import sys, tempfile, unittest.mock as um
sys.path.insert(0, str(ROOT) + "/tests")
from conftest import make_cfg
from pathlib import Path
from voicetwin import workflows as wf
from voicetwin.data import proofcheck as pc, review
from voicetwin.utils import progress as pg

T = ["它最经常用在定语从句里面", "这个句子完全没有错误我们继续", "我们来看下一个例子好不好"]
HEARD = {"c000": "它很经常用在定语从句里面"}

def auto_check(project, cfg, stop_after=None, stop_in_merge=False):
    class FakeRunner(pc._EngineRunner):
        def recognize(self, rec, lang):
            return HEARD.get(rec["id"], rec["text"]), None, pc.ENGINE_FUNASR
    calls = {"n": 0}
    def prog(f, msg):
        calls["n"] += 1
        if stop_after is not None and msg.startswith(f"已检查 {stop_after} /"):
            pg.request_cancel()
        if stop_in_merge and msg.startswith("和「一键全部文字校正」"):
            pg.request_cancel()
    try:
        with um.patch.object(pc, "_EngineRunner", FakeRunner):
            return pc.find_suspects(project, cfg, progress=prog)
    except pg.TaskCancelled as exc:
        return f"stopped: {exc}"
    finally:
        pg.clear_cancel()

def shown(project, rid="c000"):
    rec = {r["id"]: r for r in project.load_manifest()}[rid]
    cur = review.current_values(rec, review.load_draft(project).get(rid))["text"]
    info = review.analyze(rec, cur)
    return [cur[s:e] for s, e in info["red"]], info["edits"]

for case in ("full", "stop_loop", "stop_merge"):
    with tempfile.TemporaryDirectory() as d:
        cfg = make_cfg(Path(d) / "ws")
        project = wf.Project(cfg, "v").ensure()
        project.save_manifest([{"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "text": t, "lang": "zh",
                                "duration": 3.0, "keep": True, "split": "train"} for i, t in enumerate(T)])
        auto_check(project, cfg)
        print(case, "1st 🔍:", shown(project))
        # 母本证明「最」没错：自带母本里没有这句，这里用上传的讲稿
        txt = Path(d) / "讲稿.txt"
        txt.write_text("它最经常用在定语从句里面，大家要记住。\n", encoding="utf-8")
        wf.run_transcript_fix(cfg, "v", once=True, files=[str(txt)])
        print("  after one-click:", shown(project), "grey:", wf.textfix_used(cfg, "v"))
        r = auto_check(project, cfg, stop_after=2 if case == "stop_loop" else None, stop_in_merge=case == "stop_merge")
        print("  2nd 🔍:", r if isinstance(r, str) else "finished", "->", shown(project), "grey:", wf.textfix_used(cfg, "v"))
