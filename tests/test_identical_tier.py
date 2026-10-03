"""「一模一样」档的第 1、2 步（research/一模一样/设计方案原文.md §2 P1 / P2，测试清单 §5.1）。

P1（对所有档位都有效的修正）：
- 发给 GPT-SoVITS 的语言：句子里只要有汉字就是 zh（以前英文单词多的中文句子被判成 en，里面的汉字全被丢掉）；
- 只有这种句子的缓存键变了，其它句子的缓存键一个字节都不变（和改之前的旧代码算出来的「金标准」比）；
- 训练列表里末尾没有标点的片段补「，」不补「。」；
- 素材准备的小结如实数出中文句子里夹着的英文。
P2（「一模一样」档的接线和默认值）：任何显卡、网页每次打开、命令行、旧版本写进 config.yaml 的默认值，都是「一模一样」；
每句至少 / 最多试几个、停下的标准是它自己的。第 2 步时它先用「完美」的一批一批地试；第 5 步（P5）起换成真正的搜索
（synth/search.py，测试在 test_identical_search.py），这里整篇走一遍的测试按新的搜索改了（意图不变）。
"""

import json
import re
import sys
import uuid
from pathlib import Path

import numpy as np
import pytest

from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.config import load_config
from voicetwin.project import Project
from voicetwin.synth import engine as eng
from voicetwin.synth.script import ScriptSegment
from voicetwin.utils.textutil import detect_lang, ensure_final_punct_train, send_lang

MIXED = "比如 This is a very long English example sentence used to show the rule clearly."
LEGACY_LINE = "  quality: balanced           # fast（每句 1 个候选）| balanced（3 个）| best（5 个并用识别校验）"


def _uniq(text: str) -> str:
    return text + "编号" + "".join(str(int(c, 16) % 10) for c in uuid.uuid4().hex[:6]) + "。"


# ============================================================================ P1：发给引擎的语言
def test_send_lang_is_zh_whenever_there_is_a_chinese_character():
    assert detect_lang(MIXED) == "en"  # 以前就是按 en 发的：GPT-SoVITS 的 en 模式把「比如」整个丢掉
    assert send_lang(MIXED, "en") == "zh"
    assert send_lang(MIXED, "zh") == "zh"
    assert send_lang("Hello everyone, this is a pure English sentence.", "en") == "en"
    assert send_lang("大家好，今天我们讲第一课。", "zh") == "zh"
    assert send_lang("Hello", "zh") == "zh"  # 没有汉字时按原来的语言
    assert send_lang("", "en") == "en"


@pytest.fixture
def quick_gsv(monkeypatch):
    """和 test_gsv_real_api.py 一样：不写 users.pth、不读真显卡、轮询快一点；让引擎的 Python 找得到测试环境的包。"""
    import os
    import sysconfig

    from voicetwin.backends.gptsovits import GPTSoVITSBackend

    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    monkeypatch.setattr(GPTSoVITSBackend, "_gpu_memory", lambda self, quick=False: (11.99, 11.2, "test"))
    monkeypatch.setattr(GPTSoVITSBackend, "POLL_SECONDS", 0.05)
    monkeypatch.setattr(GPTSoVITSBackend, "STARTUP_NOTE_SECONDS", 0.4)
    paths = [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"], os.environ.get("PYTHONPATH", "")]
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(p for p in dict.fromkeys(paths) if p))


