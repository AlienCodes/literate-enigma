"""「一模一样」第 7 步：中文句子里夹着的英文也参加训练（VoiceTwin 自己的 1A，设计方案 §2 P7、§5.1）。

- gsv_mixed_text：合并规则（照抄 abe9843 的 TextPreprocessor）、拼接、英文音素计数；
- gsv_scripts/get_text_mixed.py：在仿真 GPT-SoVITS 目录里用替身的 LangSegmenter / clean_text 跑（VOICETWIN_TEXT_DRYRUN=1），
  分几路、自检、出错；
- 训练时：成功就用它；出错（替身抛异常、缺模块、自检不过）自动退回官方的 1-get-text.py 并说明原因；
  换了处理文字的方法 / 录音文件改过 → 重新提取特征、旧的训练备份起来。
这些都不需要 torch，也不需要 yaml（1A / 1B / 1C 的仿真脚本只用标准库），三个环境都跑。"""

import importlib.util
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from voicetwin import workflows as wf
from voicetwin.backends import gptsovits as gsv
from voicetwin.backends.base import get_backend
from voicetwin.backends.gptsovits import GPTSoVITSBackend
from voicetwin.backends.gsv_mixed_text import ARPABET_RE, assemble, count_en_phones, is_arpabet, merge_segments

from conftest import make_cfg
from fake_gptsovits import build_fake_root

TEACHER_LINE = "翻译成英文就是There are some nuts which Lucy bought on the table."
LINES = [
    TEACHER_LINE,                       # 老师素材里常见的：中文 + 一整句英文例句
    "我们今天学第3课，",                 # 带数字（数字段和中文合在一起，按中文处理）
    "OK，好的",                          # 开头是英文
    "纯中文的一句话。",                  # 没有英文：一段，和官方的结果一样
    "Hello world, this is a test.",    # 纯英文句子（训练列表里标 en）
]


