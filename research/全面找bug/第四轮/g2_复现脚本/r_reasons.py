# 复现 proofcheck#6：撤销过 / 自己改过的改法，🔍 以后原因里还写着「另一个识别引擎听到的是「黄」」
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

T = "今天王芳同学回答得很好"
HEARD = "今天黄芳同学回答得很早"

def auto_check(project, cfg):
    class FakeRunner(pc._EngineRunner):
        def recognize(self, rec, lang):
            return HEARD, None, pc.ENGINE_FUNASR
    with um.patch.object(pc, "_EngineRunner", FakeRunner):
        return pc.find_suspects(project, cfg)

def shown(project):
    rec = project.load_manifest()[0]
    cur = review.current_values(rec, review.load_draft(project).get(rec["id"]))["text"]
    return cur, review.analyze(rec, cur)

for case in ("rejected", "typed"):
    with tempfile.TemporaryDirectory() as d:
        cfg = make_cfg(Path(d) / "ws")
        project = wf.Project(cfg, "v").ensure()
        project.save_manifest([{"id": "c000", "path": "clips/c000.wav", "text": T, "lang": "zh", "duration": 3.0,
                                "keep": True, "split": "train"}])
        auto_check(project, cfg)
        cur, info = shown(project)
        print(case, "first:", info["reasons"], info["edits"])
        if case == "rejected":
            review.adopt_suggestion(project, "c000")
            review.unadopt_suggestion(project, "c000")
            print("  rejected file:", review.load_rejected(project))
            # 只撤销「王 → 黄」：手动记一条
            from voicetwin.utils import atomic
            import json
            atomic.write_text(review._rejected_path(project) if hasattr(review, "_rejected_path") else Path(project.root) / review.REJECTED_FILE,
                              json.dumps({"c000": [["王", "黄"]]}, ensure_ascii=False))
        else:
            review.set_draft(project, "c000", text=T.replace("王", "汪"))
            review.save_rows(project)
        auto_check(project, cfg)
        cur, info = shown(project)
        print("  after 🔍:", cur, "red:", [cur[s:e] for s, e in info["red"]], "edits:", info["edits"], "reasons:", info["reasons"])
