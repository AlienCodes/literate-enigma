"""母本优先：老师上传的是「讲稿」（讲课以前写的，讲的时候会换说法）时会怎么样——如实量出来。

数据是 `../评测.py` 里开发时自己写的（不是老师的文字）：
- 场景一「同一节课的讲稿」：上传的母本 = LECTURE_A（讲稿）；老师实际说的 = CASES_A 第一列（约三分之一的句子和讲稿不一样：
  多了「那、呢、啊、一下」、换了说法、页码不一样）；识别出来的 = 第二列（放了识别错误）。
- 场景二「平时的习惯」：上传 LECTURE_B（另一节课），识别的是第三节课（CASES_C），母本里没有这些句子。
跑完整的「一键全部文字校正」（程序自带的母本 + 上传的讲稿），按句子数：改得和实际说的一模一样、没改对、
把实际说的话（讲稿里没有的说法）改成了讲稿的写法。

运行：PYTHONPATH=. /tmp/gsv39/bin/python research/文字校正/母本优先/讲稿实测.py  → 讲稿实测结果.txt
"""

import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "文字校正"))
sys.path.insert(0, str(ROOT / "tests"))

import 评测 as E  # noqa: E402
from conftest import make_cfg  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review  # noqa: E402
from voicetwin.utils.textutil import clean_transcript  # noqa: E402


def run(name, lecture, cases):
    tmp = Path(tempfile.mkdtemp(prefix="jianggao_"))
    try:
        cfg = make_cfg(tmp / "ws")
        project = wf.Project(cfg, "讲稿").ensure()
        ids = [f"k{i:03d}" for i in range(len(cases))]
        project.save_manifest([{"id": i, "path": f"clips/{i}.wav", "text": asr, "lang": "zh", "duration": 3.0,
                                "keep": True, "split": "train"} for i, (_s, asr, _k) in zip(ids, cases)])
        up = tmp / "讲稿.txt"
        up.write_text(lecture, encoding="utf-8")
        res = wf.run_transcript_fix(cfg, "讲稿", files=[str(up)])
        draft = review.load_draft(project)
        out = {"rows": len(cases), "need": 0, "exact": 0, "not_fixed": 0, "overwritten": [], "ok_changed": [],
               "mother_rows": res.get("mother_rows", 0)}
        for rid, (spoken, asr, _kind) in zip(ids, cases):
            cur = draft.get(rid, {}).get("text", asr)
            truth = clean_transcript(spoken)
            if clean_transcript(asr) != truth:
                out["need"] += 1
                if clean_transcript(cur) == truth:
                    out["exact"] += 1
                else:
                    out["not_fixed"] += 1
            elif cur != asr:
                out["ok_changed"].append(f"「{asr}」→「{cur}」")
            # 实际说的话（讲稿里没有的说法）被改成了讲稿的写法：改完离实际说的更远
            if cur != asr and review.unit_dist(cur, truth) > review.unit_dist(asr, truth):
                out["overwritten"].append(f"说的是「{spoken}」→ 改成了「{cur}」")
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    lines = [f"母本优先：上传讲稿时（{time.strftime('%Y-%m-%d %H:%M')}，数据是开发时自己写的，见 ../评测.py）", ""]
    for name, lecture, cases in (("场景一：同一节课的讲稿（讲的时候约三分之一的句子换了说法）", E.LECTURE_A, E.CASES_A),
                                 ("场景二：另一节课的讲稿（母本里没有这些句子）", E.LECTURE_B, E.CASES_C)):
        r = run(name, lecture, cases)
        lines += [f"## {name}",
                  f"{r['rows']} 句，识别有错的 {r['need']} 句：改得和实际说的一模一样 {r['exact']} 句，没改对 {r['not_fixed']} 句；"
                  f"在母本里找到了差不多的句子 {r['mother_rows']} 句",
                  f"识别本来就对的句子被改：{len(r['ok_changed'])} 句；把实际说的话改成讲稿写法（离实际说的更远）：{len(r['overwritten'])} 句"]
        lines += [f"  - {x}" for x in r["ok_changed"][:10]]
        lines += [f"  - {x}" for x in r["overwritten"][:10]]
        lines.append("")
    text = "\n".join(lines)
    print(text)
    (Path(__file__).resolve().parent / "讲稿实测结果.txt").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