def _stub(root: Path, name: str):
    """把仿真目录里的替身模块（GPT_SoVITS/text/<name>.py）当普通模块加载进测试。"""
    spec = importlib.util.spec_from_file_location(f"stub_{name}", root / "GPT_SoVITS" / "text" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ============================================================================ 纯计算
def test_merge_rule_is_the_inference_rule(tmp_path):
    root = build_fake_root(tmp_path / "GSV")
    seg = _stub(root, "LangSegmenter").LangSegmenter
    # 老师的句子：中文、英文、最后的句号（句号不是英文，单独一段按中文处理，和生成时一样）
    assert merge_segments(seg.getTexts(TEACHER_LINE)) == [
        ("翻译成英文就是", "zh"), ("There are some nuts which Lucy bought on the table", "en"), (".", "zh")]
    # 数字段（LangSegmenter 标成别的语言）和前后的中文合成一段，按中文处理
    raw = seg.getTexts("我们今天学第3课，")
    assert [r["lang"] for r in raw] == ["zh", "digit", "zh"]
    assert merge_segments(raw) == [("我们今天学第3课，", "zh")]
    assert merge_segments(seg.getTexts("OK，好的")) == [("OK", "en"), ("，好的", "zh")]
    assert merge_segments(seg.getTexts("纯中文的一句话。")) == [("纯中文的一句话。", "zh")]
    assert merge_segments(seg.getTexts("Hello world, this is a test.")) == [("Hello world", "en"), (", ", "zh"),
                                                                           ("this is a test", "en"), (".", "zh")]
    # 连着的英文段接在一起；连着的不是英文的段接在一起、记成 zh（abe9843 TextPreprocessor 的 else 分支）
    assert merge_segments([{"lang": "en", "text": "Hello"}, {"lang": "en", "text": " world"},
                           {"lang": "ja", "text": "の"}, {"lang": "zh", "text": "书"}]) == [
        ("Hello world", "en"), ("の书", "zh")]
    # 空的段也照样参加（官方也不跳过）
    assert merge_segments([{"lang": "en", "text": "A"}, {"lang": "zh", "text": ""}, {"lang": "en", "text": "B"}]) == [
        ("A", "en"), ("", "zh"), ("B", "en")]
    assert merge_segments([]) == []


def _results(root: Path, line: str):
    seg = _stub(root, "LangSegmenter").LangSegmenter
    clean = _stub(root, "cleaner").clean_text
    out = []
    for text, lang in merge_segments(seg.getTexts(line)):
        ph, w2p, norm = clean(text, lang)
        out.append((lang, ph, w2p, norm))
    return out


def test_assemble_spans_add_up_and_english_has_no_bert(tmp_path):
    root = build_fake_root(tmp_path / "GSV")
    clean = _stub(root, "cleaner").clean_text
    for line in LINES[:4]:
        results = _results(root, line)
        phones, word2ph, norm, spans = assemble(results)
        assert sum(n for _, n in spans) == len(phones) == sum(word2ph), line
        assert [lang for lang, _ in spans] == [r[0] for r in results]
        assert "\t" not in norm and "\n" not in norm
    # 英文段的音素是英文音素（ARPAbet），算 BERT 时这一段是 0（spans 里标 en）
    phones, _w, _n, spans = assemble(_results(root, TEACHER_LINE))
    assert spans[1][0] == "en" and spans[1][1] == 20
    en_part = phones[spans[0][1]:spans[0][1] + spans[1][1]]
    assert all(is_arpabet(p) for p in en_part)
    # 没有英文的句子：一段，音素和官方整句 clean_text 的结果一模一样（以前训练用的就是这个）
    phones, word2ph, norm, spans = assemble(_results(root, "纯中文的一句话。"))
    official = clean("纯中文的一句话。", "zh")
    assert phones == official[0] and word2ph == official[1] and norm == official[2] and spans == [("zh", len(phones))]
    # 官方的方法把英文整个删掉：同一句只剩「翻译成英文就是.」的音素
    assert len(clean(TEACHER_LINE, "zh")[0]) == 15 < len(assemble(_results(root, TEACHER_LINE))[0])


def test_english_phone_count_only_counts_english_segments():
    assert ARPABET_RE.match("AH0") and ARPABET_RE.match("HH") and ARPABET_RE.match("OW1")
    assert not any(is_arpabet(p) for p in ("SP", "AP", "SP2", "SP3", "UNK", "a1", ",", "zh", "AH3", "ABC"))
    # 中文的零声母写法（AA / EE / OO）和英文音素长得一样：只数英文段里的
    results = [("zh", ["AA", "a1", "EE", "e4"], [2, 2], "啊饿"), ("en", [",", "HH", "AH0"], None, "Hi")]
    assert count_en_phones(results) == 2


# ============================================================================ 自己的 1A 脚本（仿真目录，测试模式）
def _write_list(path: Path, lines=LINES) -> Path:
    rows = []
    for i, text in enumerate(lines):
        lang = "en" if not any("一" <= c <= "鿿" for c in text) else "zh"
        rows.append(f"c{i}.wav|vt|{lang}|{text}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _run_runner(root: Path, lst: Path, opt: Path, i_part: int = 0, all_parts: int = 1, **extra):
    env = dict(os.environ, inp_text=str(lst), opt_dir=str(opt), i_part=str(i_part), all_parts=str(all_parts),
               version="v2ProPlus", is_half="True", exp_name="vt", VOICETWIN_TEXT_DRYRUN="1",
               PYTHONPATH=os.pathsep.join([str(root), str(root / "GPT_SoVITS")]), **extra)
    return subprocess.run([sys.executable, "-s", str(gsv.MIXED_SCRIPT)], cwd=str(root), env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=120)


def test_runner_dry_run_in_fake_root(tmp_path):
    root = build_fake_root(tmp_path / "GSV")
    lst = _write_list(tmp_path / "train.list")
    opt = tmp_path / "opt"
    proc = _run_runner(root, lst, opt)
    out = proc.stdout.decode("utf-8", "replace")
    assert proc.returncode == 0, out
    rows = [ln.split("\t") for ln in (opt / "2-name2text-0.txt").read_text(encoding="utf-8").strip().split("\n")]
    assert [r[0] for r in rows] == [f"c{i}.wav" for i in range(5)] and all(len(r) == 4 for r in rows)
    clean = _stub(root, "cleaner").clean_text
    for name, phones, word2ph, norm in rows:
        spans_file = opt / "3-bert" / f"{name}.json"
        if name == "c4.wav":  # 纯英文句子：和官方一样整句按英文处理，没有 BERT 文件，word2ph 是 None
            assert not spans_file.exists() and word2ph == "None"
            assert phones.split(" ") == clean(LINES[4], "en")[0]
            continue
        spans = json.loads(spans_file.read_text(encoding="utf-8"))
        assert sum(n for _, n in spans["spans"]) == spans["n_phones"] == len(phones.split(" "))
    assert json.loads((opt / "3-bert" / "c0.wav.json").read_text(encoding="utf-8"))["spans"] == [
        ["zh", 14], ["en", 20], ["zh", 1]]
    assert rows[3][1].split(" ") == clean(LINES[3], "zh")[0]   # 纯中文：和官方的一样
    # 最后打印英文音素一共几个、几句夹着英文（c0 的 20 个 + c2 的「OK」2 个；纯英文句子不算「新参加训练」）
    assert "VT_EN_PHONES 22" in out and "VT_EN_LINES 2" in out
    # 和官方一样每处理一句打印一行文件名（进度靠它）
    assert [ln for ln in out.splitlines() if ln.endswith(".wav")] == [f"c{i}.wav" for i in range(5)]


def test_runner_parts_split_the_lines(tmp_path):
    root = build_fake_root(tmp_path / "GSV")
    lst = _write_list(tmp_path / "train.list")
    opt = tmp_path / "opt"
    for i in (0, 1):
        assert _run_runner(root, lst, opt, i, 2).returncode == 0
    names = [[ln.split("\t")[0] for ln in (opt / f"2-name2text-{i}.txt").read_text(encoding="utf-8").strip().split("\n")]
             for i in (0, 1)]
    assert names == [["c0.wav", "c2.wav", "c4.wav"], ["c1.wav", "c3.wav"]]


def test_runner_self_check_and_failures(tmp_path):
    root = build_fake_root(tmp_path / "GSV")
    lst = _write_list(tmp_path / "train.list")
    # LangSegmenter 丢字（版本不一样）：没有英文的句子的音素和官方的不一样 → 退出码 3，说明原因
    proc = _run_runner(root, lst, tmp_path / "o1", FAKE_GSV_LANGSEG_DROP="1")
    out = proc.stdout.decode("utf-8", "replace")
    assert proc.returncode == 3 and "VT_FAIL 自检没通过" in out
    # 整合包里没有这些模块：退出码不是 0，说明缺什么
    bare = build_fake_root(tmp_path / "GSV-bare", text_stubs=False)
    proc = _run_runner(bare, lst, tmp_path / "o2")
    assert proc.returncode != 0 and "VT_FAIL 整合包里缺少需要的文字处理模块" in proc.stdout.decode("utf-8", "replace")
    # 每句都出错：一句也没写（调用的地方按「不到 98%」退回官方的方法）
    proc = _run_runner(root, lst, tmp_path / "o3", FAKE_GSV_CLEANER_RAISE="1")
    assert proc.returncode == 0
    assert (tmp_path / "o3" / "2-name2text-0.txt").read_text(encoding="utf-8").strip() == ""


# ============================================================================ 训练时（仿真 GPT-SoVITS）
class _Log(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


@pytest.fixture
def vt_log():
    h = _Log()
    logger = logging.getLogger("voicetwin")
    old = logger.level
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
    try:
        yield h
    finally:
        logger.removeHandler(h)
        logger.setLevel(old)


@pytest.fixture
def gsv_env(prepared, tmp_path, monkeypatch):
    """复制一份测试声音 + 仿真 GPT-SoVITS 目录；不读真显卡（12 GB），1B 不等。"""
    import shutil

    _, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    root = build_fake_root(tmp_path / "GPT-SoVITS")
    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    monkeypatch.setattr(GPTSoVITSBackend, "_gpu_memory", lambda self, quick=False: (11.99, 11.2, "test"))
    monkeypatch.setattr(GPTSoVITSBackend, "POLL_SECONDS", 0.05)
    monkeypatch.setenv("FAKE_GSV_CLIP_SLEEP", "0")

    def make(**train):
        cfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {
            "root": str(root), "python": sys.executable, "is_half": True, "train": train}})
        p = wf.open_project(cfg, project.voice, must_exist=True)
        return cfg, p, get_backend("gptsovits", cfg, p)

    return make, root


def _features(b, parts=1, **kw):
    from voicetwin.data.exporters import export_gptsovits

    exp = export_gptsovits(b.project, speaker=b.exp_name)
    res = b._prepare_features(Path(exp["list"]), Path(exp["wav_dir"]), None, n_clips=int(exp["count"]), parts=parts, **kw)
    return res, int(exp["count"])


def _rows(b):
    return [ln.split("\t") for ln in (b._opt_dir() / "2-name2text.txt").read_text(encoding="utf-8").strip().split("\n")]


def test_training_uses_the_mixed_front_end(gsv_env, monkeypatch, vt_log):
    monkeypatch.setenv("VOICETWIN_TEXT_DRYRUN", "1")
    make, root = gsv_env
    _, project, b = make()
    res, n = _features(b, parts=2)
    assert res["frontend"] == "mixed" and (b._opt_dir() / gsv.FRONTEND_FILE).read_text(encoding="utf-8") == "mixed"
    rows = _rows(b)
    assert len(rows) == n and len({r[0] for r in rows}) == n
    # 测试素材里「今天我们来学习Python里面的列表推导式。」这样的句子：Python 这次有英文音素
    mixed = [r for r in rows if any(is_arpabet(p) for p in r[1].split(" ")) and any("一" <= c <= "鿿" for c in r[3])]
    assert mixed and res["en_lines"] == len(mixed) and res["en_phones"] > 0
    assert not any("没成功" in m for m in vt_log.messages)
    assert any("处理文字：中文和英文都参加训练（以前英文部分会被丢掉）" in m for m in vt_log.messages)
    # 每路一个日志
    assert (project.logs_dir / "gsv_1a_text.log").exists() and (project.logs_dir / "gsv_1a_text_2.log").exists()


@pytest.mark.parametrize("how", ["raise", "missing", "self_check"])
def test_mixed_front_end_falls_back_to_official(gsv_env, monkeypatch, vt_log, how, tmp_path):
    monkeypatch.setenv("VOICETWIN_TEXT_DRYRUN", "1")
    make, root = gsv_env
    if how == "raise":
        monkeypatch.setenv("FAKE_GSV_LANGSEG_RAISE", "1")
    elif how == "self_check":
        monkeypatch.setenv("FAKE_GSV_LANGSEG_DROP", "1")
    else:
        for name in ("LangSegmenter.py", "cleaner.py"):
            (root / "GPT_SoVITS" / "text" / name).unlink()
    _, project, b = make()
    res, n = _features(b)
    assert res["frontend"] == "official" and (b._opt_dir() / gsv.FRONTEND_FILE).read_text(encoding="utf-8") == "official"
    rows = _rows(b)
    assert len(rows) == n and all(r[1] == "ph" for r in rows)   # 仿真的官方 1-get-text.py 写的
    assert not list((b._opt_dir()).glob("2-name2text-*.txt"))   # 没做完的结果先删掉了
    warn = [m for m in vt_log.messages if m.startswith("中英文一起训练的新方法这次没成功（原因：")]
    assert len(warn) == 1 and warn[0].endswith("已改用官方的方法（英文部分不参加训练），训练照常进行。")
    # LangSegmenter 每句都出错时，只有纯英文的句子（不用 LangSegmenter）写出来了：不到 98%
    reason = {"raise": "（不到 98%）", "missing": "整合包里缺少需要的文字处理模块", "self_check": "自检没通过"}[how]
    assert reason in warn[0]


def test_official_front_end_when_configured(gsv_env, monkeypatch, vt_log):
    monkeypatch.setenv("VOICETWIN_TEXT_DRYRUN", "1")
    make, _ = gsv_env
    _, _, b = make(text_frontend="official")
    res, _ = _features(b)
    assert res["frontend"] == "official" and not any("中英文" in m for m in vt_log.messages)


def _fake_old_models(b, project):
    """假装上次已经训练好、挑好了一个模型（模型文件 + 接着练用的进度 + models.json）。"""
    sd, gd = b.p("SoVITS_weights_v2ProPlus"), b.p("GPT_weights_v2ProPlus")
    sd.mkdir(parents=True, exist_ok=True)
    gd.mkdir(parents=True, exist_ok=True)
    sov, gpt = sd / f"{b.exp_name}_e8_s80.pth", gd / f"{b.exp_name}-e15.ckpt"
    sov.write_bytes(b"06" + b"x" * 2000)
    gpt.write_bytes(b"x" * 2000)
    (b._opt_dir() / "logs_s2_v2ProPlus").mkdir(parents=True, exist_ok=True)
    (b._opt_dir() / "logs_s2_v2ProPlus" / "G_233333333333.pth").write_text("8")
    project.update_models("gptsovits", {"sovits": [str(sov)], "gpt": [str(gpt)],
                                        "selected": {"id": "s8-g15", "sovits": str(sov), "gpt": str(gpt)},
                                        "selection": {"best": "s8-g15", "results": [{"id": "s8-g15", "pct": 97.5}]}})
    return sov, gpt


def test_changing_front_end_or_clips_rebuilds_and_archives(gsv_env, monkeypatch, vt_log):
    monkeypatch.setenv("VOICETWIN_TEXT_DRYRUN", "1")
    make, _ = gsv_env
    _, project, b = make()
    _features(b)
    opt = b._opt_dir()
    hubert_before = {f.name: f.stat().st_mtime_ns for f in (opt / "4-cnhubert").glob("*.pt")}
    sov, gpt = _fake_old_models(b, project)
    time.sleep(0.02)

    # 1) 换成官方的方法：只重新处理文字（声音特征接着用），旧的训练进度和模型备份起来
    _, _, b2 = make(text_frontend="official")
    from voicetwin.data.exporters import export_gptsovits

    exp = export_gptsovits(project, speaker=b2.exp_name)
    changed, kinds, reasons = b2._material_changes(b2._feature_digest(Path(exp["list"]), Path(exp["wav_dir"])), opt)
    assert changed and kinds == ["frontend"] and reasons == ["处理文字改用官方的方法"]
    res, _ = _features(b2, changed=True, kinds=kinds)
    assert res["frontend"] == "official" and all(r[1] == "ph" for r in _rows(b2))
    assert {f.name: f.stat().st_mtime_ns for f in (opt / "4-cnhubert").glob("*.pt")} == hubert_before
    (run1,) = list((opt / "old_runs").iterdir())
    assert (run1 / "logs_s2_v2ProPlus").is_dir() and (run1 / "SoVITS_weights_v2ProPlus" / sov.name).exists()
    assert not sov.exists() and any("处理文字的方法或训练文字变了" in m for m in vt_log.messages)
    # 原来的模型记成 previous_selected（下次挑选时也参加比较），备份不会被删
    prev = project.load_models()["gptsovits"]["previous_selected"]
    assert prev["pending"] is True and prev["id"] == "s8-g15" and prev["pct"] == 97.5
    assert prev["sovits"].startswith(str(run1)) and Path(prev["sovits"]).exists()
    # 新模型还没练出来：models.json 里的模型就是挪走的原来那个（不重复加）
    assert [c["sovits"] for c in b2.checkpoints()] == [prev["sovits"]]

    # 2) 没有再改：素材的指纹一样，不再重新做
    exp = export_gptsovits(project, speaker=b2.exp_name)
    assert b2._material_changes(b2._feature_digest(Path(exp["list"]), Path(exp["wav_dir"])), opt)[0] is False

    # 3) 录音文件改过（修改时间变了）：声音特征也要重新提取，再备份一次
    first = Path(exp["list"]).read_text(encoding="utf-8").split("|", 1)[0]   # 训练列表里的第一条
    clip = Path(exp["wav_dir"]) / first
    st = clip.stat()
    os.utime(clip, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
    _fake_old_models(b2, project)
    exp = export_gptsovits(project, speaker=b2.exp_name)
    changed, kinds, reasons = b2._material_changes(b2._feature_digest(Path(exp["list"]), Path(exp["wav_dir"])), opt)
    assert changed and kinds == ["clips"] and reasons == ["录音文件改过"]
    _features(b2, changed=True, kinds=kinds)
    assert {f.name: f.stat().st_mtime_ns for f in (opt / "4-cnhubert").glob("*.pt")} != hubert_before
    assert len(list((opt / "old_runs").iterdir())) == 2


def test_old_version_stamp_counts_as_new_front_end(gsv_env, monkeypatch):
    """以前的版本训练的（指纹只有训练列表 + 版本）：训练列表没变时只是「中英文一起训练的新方法」，只重新处理文字。"""
    monkeypatch.setenv("VOICETWIN_TEXT_DRYRUN", "1")
    make, _ = gsv_env
    _, project, b = make()
    _features(b)
    opt = b._opt_dir()
    from voicetwin.data.exporters import export_gptsovits

    exp = export_gptsovits(project, speaker=b.exp_name)
    feat = b._feature_digest(Path(exp["list"]), Path(exp["wav_dir"]))
    (opt / "voicetwin_list.sha1").write_text(feat["list_sha1"])   # 以前的写法
    (opt / gsv.FEATURES_FILE).unlink()
    changed, kinds, reasons = b._material_changes(feat, opt)
    assert changed and set(kinds) == {"legacy", "frontend"} and reasons == ["中英文一起训练的新方法"]


def test_mixed_runner_is_packaged():
    """新脚本要跟着程序一起装（pip 安装时是 package-data；Windows 发布包把整个 voicetwin 文件夹打进去）。"""
    root = Path(__file__).resolve().parents[1]
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert '"backends/gsv_scripts/*.py"' in text
    assert gsv.MIXED_SCRIPT.exists() and gsv.MIXED_SCRIPT.parent.parent.name == "backends"
    assert (gsv.MIXED_SCRIPT.parent.parent / "gsv_mixed_text.py").exists()
    build = (root / "scripts" / "build_windows_release.py").read_text(encoding="utf-8")
    assert '"voicetwin"' in build.split("INCLUDE = ", 1)[1].split("\n", 1)[0]
