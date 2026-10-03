"""算几句话在各档位下的句子缓存键（「一模一样」第 1 步：发给引擎的语言改成「有汉字就是 zh」以后，
没有这个问题的句子缓存键必须一个字节都不变，以前生成好的照常直接用）。

在仓库根目录运行：python3 research/一模一样/scripts/golden_cache_keys.py
改之前（提交 e02dd2f）跑出来的结果写进了 tests/test_identical_tier.py 的 GOLDEN_KEYS / OLD_BUGGY_KEYS。"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from conftest import make_cfg  # noqa: E402
from voicetwin.project import Project  # noqa: E402
from voicetwin.synth import engine as eng  # noqa: E402
from voicetwin.synth.script import ScriptSegment  # noqa: E402

REFS = [
    {"id": "r_zh_s1", "path": "references/a.wav", "text": "我们今天先来看第一个例子。", "lang": "zh", "kind": "statement"},
    {"id": "r_zh_s2", "path": "references/b.wav", "text": "这个关系代词相对来说比较特殊，大家要注意。", "lang": "zh", "kind": "statement"},
    {"id": "r_zh_q", "path": "references/c.wav", "text": "大家想一想，这道题应该怎么做呢？", "lang": "zh", "kind": "question"},
    {"id": "r_zh_s3", "path": "references/d.wav", "text": "好，这就是今天的全部内容。", "lang": "zh", "kind": "statement"},
    {"id": "r_en_s", "path": "references/e.wav", "text": "Next, let's look at a slightly more complex example.", "lang": "en", "kind": "statement"},
]
SEGS = [
    ("今天我们来学习列表推导式。", "zh", "statement"),
    ("大家想一想，这段代码输出的结果是什么？", "zh", "question"),
    ("首先，as这个关系代词经常出现在非限定性定语从句中。", "zh", "statement"),
    ("We can add a condition at the end of the expression.", "en", "statement"),
    ("比如 This is a very long English example sentence used to show the rule clearly.", "en", "statement"),
]


class KeyBackend:
    name = "dummy"
    display_name = "测试"
    supports_aux_refs = True
    bcfg = {}

    def model_id(self):
        return "golden-model"

    def speed_calibration(self):
        return {"zh": 1.0, "en": 1.05}


def keys(ws: Path) -> dict:
    cfg = make_cfg(ws)
    p = Project(cfg, "金键")
    p.root.mkdir(parents=True, exist_ok=True)
    p.references_path.write_text(json.dumps(REFS, ensure_ascii=False), encoding="utf-8")
    out = {}
    for q in ("fast", "balanced", "best", "max", "perfect"):
        for tier in ("high", "low"):
            n = eng.Narrator(cfg, p, KeyBackend(), quality=q, tier=tier)
            for i, (text, lang, kind) in enumerate(SEGS):
                seg = ScriptSegment(text=text, display=text, lang=lang, kind=kind, index=i)
                out[f"{q}/{tier}/{i}"] = n._plan(seg).key
    return out


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        print(json.dumps(keys(Path(d) / "ws"), indent=1))
