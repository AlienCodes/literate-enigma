# 复现 textfix#1：上传的讲稿里的同音错字把校对表里本来对的字改错（标准库里的术语也会）
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
import sys, tempfile
sys.path.insert(0, str(ROOT) + "/tests")
from conftest import make_cfg
from pathlib import Path
from voicetwin import workflows as wf
from voicetwin.data import review
ROWS = ["这个句子的谓语动词是过去式，所以我们要注意时态的变化。",
        "好，我们一起来读一下这个句子，注意它的语调和停顿。",
        "我们再来看一个同位语从句的例子，它和定语从句不一样。",
        "这个动名词在句子里面作主语，后面的动词要用单数。"]
UP = ["这个句子的谓语动词是过去试，所以我们要注意时态的变化。",
      "好，我们一起来度一下这个句子，注意它的语调和停顿。",
      "我们在来看一个同位于从句的例子，它和定语从句不一样。",
      "这个动名词在句子里面作主雨，后面的动词要用单数。"]
for upload in (False, True):
    with tempfile.TemporaryDirectory() as d:
        cfg = make_cfg(Path(d) / "ws")
        project = wf.Project(cfg, "v").ensure()
        project.save_manifest([{"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "text": t, "lang": "zh",
                                "duration": 3.0, "keep": True, "split": "train"} for i, t in enumerate(ROWS)])
        files = None
        if upload:
            p = Path(d) / "讲稿.txt"
            p.write_text("\n".join(UP) + "\n", encoding="utf-8")
            files = [str(p)]
        res = wf.run_transcript_fix(cfg, "v", once=True, files=files)
        draft = review.load_draft(project)
        print("upload" if upload else "no upload", "fixes:", res["fixes"], "adopted:", res["adopted"]["changes"], "examples:", res["examples"])
        for r in project.load_manifest():
            cur = review.current_values(r, draft.get(r["id"]))["text"]
            if cur != r["text"]:
                print("  CHANGED", cur, "| reasons:", (r.get("suspect") or {}).get("reasons"))
            else:
                info = review.analyze(r, cur)
                if info["active"]:
                    print("  flagged", cur, [cur[s:e] for s, e in info["red"]], info["edits"], info["reasons"])
