# _protect 的把关标准库：只用程序自带的母本（上传文字里的错字不能当成老师的说法）
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
import sys, tempfile
sys.path.insert(0, str(ROOT) + "/tests")
from conftest import make_cfg
from pathlib import Path
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix as tf
from voicetwin.data.lexicon_fix import Lexicon
ROWS = ["这个句子的谓语动词是过去式，所以我们要注意时态的变化。", "我们来看一下宾语从句，它在句子里面作宾语。",
        "接下来我们讲一讲非谓语动词的用法，这个很重要。", "这里要用一般过去时，因为是昨天发生的事情。"]
UP = ["这个句子的未雨动词是过去试，所以我们要注意时态的变化。", "我们来看一下彬鱼从句，它在句子里面作宾语。",
      "接下来我们讲一讲非未雨动词的用法，这个很重要。", "这里要用一般过去式，因为是昨天发生的事情。"]
mode = sys.argv[1] if len(sys.argv) > 1 else "new"
if mode == "noguard":  # 把关用全部母本（以前的做法）
    orig = Lexicon.build
    tf_check = tf.check_with_transcript
with tempfile.TemporaryDirectory() as d:
    cfg = make_cfg(Path(d) / "ws")
    project = wf.Project(cfg, "v").ensure()
    project.save_manifest([{"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "text": t, "lang": "zh",
                            "duration": 3.0, "keep": True, "split": "train"} for i, t in enumerate(ROWS)])
    p = Path(d) / "讲稿.txt"
    p.write_text("\n".join(UP) + "\n", encoding="utf-8")
    if mode == "noguard":
        real = tf._protect
        lines = tf.parse_mother("x.txt", "\n".join(UP))
        full = Lexicon.build([x for _, x in tf.builtin_mother()] + [x for _, x in lines])
        tf._protect = lambda fixes, cur, changed, lex: real(fixes, cur, changed, full)
    res = wf.run_transcript_fix(cfg, "v", once=True, files=[str(p)])
    draft = review.load_draft(project)
    print(mode, "fixes", res["fixes"], res["examples"])
    for r in project.load_manifest():
        cur = review.current_values(r, draft.get(r["id"]))["text"]
        info = review.analyze(r, cur)
        print("  ", "CHANGED" if cur != r["text"] else "same   ", cur, info["edits"] if info["active"] else "")