def _free_port() -> int:
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.parametrize("api", ["abe9843", "20250606v2pro"])
def test_real_api_receives_zh_for_mixed_sentence(prepared, tmp_path, quick_gsv, api):
    """拿两个真实的 api_v2.py（老师用的 abe9843 和 20250606v2pro）：中英混合、被判成 en 的句子，实际发的是 text_lang=zh；
    参考音频的文字有汉字时 prompt_lang 也是 zh；纯英文照旧是 en。"""
    pytest.importorskip("fastapi")
    pytest.importorskip("uvicorn")
    from fake_gptsovits import REAL_API_V2, REAL_API_V2_2025, build_fake_root
    from voicetwin.backends.base import SynthRequest, get_backend

    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GPT-SoVITS", real_api=REAL_API_V2 if api == "abe9843" else REAL_API_V2_2025)
    gcfg = make_cfg(project.root.parent, backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": _free_port(), "startup_timeout": 60}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    ref = next(r for r in p2.load_references() if r.get("lang") == "zh")
    b = get_backend("gptsovits", gcfg, p2)

    def runs():
        f = root / "_real_api_calls.jsonl"
        return [json.loads(x)["req"] for x in f.read_text(encoding="utf-8").splitlines()
                if x.strip() and json.loads(x)["kind"] == "run"]

    try:
        b.start()
        b.synthesize(SynthRequest(text=MIXED, lang="en", ref_audio=p2.abspath(ref["path"]), ref_text=ref["text"],
                                  ref_lang="en", seed=3), tmp_path / "mixed.wav")
        run = runs()[-1]
        assert run["text"] == MIXED and run["text_lang"] == "zh" and run["prompt_lang"] == "zh"
        b.synthesize(SynthRequest(text="Hello everyone.", lang="en", ref_audio=p2.abspath(ref["path"]),
                                  ref_text=ref["text"], ref_lang="zh", seed=4), tmp_path / "en.wav")
        assert runs()[-1]["text_lang"] == "en"
    finally:
        b.stop()


# ---------------------------------------------------------------------------- 缓存键
_REFS = [
    {"id": "r_zh_s1", "path": "references/a.wav", "text": "我们今天先来看第一个例子。", "lang": "zh", "kind": "statement"},
    {"id": "r_zh_s2", "path": "references/b.wav", "text": "这个关系代词相对来说比较特殊，大家要注意。", "lang": "zh",
     "kind": "statement"},
    {"id": "r_zh_q", "path": "references/c.wav", "text": "大家想一想，这道题应该怎么做呢？", "lang": "zh", "kind": "question"},
    {"id": "r_zh_s3", "path": "references/d.wav", "text": "好，这就是今天的全部内容。", "lang": "zh", "kind": "statement"},
    {"id": "r_en_s", "path": "references/e.wav", "text": "Next, let's look at a slightly more complex example.",
     "lang": "en", "kind": "statement"},
]
_SEGS = [
    ("今天我们来学习列表推导式。", "zh", "statement"),
    ("大家想一想，这段代码输出的结果是什么？", "zh", "question"),
    ("首先，as这个关系代词经常出现在非限定性定语从句中。", "zh", "statement"),
    ("We can add a condition at the end of the expression.", "en", "statement"),
    (MIXED, "en", "statement"),  # 有这个问题的句子（第 4 句）
]
#: 改之前的旧代码（e02dd2f）算出来的缓存键（py3.9 / py3.11 一样）：没有问题的句子一个字节都不能变
GOLDEN_KEYS = {
    "fast/high/0": "ee291b67d3397079", "fast/high/1": "8a2d48b4e3d50372", "fast/high/2": "f0eb2bb4629f9a4a",
    "fast/high/3": "0bb15114a9079b4d", "fast/low/0": "ee291b67d3397079", "fast/low/1": "8a2d48b4e3d50372",
    "fast/low/2": "f0eb2bb4629f9a4a", "fast/low/3": "0bb15114a9079b4d",
    "balanced/high/0": "9e2ffef295a93696", "balanced/high/1": "0d6b2bd7eb181888", "balanced/high/2": "c5cfbd8724aa3d03",
    "balanced/high/3": "95f20aed1a27a732", "balanced/low/0": "9e2ffef295a93696", "balanced/low/1": "0d6b2bd7eb181888",
    "balanced/low/2": "c5cfbd8724aa3d03", "balanced/low/3": "95f20aed1a27a732",
    "best/high/0": "18ce748ae51cb0e9", "best/high/1": "bafc5fd408b88420", "best/high/2": "9f3d7ccc8561cece",
    "best/high/3": "0454e4350fc0e426", "best/low/0": "18ce748ae51cb0e9", "best/low/1": "bafc5fd408b88420",
    "best/low/2": "9f3d7ccc8561cece", "best/low/3": "0454e4350fc0e426",
    "max/high/0": "f38bfbacfbfb8335", "max/high/1": "a1dcc5871eb915a6", "max/high/2": "8fb44428eeaecf37",
    "max/high/3": "2680c74dd8677a7e", "max/low/0": "56b176e19f8a6c59", "max/low/1": "c4a2acffd3557876",
    "max/low/2": "129c094cc7314d0d", "max/low/3": "0fc1dc27f369f41f",
    "perfect/high/0": "9176894d41d4d02a", "perfect/high/1": "61c008137dfed027", "perfect/high/2": "2d1d002f83ac73c2",
    "perfect/high/3": "ed87084b2b9f676b", "perfect/low/0": "8290047f8ba68fe5", "perfect/low/1": "3950a762a57d1673",
    "perfect/low/2": "5c8fe1c071a111d9", "perfect/low/3": "786f8bdac09aa5d2",
}
#: 有问题的那句（第 4 句）在旧代码里的缓存键：现在必须不一样（旧缓存里的汉字没读出来，不能再用）
OLD_BUGGY_KEYS = {
    "fast/high/4": "501aff9c54bafde9", "fast/low/4": "501aff9c54bafde9", "balanced/high/4": "d5b7bc0f4b8f7d49",
    "balanced/low/4": "d5b7bc0f4b8f7d49", "best/high/4": "35c0af0cf52ac16b", "best/low/4": "35c0af0cf52ac16b",
    "max/high/4": "7c57f57721e42534", "max/low/4": "7c721e1aca09b0fa", "perfect/high/4": "1040b139e2cdfcef",
    "perfect/low/4": "62f01978af2a8429",
}


class _KeyBackend:
    """只给缓存键用的假引擎（固定的模型标识和语速校准）。"""

    name = "dummy"
    display_name = "测试"
    supports_aux_refs = True
    bcfg: dict = {}

    def model_id(self):
        return "golden-model"

    def speed_calibration(self):
        return {"zh": 1.0, "en": 1.05}


def _key_project(tmp_path, cfg=None):
    cfg = cfg or make_cfg(tmp_path / "ws")
    project = Project(cfg, "金键")
    project.root.mkdir(parents=True, exist_ok=True)
    project.references_path.write_text(json.dumps(_REFS, ensure_ascii=False), encoding="utf-8")
    return cfg, project


def test_cache_keys_unchanged_except_for_the_language_bug(tmp_path):
    cfg, project = _key_project(tmp_path)
    keys = {}
    for q in ("fast", "balanced", "best", "max", "perfect"):
        for tier in ("high", "low"):
            n = eng.Narrator(cfg, project, _KeyBackend(), quality=q, tier=tier)
            for i, (text, lang, kind) in enumerate(_SEGS):
                keys[f"{q}/{tier}/{i}"] = n._plan(ScriptSegment(text=text, display=text, lang=lang, kind=kind,
                                                                index=i)).key
    for k, v in GOLDEN_KEYS.items():
        assert keys[k] == v, k
    for k, v in OLD_BUGGY_KEYS.items():
        assert keys[k] != v, k
    # 「一模一样」的缓存键和「完美」的不一样（档位不同、标准不同）
    n = eng.Narrator(cfg, project, _KeyBackend(), quality="identical", tier="high")
    seg = ScriptSegment(text=_SEGS[0][0], display=_SEGS[0][0], lang="zh", index=0)
    assert n._plan(seg).key not in GOLDEN_KEYS.values()


# ============================================================================ P1：训练列表的句末标点
def test_train_list_appends_comma_not_full_stop():
    f = ensure_final_punct_train
    assert f("There are some nuts which", "en") == "There are some nuts which,"
    assert f("我们今天", "zh") == "我们今天，"
    assert f("好的。", "zh") == "好的。"
    assert f("首先，", "zh") == "首先，" and f("大家想一想？", "zh") == "大家想一想？"
    assert f("He said yes.", "en") == "He said yes." and f("OK,", "en") == "OK,"
    assert f("他说：“好的。”", "zh") == "他说：“好的。”"  # 引号里已经有句号了
    assert f("他说“好的”", "zh") == "他说“好的”，"
    assert f("  我们今天  ", "zh") == "我们今天，" and f("", "zh") == ""


def test_gptsovits_list_text_uses_comma_rule(tmp_path):
    from voicetwin.data.exporters import gptsovits_list_text

    cfg = make_cfg(tmp_path / "ws")
    project = Project(cfg, "标点")
    recs = [
        {"id": "c0", "path": "clips/c0.wav", "text": "翻译成英文就是There are some nuts which", "lang": "zh",
         "keep": True, "split": "train", "duration": 3.0},
        {"id": "c1", "path": "clips/c1.wav", "text": "There are some nuts which", "lang": "en", "keep": True,
         "split": "train", "duration": 3.0},
        {"id": "c2", "path": "clips/c2.wav", "text": "好的。", "lang": "zh", "keep": True, "split": "train",
         "duration": 3.0},
        {"id": "c3", "path": "clips/c3.wav", "text": "验证用的句子", "lang": "zh", "keep": True, "split": "val",
         "duration": 3.0},
    ]
    project.save_manifest(recs)
    lines = gptsovits_list_text(project, "spk").splitlines()
    assert lines == ["c0.wav|spk|zh|翻译成英文就是There are some nuts which，", "c1.wav|spk|en|There are some nuts which,",
                     "c2.wav|spk|zh|好的。"]
    assert [r["text"] for r in project.load_manifest()][0] == "翻译成英文就是There are some nuts which"  # manifest 不改


def test_old_model_is_not_reported_as_trained_on_old_texts(tmp_path):
    """以前训练的模型，训练列表是按以前的规则（末尾补「。」）写的：老师什么都没改时，不能因为导出规则改了
    就提醒「校对表在上次训练以后改过」；真的改了文字时照样提醒。"""
    import hashlib
    import os

    from voicetwin.backends import gptsovits as g
    from voicetwin.data.exporters import gptsovits_list_text

    project = Project(make_cfg(tmp_path / "ws"), "旧模型")
    recs = [{"id": "c0", "path": "clips/c0.wav", "text": "我们今天", "lang": "zh", "keep": True, "split": "train",
             "duration": 3.0},
            {"id": "c1", "path": "clips/c1.wav", "text": "好的。", "lang": "zh", "keep": True, "split": "train",
             "duration": 3.0}]
    project.save_manifest(recs)

    class B:
        name, exp_name, version = "gptsovits", "x", "v2ProPlus"

    b = B()
    b.project = project
    b._opt_dir = lambda: tmp_path / "logs"
    old = gptsovits_list_text(project, "x", legacy_punct=True)
    assert "我们今天。" in old and "我们今天，" in gptsovits_list_text(project, "x")
    sha = hashlib.sha1(old.replace("\n", os.linesep).encode("utf-8") + B.version.encode()).hexdigest()
    project.write_json(project.models_path, {"gptsovits": {"sovits": ["a.pth"], "list_sha1": sha}})
    assert g.GPTSoVITSBackend.trained_material_note(b) == ""
    recs[1]["text"] = "好的，改过了。"
    project.save_manifest(recs)
    assert "校对表在上次训练以后改过" in g.GPTSoVITSBackend.trained_material_note(b)


# ============================================================================ P1：素材小结里的英文
def test_summarize_counts_english_inside_chinese_lines(tmp_path):
    from voicetwin.data.prepare import summarize

    project = Project(make_cfg(tmp_path / "ws"), "英文")
    recs = [
        {"id": "a", "keep": True, "lang": "zh", "duration": 300.0, "text": "首先，as这个关系代词经常出现。"},
        {"id": "b", "keep": True, "lang": "zh", "duration": 300.0, "text": "翻译成英文就是There are some nuts."},
        {"id": "c", "keep": True, "lang": "zh", "duration": 300.0, "text": "这一句没有英文。"},
        {"id": "d", "keep": False, "lang": "zh", "duration": 3.0, "text": "删掉的 hello world", "drop_reason": "x"},
    ]
    warnings = summarize(project, recs, [])["warnings"]
    line = next(w for w in warnings if "英文" in w)
    assert line.startswith("素材里有 2 句夹着英文（共 5 个英文单词），没有纯英文的句子。")
    assert not any(w.startswith("素材里没有英文") for w in warnings)
    only_zh = summarize(project, [recs[2]], [])["warnings"]
    assert any(w.startswith("素材里没有英文") for w in only_zh)


# ============================================================================ P2：档位名、默认值
@pytest.mark.parametrize("tier", ["high", "mid", "low", "none", None])
def test_resolve_quality_defaults_to_identical_on_every_tier(tier, monkeypatch):
    monkeypatch.setattr(eng, "_vram_tier", lambda: "none")
    for x in (None, "", "auto", "AUTO", "自动", "none", "None", "garbage", "不知道", 0, []):
        assert eng.resolve_quality(x, tier) == "identical", x
    for x in ("identical", "Identical", " identical ", "一模一样", "一模一样（默认）", eng.QUALITY_LABELS["identical"],
              ["identical"]):
        assert eng.resolve_quality(x, tier) == "identical", x
    assert eng.resolve_quality("perfect", tier) == "perfect" and eng.resolve_quality("完美", tier) == "perfect"
    assert eng.resolve_quality(eng.QUALITY_LABELS["perfect"], tier) == "perfect"
    assert eng.resolve_quality("balanced", tier) == "balanced" and eng.resolve_quality("均衡", tier) == "balanced"


def test_unknown_quality_is_logged_in_chinese(monkeypatch):
    seen = []
    monkeypatch.setattr(eng.log, "warning", lambda msg, *a, **k: seen.append(msg))
    assert eng.resolve_quality("超快") == "identical"
    assert seen == ["不认识的质量档位「超快」，改用默认的「一模一样」"]


def test_quality_order_labels_help():
    assert eng.QUALITY_ORDER == ("fast", "balanced", "best", "max", "perfect", "identical")
    assert eng.DEFAULT_QUALITY == "identical"
    for table in (eng.QUALITY_LABELS, eng.QUALITY_SHORT, eng.QUALITY_HELP):
        assert set(table) == set(eng.QUALITY_ORDER)
    assert eng.QUALITY_SHORT["identical"] == "一模一样"
    assert eng.QUALITY_LABELS["identical"].startswith("一模一样（默认）：") and "（最慢）" in eng.QUALITY_LABELS["identical"]
    # 「完美」不再写「最慢」「尽最大可能」：「一模一样」比它更慢
    for text in (eng.QUALITY_LABELS["perfect"], eng.QUALITY_HELP["perfect"]):
        assert "最慢" not in text and "尽最大可能" not in text and "（很慢）" in text
    assert sum("最慢" in v for v in eng.QUALITY_LABELS.values()) == 1
    assert [v for _, v in eng.quality_choices()] == list(eng.QUALITY_ORDER)
    p = eng.QUALITY_PRESETS["identical"]
    assert p["variants"] and p["match_reference"] and p["adaptive"] and p["force_asr"]
    assert p["min_candidates"] == {"high": 40, "mid": 40, "low": 16, "none": 6}
    assert p["max_candidates"] == {"high": 64, "mid": 64, "low": 32, "none": 12}
    assert p["batch"] == {"high": 12, "mid": 8, "low": 2, "none": 1}


def test_recommended_quality_is_identical_on_every_tier():
    notes = {}
    for tier in ("high", "mid", "low", "none"):
        q, note = eng.recommended_quality(tier)
        assert q == "identical" and "一模一样" in note
        notes[tier] = note
        assert wf.recommended_quality(tier)[0] == "identical"
    # 只写现在真的会做的事：「新模型第一次先做一次准备」「显存不够也不停下」等后面几步做好了再写（见 UNBUILT_PHRASES）
    assert notes["high"] == notes["mid"] and "很慢" in notes["mid"] and "按实际速度告诉你还要多久" in notes["mid"]
    assert "32 个版本" in notes["low"] and "显存偏小" in notes["low"] and "「均衡」" in notes["low"]
    assert "12 个版本" in notes["none"] and "N 卡" in notes["none"] and "「均衡」" in notes["none"]
    assert eng.recommended_quality("mid", size="显存 12 GB")[1].startswith("已选好「一模一样」（显存 12 GB）。")
    assert eng.recommended_quality("low", size="显存 6 GB")[1].startswith("已选好「一模一样」（显存 6 GB，显存偏小）")


def _no_100_promise(text: str) -> bool:
    """每个「100%」「百分之百」前面 6 个字以内都要有「不能保证 / 不会 / 做不到」。"""
    for m in re.finditer(r"100\s*%|百分之百", text):
        ok = False
        for phrase in ("不能保证", "不会", "做不到"):
            j = text.rfind(phrase, 0, m.start())
            if j >= 0 and j + len(phrase) >= m.start() - 6:
                ok = True
        if not ok:
            return False
    return True


def test_no_text_promises_100_percent():
    from voicetwin.webui import app as A

    texts = (list(eng.QUALITY_LABELS.values()) + list(eng.QUALITY_HELP.values()) + [eng.QUALITY_NOTE]
             + list(eng.QUALITY_TIER_NOTES.values()) + [A.QUALITY_NOTE, A.BLIND_QUALITY_NOTE]
             + [eng.recommended_quality(t, size="显存 8 GB")[1] for t in ("high", "mid", "low", "none")])
    for t in texts:
        assert _no_100_promise(t), t
    assert any("百分之百" in t for t in texts)  # 确实说了（做不到百分之百一样），不是没提
    # 设置文件里质量档位的说明（「"像你本人（%）"：100% = ……」是分数的定义，不是保证，不在这里查）
    yaml_text = (Path(eng.__file__).resolve().parents[1] / "default_config.yaml").read_text(encoding="utf-8")
    block = yaml_text.split("  # 质量档位", 1)[1].split("\n  quality:", 1)[0]
    assert "百分之百" in block and _no_100_promise(block)
    assert not _no_100_promise("保证 100% 一样") and _no_100_promise("不能保证百分之百一样")


def test_narrate_stage_table_for_identical():
    cfg = make_cfg(Path("."))
    assert wf.task_stages("narrate", cfg, quality="identical") == wf.STAGES_NARRATE_IDENTICAL
    assert wf.task_stages("narrate", cfg) == wf.STAGES_NARRATE_IDENTICAL  # 配置是 auto = 一模一样
    assert wf.task_stages("narrate", cfg, quality="一模一样") == wf.STAGES_NARRATE_IDENTICAL
    assert wf.task_stages("narrate", cfg, quality="perfect") == wf.STAGES_NARRATE_VARIANTS
    assert wf.task_stages("narrate", cfg, quality="fast") == wf.STAGES_NARRATE
    st = wf.STAGES_NARRATE_IDENTICAL
    assert [f for f, _ in st] == sorted(f for f, _ in st) and st[0] == (0.0, "启动合成引擎")
    # 时间点和设计方案 §2 P2 一样；0.88 这一步的名字只写现在真的会做的事（「整篇再挑一遍」等第 6 步做好了再改）
    assert st == [(0.00, "启动合成引擎"), (0.02, "准备「一模一样」"), (0.08, "逐句生成"),
                  (0.88, "按你的停顿拼接、调整音量"), (0.92, "做「去杂音」版本并比较"), (0.99, "写字幕和报告")]


def test_title_version_stays_18():
    from voicetwin.webui import app as A

    assert A.APP_TITLE_VERSION == "18" and A.PAGE_TITLE == "声音分身 VoiceTwin v18"


# ============================================================================ P2：config.yaml
def test_legacy_default_line_means_identical(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text("backend: gptsovits\nsynth:\n" + LEGACY_LINE + "\n  candidates: auto\n", encoding="utf-8")
    cfg = load_config(str(p))
    assert cfg.get_path("synth.quality") == "auto" and cfg["_legacy_quality"] == "balanced"
    assert eng.resolve_quality(cfg.get_path("synth.quality")) == "identical"
    assert wf.task_stages("narrate", cfg) == wf.STAGES_NARRATE_IDENTICAL
    # 记事本另存的 GBK + Windows 换行也认得出
    p.write_bytes(("synth:\r\n" + LEGACY_LINE + "\r\n").encode("gbk"))
    assert load_config(str(p)).get("_legacy_quality") == "balanced"
    # 自己改过的（后面的旧说明删了 / 换了档位）照常按写的来
    p.write_text("synth:\n  quality: balanced\n", encoding="utf-8")
    cfg2 = load_config(str(p))
    assert cfg2.get_path("synth.quality") == "balanced" and "_legacy_quality" not in cfg2
    p.write_text("synth:\n  quality: perfect           # fast（每句 1 个候选）| balanced（3 个）\n", encoding="utf-8")
    cfg3 = load_config(str(p))
    assert cfg3.get_path("synth.quality") == "perfect" and "_legacy_quality" not in cfg3
    # 程序里明确传了档位（overrides）时不管旧的那一行
    p.write_text("synth:\n" + LEGACY_LINE + "\n", encoding="utf-8")
    cfg4 = load_config(str(p), overrides={"synth": {"quality": "fast"}})
    assert cfg4.get_path("synth.quality") == "fast" and "_legacy_quality" not in cfg4


def test_default_config_documents_identical():
    from voicetwin.config import load_default

    d = load_default()
    assert d["synth"]["quality"] == "auto"
    ident = d["synth"]["tiers"]["identical"]
    assert ident["search_target"] == "p50" and ident["pass_target"] == "p25"
    assert ident["batch"] == ident["min_candidates"] == ident["max_candidates"] == "auto"
    assert ident["cer_target"] == {"strong": 0.03, "weak": 0.06} and ident["plateau"] == 8
    text = (Path(eng.__file__).resolve().parents[1] / "default_config.yaml").read_text(encoding="utf-8")
    assert "auto（默认）= identical「一模一样」" in text


# ============================================================================ P2：命令行
def test_cli_quality_argument(capsys):
    from voicetwin import cli

    assert cli.QUALITY_CHOICES == list(eng.QUALITY_ORDER)
    ap = cli.build_parser()
    for value, want in (("identical", "identical"), ("一模一样", "identical"), ("auto", "identical"),
                        ("perfect", "perfect"), ("完美", "perfect"), ("fast", "fast")):
        assert ap.parse_args(["say", "-v", "x", "你好", "-q", value]).quality == want
    assert ap.parse_args(["narrate", "-v", "x", "讲稿.md"]).quality is None  # 没写 -q：看 config.yaml
    with pytest.raises(SystemExit) as ei:
        ap.parse_args(["say", "-v", "x", "你好", "-q", "超快"])
    assert ei.value.code == 2
    err = capsys.readouterr().err
    assert "不认识的质量档位「超快」" in err and "fast/balanced/best/max/perfect/identical（一模一样）" in err
    assert "identical 一模一样（默认）" in cli.QUALITY_HELP


def _run_cli_say(tmp_path, monkeypatch, config_text, extra=()):
    from voicetwin import cli

    seen = {}
    monkeypatch.setattr(wf, "run_narrate", lambda *a, **k: seen.update(k) or object())
    monkeypatch.setattr(cli, "_print_narration", lambda res, full: None)
    monkeypatch.setattr(cli, "_disable_quick_edit", lambda: None)
    path = tmp_path / "config.yaml"
    path.write_text(config_text, encoding="utf-8")
    cli.main(["-c", str(path), "say", "-v", "x", "你好", *extra])
    return seen


def test_cli_notes_about_config_quality(tmp_path, monkeypatch, capsys):
    seen = _run_cli_say(tmp_path, monkeypatch, "synth:\n  quality: perfect\n")
    out = capsys.readouterr().out
    assert seen["quality"] is None  # 交给引擎按 config.yaml 的 perfect
    assert ("设置文件 config.yaml 里写了质量「perfect（完美）」，这次按它生成；想用默认的「一模一样」，"
            "把那一行改成 quality: auto，或者加 -q identical") in out
    seen = _run_cli_say(tmp_path, monkeypatch, "synth:\n" + LEGACY_LINE + "\n")
    out = capsys.readouterr().out
    assert "旧版本（v0.1.0～v0.1.3）自动写进去的默认值" in out and "按默认的「一模一样」生成" in out
    assert "这次按它生成" not in out
    # auto、写了 -q：什么都不用说
    _run_cli_say(tmp_path, monkeypatch, "synth:\n  quality: auto\n")
    assert "config.yaml" not in capsys.readouterr().out
    seen = _run_cli_say(tmp_path, monkeypatch, "synth:\n  quality: perfect\n", ("-q", "一模一样"))
    assert seen["quality"] == "identical" and "config.yaml" not in capsys.readouterr().out


# ============================================================================ P2：网页
def test_web_defaults_to_identical_on_every_gpu(tmp_path, monkeypatch):
    from voicetwin.webui import app as A

    assert A.TIER_QUALITY == {"high": "identical", "mid": "identical", "low": "identical", "none": "identical"}
    assert A.QUALITY_NOTE == eng.QUALITY_NOTE
    assert A.SPEED_BTN == "▶ 试听（快速，只听语速）"
    from voicetwin.webui import tasks

    assert tasks.KIND_BUTTONS["speed"] == A.SPEED_BTN
    statuses = {
        "high": ({"ok": True, "level": "ok", "total_gb": 23.6}, "显存 24 GB"),
        "mid": ({"ok": True, "level": "ok", "total_gb": 11.94, "nominal_gb": 12.0}, "显存 12 GB"),
        "low": ({"ok": True, "level": "warn", "total_gb": 5.8}, "显存 6 GB"),
        "none": ({"ok": False, "level": "error", "total_gb": None}, None),
    }
    ui = A.WebUI(make_cfg(tmp_path / "ws"))
    for tier, (status, size) in statuses.items():
        q, note = A._recommended_quality(status)
        assert q == "identical" and note == eng.recommended_quality(tier, size=size)[1], tier
        monkeypatch.setattr(A, "_gpu_status", lambda refresh=False, st=status: st)
        badge, radio, md = ui.on_load_gpu()
        assert radio["value"] == "identical" and md == f"{eng.QUALITY_NOTE}\n\n{note}"


def test_web_generate_and_blind_fall_back_to_identical(prepared, tmp_path, monkeypatch):
    """网页刚打开、还没收到显卡检查的结果时质量是空的：生成和盲听测试都用「一模一样」（以前是「均衡」）。"""
    import shutil

    from voicetwin.webui import app as A

    _, project, _ = prepared
    shutil.copytree(project.root, tmp_path / "ws" / project.voice)
    (tmp_path / "ws" / project.voice / "models.json").unlink(missing_ok=True)
    cfg = make_cfg(tmp_path / "ws")
    seen = {}

    def fake_stream(kind, label, voice, fn, *args, stages=None, hint="", note="", **kwargs):
        seen.update(kind=kind, fn=fn, args=args, stages=stages, kwargs=kwargs)
        yield "", {"done": True, "bar": "", "error": RuntimeError("测试"), "friendly": None}

    monkeypatch.setattr(A, "stream_task", fake_stream)
    ui = A.WebUI(cfg)
    list(ui.do_generate(project.voice, "第一句。第二句。", None, "dummy", None, 0, "", "", "", "wav"))
    assert seen["kwargs"]["quality"] == "identical" and seen["stages"] == wf.STAGES_NARRATE_IDENTICAL
    monkeypatch.setattr(wf, "build_blind_test", lambda *a, **k: {}, raising=False)
    list(ui.do_blind(project.voice, 2, None))
    assert seen["kind"] == "blind" and seen["args"][-1] == "identical"
    list(ui.do_speed_preview(project.voice, "", 0, "dummy"))  # 试听语速永远是「快速」
    assert seen["kwargs"]["quality"] == "fast" and seen["stages"] == wf.STAGES_NARRATE


def test_web_page_build_defaults(tmp_path):
    gr = pytest.importorskip("gradio")
    if not str(getattr(gr, "__version__", "")).startswith("4."):
        pytest.skip("这个测试只针对 gradio 4.x（整合包自带 4.24）")
    from voicetwin.webui import app as A

    ui = A.WebUI(make_cfg(tmp_path / "ws"))
    app = ui.build()
    assert ui.c["quality"].value == "identical"
    assert [v for _, v in ui.c["quality"].choices] == list(eng.QUALITY_ORDER)
    assert ui.c["speed_try"].value == "▶ 试听（快速，只听语速）"
    conf = json.dumps(app.get_config_file(), ensure_ascii=False)
    assert A.BLIND_QUALITY_NOTE in conf and "大约几分钟" not in conf
    assert app.title == "声音分身 VoiceTwin v18"


# ============================================================================ P2：生成引擎里的「一模一样」
def test_identical_caps_per_gpu_tier(tmp_path):
    cfg, project = _key_project(tmp_path)
    want = {"high": (12, 40, 64, 3), "mid": (8, 40, 64, 3), "low": (2, 16, 32, 2), "none": (1, 6, 12, 2)}
    for tier, (batch, lo, hi, refs) in want.items():
        n = eng.Narrator(cfg, project, _KeyBackend(), tier=tier)  # 不写质量 = 一模一样
        assert n.quality == "identical" and n.adaptive and n.want_variants and n.use_asr
        assert (n.n_candidates, n.min_candidates, n.max_candidates, n.R) == (batch, lo, hi, refs), tier
        assert n._desc() == f"每句至少试 {lo} 个、最多 {hi} 个版本，达到严格标准并且再试也不更好时才停"
        assert n._n_aux() == (2 if tier == "low" else 3)
    assert any("每句至少 16 个、最多 32 个" in x for x in eng.Narrator(cfg, project, _KeyBackend(), tier="low").notes)
    assert any("N 卡" in x and "「均衡」" in x for x in eng.Narrator(cfg, project, _KeyBackend(), tier="none").notes)
    assert eng.Narrator(cfg, project, _KeyBackend(), tier="high").notes == []
    # -n：每句最多试几个（至少试的个数跟着变小）
    n5 = eng.Narrator(cfg, project, _KeyBackend(), tier="mid", candidates=5)
    assert (n5.n_candidates, n5.min_candidates, n5.max_candidates) == (5, 5, 5)
    n50 = eng.Narrator(cfg, project, _KeyBackend(), tier="mid", candidates=50)
    assert (n50.n_candidates, n50.min_candidates, n50.max_candidates) == (8, 40, 50)
    # synth.tiers.identical 里写一个数 = 每种显卡都用它；写按显卡分档的也认
    synth = dict(cfg["synth"], tiers={"identical": {"max_candidates": 20, "min_candidates": {"mid": 10, "none": 3},
                                                    "batch": 4}})
    c2 = {**cfg, "synth": synth}
    n2 = eng.Narrator(c2, project, _KeyBackend(), tier="mid")
    assert (n2.n_candidates, n2.min_candidates, n2.max_candidates) == (4, 10, 20)
    assert eng.Narrator(c2, project, _KeyBackend(), tier="none").min_candidates == 3


def test_identical_ignores_similarity_target_pct(tmp_path):
    cfg, project = _key_project(tmp_path)
    c = {**cfg, "similarity": {**cfg["similarity"], "target_pct": 50}}
    n = eng.Narrator(c, project, _KeyBackend(), quality="identical", tier="high")
    assert n.target_pct == 99.0 and (n.search_target, n.pass_target) == ("p50", "p25")
    assert n._sim_target("search") == 99.0 and n._sim_target("pass") == 99.0  # 没有精准声纹打分：和「完美」一样 99
    n._judge = type("J", (), {"natural_range": lambda self: {"p10": 80.0, "p25": 92.0, "p50": 100.0, "p90": 108.0}})()
    assert n._sim_target("search") == 100.0 and n._sim_target("pass") == 92.0
    synth = dict(cfg["synth"], tiers={"identical": {"search_target": "p90", "pass_target": 95}})
    n2 = eng.Narrator({**c, "synth": synth}, project, _KeyBackend(), quality="identical", tier="high")
    n2._judge = n._judge
    assert n2._sim_target("search") == 108.0 and n2._sim_target("pass") == 95.0
    assert eng.Narrator(c, project, _KeyBackend(), quality="perfect", tier="high").target_pct == 50.0  # 完美照旧


class _Judge:
    available = reliable = calibrated = True
    models = ["fake"]
    members: list = []

    def __init__(self, natural=None):
        self._natural = natural

    def judge(self, wav, sr):
        return {"pct": 100.0, "pcts": {"fake": 100.0}, "sims": {"fake": 0.8}, "sim": 0.8}

    def info(self):
        return {"models": ["fake"], "labels": ["fake"], "reliable": True, "calibration": {}, "definition": "",
                "note": ""}

    def natural_range(self):
        return self._natural


class _Checker:
    def __init__(self, *a, **k):
        pass

    def check(self, wav, sr, text, lang):
        return {"cer": 0.0, "hyp": text, "errors": 0, "units": 10, "engine": "fake", "strong": False}

    def strong(self, lang, text=""):
        return False

    def wants_paraformer(self, lang, text=""):
        return False

    def _load(self):
        return True

    def _load_paraformer(self):
        return False


def _scripted(monkeypatch, totals, pct=100.0, pct_raw=None, natural=None, tier="none"):
    """每个候选的分数按顺序给（用完后一直是最后一个）；「像你本人」固定，或者和综合分一起按 (综合分, 没封顶的百分比) 给。
    没有 N 卡：每批 1 个、至少 6 个、最多 12 个。「一模一样」的两步打分（快速 / 完整）也按同一个顺序给：
    每个版本快速打分时取下一个分数，完整打分时用同一个。"""
    import dataclasses

    from voicetwin.eval import identical_judge as IJ
    from voicetwin.eval import metrics

    monkeypatch.setattr(eng, "_vram_tier", lambda: tier)
    monkeypatch.setattr(eng, "CERChecker", _Checker)
    monkeypatch.setattr(eng.SimilarityJudge, "for_project", classmethod(lambda cls, cfg, project, **k: _Judge(natural)))
    state = {"i": 0}

    def score(self, wav, sr, text, lang, speed=1.0, use_asr=True, check_pauses=True):
        t = totals[min(state["i"], len(totals) - 1)]
        state["i"] += 1
        p, raw = pct, pct_raw
        if isinstance(t, tuple):  # (综合分, 没封顶的「像你本人」)：每个候选的分数不一样
            t, raw = t
            p = min(float(raw), 100.0)
        return metrics.Score(total=float(t), pct=p, pct_raw=raw, cer=0.0, errors=0, rate=4.0, speaker_sim=0.8)

    held = {}

    def quick(self, wav, sr, text, lang, mult=1.0):
        s = score(self, wav, sr, text, lang)
        held[id(wav)] = s
        return IJ.QuickScore(total=s.total, pct_raw=s.pct_raw, voiced=1.0, expected=None, dur_dev=None, gate_ok=True)

    def full(self, wav, sr, text, lang, mult=1.0, prepared=None, use_asr=True, cer=None, check_pauses=True):
        s = held.get(id(wav)) or score(self, wav, sr, text, lang)
        return dataclasses.replace(s, stage="full", issues=list(s.issues))

    monkeypatch.setattr(metrics.Scorer, "score", score)
    monkeypatch.setattr(metrics.Scorer, "in_normal_range", lambda self, s, lang, speed=1.0: True)
    monkeypatch.setattr(IJ.IdenticalScorer, "quick", quick)
    monkeypatch.setattr(IJ.IdenticalScorer, "full", full)
    return state


def _narrate(prepared, tmp_path, name, **kw):
    cfg, project, _ = prepared
    rec = []
    res = wf.run_narrate(cfg, project.voice, _uniq(name), out=str(tmp_path / f"{uuid.uuid4().hex[:6]}.wav"),
                         variants=False, progress=lambda f, m: rec.append((f, m)), **kw)
    return res, rec


def test_identical_stops_at_minimum_when_nothing_gets_better(prepared, tmp_path, monkeypatch):
    _scripted(monkeypatch, [1.0])
    res, rec = _narrate(prepared, tmp_path, "一模一样至少试满")  # 不写质量 = 一模一样
    seg = res.segments[0]
    assert res.quality == "identical" and seg["tries"] == 6 and seg["met"] is True and not seg["flagged"]
    assert any("达到了「一模一样」的严格标准" in n for n in res.notes)
    assert any("平均每句试了 6.0 个版本（最多 12 个）" in n for n in res.notes)
    # 没有 N 卡：第 1 轮 3 种组合各 1 个，挑出来的那个已经达标，接着试是为了确认没有更好的
    assert any("已经达到标准，再多试几个，确认没有更好的（第 4 个）" in m for _, m in rec)
    assert any("[1/1] 已试 3 个版本，目前最像你的 100.0%" in m for _, m in rec)
    gen = [f for f, m in rec if m.startswith("[1/1]")]
    assert gen and all(0.08 <= f <= 0.88 for f in gen)  # 和阶段表「逐句生成」对齐
    assert any(abs(f - 0.99) < 1e-9 and "写字幕和报告" in m for f, m in rec) and rec[-1][0] == 1.0


def test_identical_keeps_trying_while_it_still_improves(prepared, tmp_path, monkeypatch):
    _scripted(monkeypatch, [1.0 + 0.05 * i for i in range(30)])
    res, _ = _narrate(prepared, tmp_path, "一模一样一直在变好", quality="identical")
    assert res.segments[0]["tries"] == 12 and res.segments[0]["met"] is True  # 试满（没有 N 卡最多 12 个）


def test_identical_plateau_window_is_eight(prepared, tmp_path, monkeypatch):
    # 前 3 个越来越好，之后都一样：最高分在第 3 个之后不变，第 3 个往后再试 8 个（共 11 个）才算「再试也不更好」
    _scripted(monkeypatch, [1.0, 1.1, 1.2])
    res, _ = _narrate(prepared, tmp_path, "一模一样不再变好", quality="identical")
    assert res.segments[0]["tries"] == 11


def test_identical_not_similar_enough_tries_to_cap(prepared, tmp_path, monkeypatch):
    _scripted(monkeypatch, [1.0], pct=95.0)  # 没有你自己录音的范围：和「完美」一样要 99%
    res, rec = _narrate(prepared, tmp_path, "一模一样不够像", quality="identical")
    seg = res.segments[0]
    assert seg["tries"] == 12 and seg["met"] is False and "可能不够像" in seg["hint"] and seg["flagged"]
    assert any("已试 12 个版本，目前最像你的 95.0%" in m for _, m in rec)
    assert not any("已经达到标准" in m for _, m in rec)


def test_identical_targets_follow_her_natural_range(prepared, tmp_path, monkeypatch):
    natural = {"p10": 80.0, "p25": 90.0, "p50": 100.0, "p90": 110.0}
    # 95%：还没到继续找的目标（你自己录音的中位水平 100%），一直试到最多；但不低于下四分位 90%，算达标
    _scripted(monkeypatch, [1.0], pct=95.0, pct_raw=95.0, natural=natural)
    res, _ = _narrate(prepared, tmp_path, "一模一样按你自己的范围", quality="identical")
    assert res.segments[0]["tries"] == 12 and res.segments[0]["met"] is True and not res.segments[0]["flagged"]
    # 101%（没封顶的值）：到了目标，至少试满 6 个、再试也不更好就停
    _scripted(monkeypatch, [1.0], pct=100.0, pct_raw=101.0, natural=natural)
    res2, _ = _narrate(prepared, tmp_path, "一模一样达到中位水平", quality="identical")
    assert res2.segments[0]["tries"] == 6 and res2.segments[0]["met"] is True
    # similarity.target_pct 写多少都不管用，只认 synth.tiers.identical
    cfg, project, _ = prepared
    c2 = make_cfg(project.root.parent, similarity={"target_pct": 50},
                  synth={"tiers": {"identical": {"search_target": 96, "pass_target": 96}}})
    _scripted(monkeypatch, [1.0], pct=95.0, pct_raw=95.0, natural=natural)
    res3 = wf.run_narrate(c2, project.voice, _uniq("一模一样自己写的目标"), out=str(tmp_path / "t3.wav"), variants=False)
    assert res3.segments[0]["tries"] == 12 and res3.segments[0]["met"] is False


def test_identical_two_versions_and_absolute_silence(prepared, tmp_path, monkeypatch):
    """「一模一样」默认出两个版本，句子之间、开头结尾都是绝对的数字静音（全是 0）；进度和阶段表对齐。"""
    import types

    nr = types.ModuleType("noisereduce")
    nr.reduce_noise = lambda y, sr, y_noise=None, stationary=False, prop_decrease=1.0, **kw: \
        (np.asarray(y, dtype=np.float32) * 0.97).astype(np.float32)
    monkeypatch.setitem(sys.modules, "noisereduce", nr)
    _scripted(monkeypatch, [1.0])
    cfg, project, _ = prepared
    rec = []
    script = _uniq("一模一样第一句，有逗号停顿") + "\n\n" + _uniq("一模一样第二句")
    res = wf.run_narrate(cfg, project.voice, script, out=str(tmp_path / "课.wav"),
                         progress=lambda f, m: rec.append((f, m)))
    assert res.quality == "identical" and [v["name"] for v in res.variants] == ["未去杂音", "去杂音"]
    from voicetwin.utils.audio import load_audio

    for v in res.variants:
        wav, sr = load_audio(v["path"])
        m = int(0.002 * sr)
        segs = res.segments
        assert np.all(wav[: int(round(segs[0]["start"] * sr)) - m] == 0.0)
        for a, b in zip(segs, segs[1:]):
            lo, hi = int(round(a["end"] * sr)) + m, int(round(b["start"] * sr)) - m
            assert hi > lo and np.all(wav[lo:hi] == 0.0)
        assert np.all(wav[int(round(segs[-1]["end"] * sr)) + m:] == 0.0) and np.any(wav != 0.0)
    fr = [f for f, _ in rec]
    assert fr == sorted(fr)
    assert any(abs(f - 0.92) < 1e-9 and "去杂音" in m for f, m in rec)
    report = json.loads(res.report_path.read_text(encoding="utf-8"))
    assert report["quality"] == "identical" and report["quality_label"] == eng.QUALITY_LABELS["identical"]


# ============================================================================ 检查意见的回归测试（第 1、2 步）
def test_config_candidates_does_not_cap_identical(prepared, tmp_path, monkeypatch):
    """config.yaml 里手改过的 synth.candidates（以前给「均衡」「完美」用的）不能悄悄把「一模一样」限制成每句只试几个：
    只有命令行明确写的 -n 才改「一模一样」每句最多试几个；网页的「生成」不传 -n。"""
    cfg, project = _key_project(tmp_path)
    c3 = {**cfg, "synth": dict(cfg["synth"], candidates=3)}
    n = eng.Narrator(c3, project, _KeyBackend(), quality="identical", tier="high")
    assert (n.n_candidates, n.min_candidates, n.max_candidates) == (12, 40, 64)
    assert any("candidates: 3" in x and "不管「一模一样」" in x and "每句至少试 40 个、最多 64 个" in x for x in n.notes)
    p = eng.Narrator(c3, project, _KeyBackend(), quality="perfect", tier="high")  # 其它档位照旧：完美是每批几个
    assert (p.n_candidates, p.max_candidates) == (3, 20) and p.notes == []
    n3 = eng.Narrator(c3, project, _KeyBackend(), quality="identical", tier="high", candidates=3)  # 命令行 -n 3
    assert (n3.n_candidates, n3.min_candidates, n3.max_candidates) == (3, 3, 3)
    assert not any("candidates" in x for x in n3.notes)
    assert eng.Narrator(cfg, project, _KeyBackend(), quality="identical", tier="high").notes == []  # auto：不提
    # 和网页的「生成」一样整篇走一遍（不传 candidates；没有 N 卡：至少 6 个）
    _scripted(monkeypatch, [1.0])
    _, proj, _ = prepared
    c_ws = make_cfg(proj.root.parent, synth={"candidates": 3})
    res = wf.run_narrate(c_ws, proj.voice, _uniq("一模一样不受旧的候选数限制"), out=str(tmp_path / "c3.wav"),
                         variants=False, quality="identical")
    assert res.segments[0]["tries"] == 6 and any("不管「一模一样」" in x for x in res.notes)


def test_partial_per_gpu_dict_keeps_the_other_gpus(tmp_path):
    """synth.tiers.identical 里按显卡分档的值只写了一种显卡：其它显卡用自带的值（不是兜底的 12 / 1），
    也不会拿 mid 的值顶替别的显卡。写错的值（不是数）同样用这种显卡自带的值。"""
    cfg, project = _key_project(tmp_path)
    tiers = {"identical": {"max_candidates": {"high": 100}, "batch": {"high": 16}, "min_candidates": {"none": "auto"}}}
    c = {**cfg, "synth": dict(cfg["synth"], tiers=tiers)}
    want = {"high": (16, 40, 100), "mid": (8, 40, 64), "low": (2, 16, 32), "none": (1, 6, 12)}
    for tier, w in want.items():
        n = eng.Narrator(c, project, _KeyBackend(), quality="identical", tier=tier)
        assert (n.n_candidates, n.min_candidates, n.max_candidates) == w, tier
    bad = {"identical": {"max_candidates": {"low": "很多"}, "batch": "abc", "min_candidates": {"low": -3}}}
    n = eng.Narrator({**cfg, "synth": dict(cfg["synth"], tiers=bad)}, project, _KeyBackend(), quality="identical",
                     tier="low")
    assert (n.n_candidates, n.min_candidates, n.max_candidates) == (2, 16, 32)
    # 同样的道理：「完美」的错字门槛只写了一半，另一半用档位自带的（不是代码里的兜底值）
    half = {"perfect": {"cer_target": {"strong": 0.02}}}
    p = eng.Narrator({**cfg, "synth": dict(cfg["synth"], tiers=half)}, project, _KeyBackend(), quality="perfect",
                     tier="high")
    assert p.preset["cer_target"] == {"strong": 0.02, "weak": 0.08}
    assert eng.QUALITY_PRESETS["perfect"]["cer_target"] == {"strong": 0.05, "weak": 0.08}  # 自带的值没被改掉


def _feature_flags():
    """说明里的说法 → 那个功能在代码里有没有了。后面几步做完以后（见设计方案 §2 P4～P8），对应的说法才可以写回去。"""
    import importlib.util

    from voicetwin.backends.base import Backend
    from voicetwin.backends.gptsovits import _new_batch_stats
    from voicetwin.eval.metrics import CERChecker
    from voicetwin.synth import select

    search = importlib.util.find_spec("voicetwin.synth.search") is not None  # 第 5 步：真正的搜索
    batch = hasattr(Backend, "synthesize_many") and search  # 第 4 步能同时生成好几个，第 5 步的搜索真的用上它
    return {
        "batch": batch,
        "oom_halve": batch and "oom_backoffs" in _new_batch_stats(),  # 第 4 步：同时生成时显存不够就减半
        # 同时生成的个数减到 1、让出识别模型的显存也不够时，生成还是会停下（显存不够是「重试也没用」的错误）
        "oom_never_stop": not eng._is_fatal(RuntimeError("CUDA out of memory. Tried to allocate 20.00 MiB")),
        "gpu_full": False,  # 「用满显卡」「显卡一直满负荷」：没有实测就永远不能写（设计方案 §0.3）
        "multi_ref": search,                                                           # 第 5 步：每句几条参考
        "mixed_cer": hasattr(CERChecker, "check_mixed"),                               # 第 5 步：中英文分开查错字
        "continuity": hasattr(eng.Narrator, "_continuity"),                            # 第 6 步：整篇再挑一遍
        "prepare": hasattr(select, "prepare_identical"),                               # 第 8 步：新模型先准备
    }


#: 每个功能对应的说法：功能没做好之前，给老师看的字里不能有
UNBUILT_PHRASES = {
    "batch": ("同时生成", "一次生成好几个"),
    "oom_halve": ("显存不够自动减半", "减少同时生成的个数", "少生成一些再接着试"),
    "oom_never_stop": ("不会因为显存不够而停下",),
    "gpu_full": ("用满显卡", "显卡一直满负荷"),
    "multi_ref": ("换几条", "几条最合适", "每句用几条参考录音："),
    "mixed_cer": ("中英文分开",),
    "continuity": ("整篇再挑一遍", "整篇按你的停顿和音量", "按你本人的停顿长短和音量拼接"),
    "prepare": ("先做一次准备",),
}


def test_texts_only_describe_what_the_code_does(tmp_path):
    """「一模一样」的说明只写现在真的会做的事（老师的规定：不要乱写）：同时生成的个数减到 1 个也显存不够时还是会停下
    （显存不够是「重试也没用」的错误），「用满显卡」没有实测，整篇再挑一遍、新模型先准备还没做……这些说法不能先写上。"""
    from voicetwin.webui import app as A

    flags = _feature_flags()
    assert eng._is_fatal(RuntimeError("torch.OutOfMemoryError: CUDA out of memory")) or flags["oom_never_stop"]
    cfg, project = _key_project(tmp_path)
    texts = [eng.QUALITY_LABELS["identical"], eng.QUALITY_HELP["identical"], eng.QUALITY_NOTE, A.BLIND_QUALITY_NOTE]
    texts += list(eng.QUALITY_TIER_NOTES.values())
    texts += [eng.recommended_quality(t, size="显存 6 GB")[1] for t in ("high", "mid", "low", "none")]
    texts += [name for _, name in wf.STAGES_NARRATE_IDENTICAL]
    for tier in ("high", "mid", "low", "none"):
        texts += eng.Narrator(cfg, project, _KeyBackend(), quality="identical", tier=tier).notes
    yaml_text = (Path(eng.__file__).resolve().parents[1] / "default_config.yaml").read_text(encoding="utf-8")
    texts.append(yaml_text.split("\nsynth:", 1)[1].split("\n  score:", 1)[0])  # 设置文件里「合成」这一段的说明
    for key, phrases in UNBUILT_PHRASES.items():
        if flags[key]:
            continue
        for t in texts:
            for ph in phrases:
                assert ph not in t, (key, ph, t)
    # 单选框上的字每台电脑都一样：没有 N 卡时每句最多 12 个，不能写「几十个」（同一页下面的说明写着 12 个）
    assert "几十" not in eng.QUALITY_LABELS["identical"]


def test_identical_stop_rule_looks_at_the_best_version(prepared, tmp_path, monkeypatch):
    """停下的条件看的是「挑出来的那个」有没有达到继续找的目标（设计方案 §1.7 (i)），不是随便哪个版本到过：
    第 1 个版本 101% 但综合分低，之后的综合分都更高、只有 95%（低于你自己录音的中位水平 100%）——要试满。"""
    natural = {"p10": 80.0, "p25": 90.0, "p50": 100.0, "p90": 110.0}
    _scripted(monkeypatch, [(1.0, 101.0), (2.0, 95.0)], natural=natural)
    res, rec = _narrate(prepared, tmp_path, "一模一样看挑出来的那个", quality="identical")
    seg = res.segments[0]
    assert seg["tries"] == 12 and seg["pct"] == 95.0 and seg["met"] is True  # 95% 不低于下四分位 90%：算达标
    # 挑出来的一直是 95% 的那个（综合分高）：一次都不能说「已经达到标准」
    assert not any("已经达到标准" in m for _, m in rec)
    # 挑出来的那个到了目标：照样至少试满 6 个、再试也不更好就停
    _scripted(monkeypatch, [(1.0, 95.0), (2.0, 101.0)], natural=natural)
    res2, _ = _narrate(prepared, tmp_path, "一模一样挑出来的到了目标", quality="identical")
    assert res2.segments[0]["tries"] == 10 and res2.segments[0]["met"] is True


def test_page_note_cap_follows_config(tmp_path, monkeypatch):
    """打开网页时说明里的「每句最多试几个」和真正生成时一样：config.yaml 改了 synth.tiers.identical.max_candidates
    就跟着变；synth.candidates 不管「一模一样」，说明里也不跟它变。"""
    from voicetwin.webui import app as A

    cfg = make_cfg(tmp_path / "ws", synth={"candidates": 3, "tiers": {"identical": {
        "max_candidates": {"high": 30, "mid": 30, "low": 10, "none": 4}}}})
    project = Project(cfg, "说明")
    project.root.mkdir(parents=True, exist_ok=True)
    project.references_path.write_text(json.dumps(_REFS, ensure_ascii=False), encoding="utf-8")
    for tier in ("low", "none"):
        cap = eng.Narrator(cfg, project, _KeyBackend(), tier=tier).max_candidates
        assert cap == {"low": 10, "none": 4}[tier]
        assert f"每句最多试 {cap} 个版本" in eng.recommended_quality(tier, cfg=cfg)[1]
        assert f"每句最多试 {cap} 个版本" in wf.recommended_quality(tier, cfg=cfg)[1]
    assert "每句最多试 32 个版本" in eng.recommended_quality("low")[1]  # 不传设置：自带的值
    ui = A.WebUI(cfg)
    monkeypatch.setattr(A, "_gpu_status", lambda refresh=False: {"ok": True, "level": "warn", "total_gb": 5.8})
    _, radio, md = ui.on_load_gpu()
    assert radio["value"] == "identical" and "每句最多试 10 个版本" in md and "32 个" not in md


@pytest.mark.parametrize("value", ["identical", "一模一样", "一模一样（默认）"])
def test_cli_no_note_when_config_already_says_identical(tmp_path, monkeypatch, capsys, value):
    """config.yaml 里写的就是「一模一样」：不用提醒（以前会说「想用默认的「一模一样」，把那一行改成 auto」，自相矛盾）。"""
    from voicetwin import cli

    seen = _run_cli_say(tmp_path, monkeypatch, f"synth:\n  quality: {value}\n")
    assert seen["quality"] is None and "config.yaml" not in capsys.readouterr().out
    cfg = load_config(str(tmp_path / "config.yaml"))
    assert cli._config_quality_notes(cfg) == []
    _run_cli_say(tmp_path, monkeypatch, "synth:\n  quality: perfect\n")  # 别的档位照样提醒
    assert "这次按它生成" in capsys.readouterr().out


#: 只有一条参考音频的两个声音（和 research/一模一样/scripts/golden_cache_keys.py 的 REF_SETS 一样）
_REF_SETS = {
    "mixed": [{"id": "r_en_mix", "path": "references/f.wav", "lang": "en", "kind": "statement",
               "text": "比如 This is a very long English example sentence used to show it."}],
    "plain": [{"id": "r_en_plain", "path": "references/g.wav", "lang": "en", "kind": "statement",
               "text": "Next, let's look at a slightly more complex example."}],
}
_REF_SEGS = [("We can add a condition at the end of the expression.", "en", "statement"),
             ("今天我们来学习列表推导式。", "zh", "statement")]
#: 改之前的旧代码（e02dd2f）算出来的：参考文字没有汉字的，缓存键一个字节都不能变
GOLDEN_REF_KEYS = {
    "plain/fast/high/0": "bc124b5a91e55bbc", "plain/fast/high/1": "7aad1ad01b6b2a7d",
    "plain/fast/low/0": "bc124b5a91e55bbc", "plain/fast/low/1": "7aad1ad01b6b2a7d",
    "plain/balanced/high/0": "8d1a9965ea9beaf3", "plain/balanced/high/1": "a328234fcae1d9d2",
    "plain/balanced/low/0": "8d1a9965ea9beaf3", "plain/balanced/low/1": "a328234fcae1d9d2",
    "plain/best/high/0": "baf86850b417f562", "plain/best/high/1": "c48e083c2149e171",
    "plain/best/low/0": "baf86850b417f562", "plain/best/low/1": "c48e083c2149e171",
    "plain/max/high/0": "ef77a2b4f8fe5c9e", "plain/max/high/1": "ca4e3127b1a5fe83",
    "plain/max/low/0": "f85498ef8e433c00", "plain/max/low/1": "b0a60007a54b9884",
    "plain/perfect/high/0": "c081216b6e2d6f49", "plain/perfect/high/1": "1064efdc35b68d53",
    "plain/perfect/low/0": "b05be9299da0226b", "plain/perfect/low/1": "11530eef45b872bd",
}
#: 参考音频标成 en、文字里有汉字：以前 prompt_lang 发 en（参考文字里的汉字被丢掉），现在发 zh——旧缓存不能再用
OLD_BUGGY_REF_KEYS = {
    "mixed/fast/high/0": "53aeca9d3686da4c", "mixed/fast/high/1": "3eb70c3803de3178",
    "mixed/fast/low/0": "53aeca9d3686da4c", "mixed/fast/low/1": "3eb70c3803de3178",
    "mixed/balanced/high/0": "ee86a741942f1f3e", "mixed/balanced/high/1": "1b14d320964cee34",
    "mixed/balanced/low/0": "ee86a741942f1f3e", "mixed/balanced/low/1": "1b14d320964cee34",
    "mixed/best/high/0": "2bcd4d7f18ec67d8", "mixed/best/high/1": "50573c59943fa628",
    "mixed/best/low/0": "2bcd4d7f18ec67d8", "mixed/best/low/1": "50573c59943fa628",
    "mixed/max/high/0": "e12d7628ffc4c0a6", "mixed/max/high/1": "8117cd48246c4e5c",
    "mixed/max/low/0": "0dc8463b35cfa367", "mixed/max/low/1": "bfc3d3989d96ea17",
    "mixed/perfect/high/0": "f97d6295a789f60d", "mixed/perfect/high/1": "97169c43083b638a",
    "mixed/perfect/low/0": "025882fe0f43bf65", "mixed/perfect/low/1": "d7993dc5f26ac71c",
}


def test_cache_key_changes_when_the_reference_language_sent_changes(tmp_path):
    """参考音频标成 en、文字里却有汉字：prompt_lang 现在发 zh（以前发 en），发给引擎的请求变了，缓存键也要变，
    不能再拿以前（参考文字里的汉字被丢掉时）生成的句子；参考文字没有汉字的，缓存键和改之前一个字节都不差。"""
    cfg = make_cfg(tmp_path / "ws")
    keys = {}
    for name, refs in _REF_SETS.items():
        project = Project(cfg, "参考" + name)
        project.root.mkdir(parents=True, exist_ok=True)
        project.references_path.write_text(json.dumps(refs, ensure_ascii=False), encoding="utf-8")
        for q in ("fast", "balanced", "best", "max", "perfect"):
            for tier in ("high", "low"):
                n = eng.Narrator(cfg, project, _KeyBackend(), quality=q, tier=tier)
                for i, (text, lang, kind) in enumerate(_REF_SEGS):
                    seg = ScriptSegment(text=text, display=text, lang=lang, kind=kind, index=i)
                    keys[f"{name}/{q}/{tier}/{i}"] = n._plan(seg).key
    for k, v in GOLDEN_REF_KEYS.items():
        assert keys[k] == v, k
    for k, v in OLD_BUGGY_REF_KEYS.items():
        assert keys[k] != v, k


class _LangChecker(_Checker):
    seen: list = []

    def check(self, wav, sr, text, lang):
        _LangChecker.seen.append(lang)
        return super().check(wav, sr, text, lang)


@pytest.mark.parametrize("quality", ["best", "identical"])
def test_attempt_scores_and_checks_with_the_language_sent(prepared, monkeypatch, quality):
    """被判成 en、里面有汉字的句子：按真正发给引擎的语言（zh）打分、查错字、比错字门槛（以前按 en：
    英文的语速标准、英文的识别模型）。"""
    from voicetwin.backends.base import get_backend
    from voicetwin.eval import metrics

    cfg, project, _ = prepared
    _LangChecker.seen = []
    seen = {"score": [], "thr": [], "cer_ok": []}
    monkeypatch.setattr(eng, "_vram_tier", lambda: "none")
    monkeypatch.setattr(eng, "CERChecker", _LangChecker)
    monkeypatch.setattr(eng.SimilarityJudge, "for_project", classmethod(lambda cls, cfg, project, **k: _Judge()))
    real_score, real_thr, real_cer_ok = metrics.Scorer.score, eng.Narrator._thr, eng.Narrator._cer_ok

    def score(self, wav, sr, text, lang, *a, **k):
        seen["score"].append(lang)
        return real_score(self, wav, sr, text, lang, *a, **k)

    def thr(self, key, lang, default, c=None):
        seen["thr"].append(lang)
        return real_thr(self, key, lang, default, c)

    def cer_ok(self, c, lang, thr=None):
        seen["cer_ok"].append(lang)
        return real_cer_ok(self, c, lang, thr)

    monkeypatch.setattr(metrics.Scorer, "score", score)
    monkeypatch.setattr(eng.Narrator, "_thr", thr)
    monkeypatch.setattr(eng.Narrator, "_cer_ok", cer_ok)
    from voicetwin.eval import identical_judge as IJ

    real_quick, real_full = IJ.IdenticalScorer.quick, IJ.IdenticalScorer.full

    def quick(self, wav, sr, text, lang, *a, **k):  # 「一模一样」用两步打分（快速 / 完整）
        seen["score"].append(lang)
        return real_quick(self, wav, sr, text, lang, *a, **k)

    def full(self, wav, sr, text, lang, *a, **k):
        seen["score"].append(lang)
        return real_full(self, wav, sr, text, lang, *a, **k)

    monkeypatch.setattr(IJ.IdenticalScorer, "quick", quick)
    monkeypatch.setattr(IJ.IdenticalScorer, "full", full)
    n = eng.Narrator(cfg, project, get_backend("dummy", cfg, project), quality=quality)
    seg = ScriptSegment(text=MIXED, display=MIXED, lang="en", kind="statement", index=0)
    res = n.synthesize_segment(seg, force=True)
    assert res.tries >= 5
    assert seen["score"] and set(seen["score"]) == {"zh"}           # 打分（语速标准等）
    assert _LangChecker.seen and set(_LangChecker.seen) == {"zh"}   # 查错字
    assert seen["cer_ok"] and set(seen["cer_ok"]) == {"zh"}         # 挑选时比错字门槛
    assert set(seen["thr"]) <= {"zh"}


def test_docs_name_the_current_default_and_button():
    """快速上手、README、Windows 教程、环境检查：默认是「一模一样」（不再写「完美」是默认、是最慢的），
    试听按钮叫「▶ 试听（快速，只听语速）」。"""
    root = Path(eng.__file__).resolve().parents[2]
    for name in ("快速上手.md", "README.md", "docs/Windows详细使用教程.md"):
        text = (root / name).read_text(encoding="utf-8")
        assert "试听语速**" not in text and "▶ 试听语速" not in text, name
        for line in text.splitlines():
            if "完美" in line and ("默认" in line or "最慢" in line):
                assert "一模一样" in line, (name, line)
    quick = (root / "快速上手.md").read_text(encoding="utf-8")
    assert "▶ 试听（快速，只听语速）" in quick and "默认就是「一模一样」" in quick
    rows = {r["item"]: r for r in wf.doctor(make_cfg(Path(".")))}
    label = next(k for k in rows if k.startswith("noisereduce"))
    assert "「一模一样」" in label and "「完美」" in label
