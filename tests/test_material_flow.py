"""核查（老师 10-02 的要求）：训练、挑选模型、生成用的一定是**校对表里改好、保存过的文字**；
**删除的句子（音频和文字）一律不用**；还有没保存的修改时不开始训练；训练以后又改了，程序会提醒重新训练。

流程和老师在网页上做的一样：改字 → 保存修改 → 删除几行 → 确认训练素材 → 开始训练（训练完自动挑选模型）→ 生成。
推理服务用真实的 api_v2.py（tests/gsv_real/），能看到 GPT-SoVITS 实际收到的每一个请求。
"""

import json
import shutil
import socket
import sys
from pathlib import Path

import pytest

from voicetwin import workflows as wf
from voicetwin.backends.base import get_backend
from voicetwin.backends.gptsovits import GPTSoVITSBackend
from voicetwin.data import review

from conftest import make_cfg
from fake_gptsovits import build_fake_root

pytest.importorskip("fastapi")
pytest.importorskip("uvicorn")

FIXED_A = "这是老师改好的第一句话，用来训练。"
FIXED_U = "这一句是确认训练素材时一起保存的。"


def _port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _calls(root: Path):
    f = root / "_real_api_calls.jsonl"
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()] if f.exists() else []


@pytest.fixture
def env(prepared, tmp_path, monkeypatch):
    import os
    import sysconfig

    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    monkeypatch.setattr(GPTSoVITSBackend, "_gpu_memory", lambda self, quick=False: (11.99, 11.2, "test"))
    monkeypatch.setattr(GPTSoVITSBackend, "POLL_SECONDS", 0.05)
    monkeypatch.setattr(GPTSoVITSBackend, "STARTUP_NOTE_SECONDS", 0.4)
    monkeypatch.setenv("FAKE_GSV_CLIP_SLEEP", "0.0")
    paths = [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"], os.environ.get("PYTHONPATH", "")]
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(p for p in dict.fromkeys(paths) if p))
    cfg, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    # 共用的测试声音可能被别的测试训练过：清掉旧的训练列表，才能检查「没开始训练」
    shutil.rmtree(ws / project.voice / "exports", ignore_errors=True)
    root = build_fake_root(tmp_path / "GPT-SoVITS", real_api=True)
    gcfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": _port(), "startup_timeout": 60, "is_half": True,
        "train": {"sovits_epochs": 2, "gpt_epochs": 2, "batch_size": 2}}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    review.save_confirmed(p2, p2.load_manifest())  # 从「已确认」开始（共用的测试声音可能被别的测试改过）
    return gcfg, p2, root


def test_only_saved_corrected_text_is_used_and_deleted_clips_never(env):
    cfg, project, root = env
    voice = project.voice
    records = project.load_manifest()
    refs = project.load_references()
    ref_ids = {r["id"] for r in refs}
    kept_train = [r for r in records if r.get("keep") and r.get("split", "train") == "train" and r.get("text")]
    val = [r for r in records if r.get("keep") and r.get("split") == "val" and r.get("text")]
    assert kept_train and val and refs

    a = next(r for r in kept_train if r["id"] not in ref_ids)          # 改字、保存
    d_ref = refs[0]["id"]                                              # 删除一条现在是参考音频的
    d_val = val[0]["id"]                                               # 删除一条「考试题」
    u = next(r for r in kept_train if r["id"] not in ref_ids | {a["id"]})  # 改了但先不保存
    old_a = a["text"]

    # 1. 改字 → 保存修改
    review.set_draft(project, a["id"], text=FIXED_A)
    wf.review_save(cfg, voice, ids=[a["id"]])
    # 2. 删除两行
    wf.review_delete(cfg, voice, d_ref)
    wf.review_delete(cfg, voice, d_val)
    # 3. 又改了一句但没保存：不能开始训练（否则会用旧文字）
    review.set_draft(project, u["id"], text=FIXED_U)
    with pytest.raises(RuntimeError) as ei:
        wf.run_train(cfg, voice, "gptsovits", select=True)
    from voicetwin.errors import explain

    f = explain(ei.value)
    assert f.key == "unsaved_edits" and "保存修改" in f.advice
    assert not (project.exports_dir / "gptsovits" / "train.list").exists()  # 根本没开始
    # 4. 确认训练素材（会先把没保存的一起保存）
    out = wf.review_confirm(cfg, voice)
    assert out["confirmed"] and u["id"] in out["saved"]
    assert review.unsaved_count(project) == 0

    # 5. 开始训练（训练完自动挑选模型）
    info = wf.run_train(cfg, voice, "gptsovits", select=True, sovits_save_every=2, gpt_save_every=2)
    assert "selection_error" not in info, info.get("selection_error_detail")

    manifest = {r["id"]: r for r in project.load_manifest()}
    wav_of = {rid: Path(project.abspath(r["path"])).name for rid, r in manifest.items()}
    # 5a. 交给 GPT-SoVITS 的训练列表：改好的字；删除的两条、考试题都不在
    lines = (project.exports_dir / "gptsovits" / "train.list").read_text(encoding="utf-8").splitlines()
    by_wav = {ln.split("|")[0]: ln.split("|")[3] for ln in lines}
    runs = [c["req"] for c in _calls(root) if c["kind"] == "run"]
    for rid, fixed in ((a["id"], FIXED_A), (u["id"], FIXED_U)):
        assert manifest[rid]["text"] == fixed
        if manifest[rid].get("split") == "val":
            # 删除了一条「考试题」以后，程序会补一条新的考试题（不训练，用来挑最像的模型）——
            # 补到的是改过的这句时，挑模型时读的也是改好的字
            assert any(req["text"].startswith(fixed.rstrip("。")) for req in runs), fixed
            assert wav_of[rid] not in by_wav
        else:
            assert by_wav[wav_of[rid]] == fixed
    # 改过的那条在列表里没有旧文字（测试素材里同一句话会在别的片段里重复出现，所以按文件名查）
    assert all(not (ln.startswith(wav_of[a["id"]] + "|") and ln.endswith("|" + old_a)) for ln in lines)
    assert wav_of[d_ref] not in by_wav and wav_of[d_val] not in by_wav
    expected = {wav_of[rid] for rid, r in manifest.items()
                if r.get("keep") and not r.get("deleted") and r.get("text") and r.get("split", "train") == "train"}
    assert set(by_wav) == expected
    # 5b. GPT-SoVITS 自己处理文字那一步（1-get-text.py）看到的也是改好的字
    backend = get_backend("gptsovits", cfg, project)
    name2text = (root / "logs" / backend.exp_name / "2-name2text.txt").read_text(encoding="utf-8")
    seen = {ln.split("\t")[0]: ln.split("\t")[-1] for ln in name2text.splitlines() if ln.strip()}
    for rid, fixed in ((a["id"], FIXED_A), (u["id"], FIXED_U)):
        if manifest[rid].get("split") != "val":
            assert seen[wav_of[rid]] == fixed
    assert wav_of[d_ref] not in seen and wav_of[d_val] not in seen
    # 5c. 参考音频：没有删除的；配的文字和校对表里保存的一样
    refs2 = project.load_references()
    assert refs2 and d_ref not in {r["id"] for r in refs2}
    for r in refs2:
        assert r["text"] == manifest[r["id"]]["text"], r["id"]
    # 5d. 挑选模型时 GPT-SoVITS 实际收到的请求：不用删除的音频当参考、不读删除的那句考试题、参考文字是改好的
    assert runs
    # 参考音频是从片段剪出来的副本（references/<片段 id>.wav）：按文件名对回片段
    def clip_of(path: str) -> str:
        return Path(path).stem

    for req in runs:
        rid = clip_of(req["ref_audio_path"])
        assert rid in {r["id"] for r in refs2} and rid not in (d_ref, d_val)
        assert not {clip_of(x) for x in req.get("aux_ref_audio_paths") or []} & {d_ref, d_val}
        assert req["prompt_text"] == manifest[rid]["text"]
        assert req["text"] != manifest[d_val]["text"]
    # 5e. 刚训练完：不需要提醒
    assert backend.trained_material_note() == ""
    assert wf.material_changed_note(cfg, voice, "gptsovits") == ""

    # 6. 训练以后又改了字：提醒重新训练（不会悄悄用旧模型当成新文字）
    other = next(r for r in manifest.values() if r.get("keep") and r.get("split", "train") == "train"
                 and r["id"] not in {a["id"], u["id"]})
    review.set_draft(project, other["id"], text="训练以后又改过的一句话。")
    wf.review_save(cfg, voice, ids=[other["id"]])
    note = get_backend("gptsovits", cfg, project).trained_material_note()
    assert "上次训练以后改过" in note and "开始训练" in note
    # 7. 撤销删除也算改过（之前删除的那句又会用来训练）
    wf.review_restore(cfg, voice, d_val)
    assert get_backend("gptsovits", cfg, project).trained_material_note()


def test_deleted_clip_is_never_kept_even_if_marked_keep(env):
    """保险：就算记录里 keep 被别的地方改成了 True，删除的也不算（load_manifest(only_kept=True)）。"""
    cfg, project, root = env
    records = project.load_manifest()
    rid = next(r["id"] for r in records if r.get("keep"))
    wf.review_delete(cfg, project.voice, rid)
    records = project.load_manifest()
    for r in records:
        if r["id"] == rid:
            r["keep"] = True  # 假设出了意外
    project.save_manifest(records)
    assert rid not in {r["id"] for r in project.load_manifest(only_kept=True)}
    from voicetwin.data.exporters import train_records, validation_items

    assert rid not in {r["id"] for r in train_records(project, include_val=True)}
    assert rid not in {r["id"] for r in validation_items(project)}


def test_cache_is_not_reused_after_reference_text_changes(prepared, tmp_path):
    """生成的句子有缓存：参考音频的文字改了以后，缓存的键要变（不能用改之前生成的声音）。"""
    from voicetwin.synth.engine import Narrator
    from voicetwin.synth.script import parse_script

    cfg, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    c2 = make_cfg(ws)
    p2 = wf.open_project(c2, project.voice, must_exist=True)
    backend = get_backend("dummy", c2, p2)
    seg = parse_script("大家好，今天我们讲第一课。")[0]
    n1 = Narrator(c2, p2, backend, quality="fast")
    plan1 = n1._plan(seg)
    refs = p2.load_references()
    for r in refs:
        if r["id"] == plan1.ref["id"]:
            r["text"] = r["text"] + "（改过）"
    p2.write_json(p2.root / "references.json", refs)
    plan2 = Narrator(c2, p2, backend, quality="fast")._plan(seg)
    assert plan2.ref["id"] == plan1.ref["id"] and plan2.key != plan1.key


class _FlakyChecker:
    """识别校验：前两次正常，第三次出错（比如识别模型显存不够）。"""
    calls = 0

    def __init__(self, *a, **k):
        pass

    def wants_paraformer(self, lang, text):
        return False

    def _load(self):
        return True

    def _load_paraformer(self):
        return True

    def check(self, wav, sr, text, lang):
        type(self).calls += 1
        if type(self).calls >= 3:
            raise RuntimeError("CUDA out of memory. Tried to allocate 512.00 MiB")
        return {"cer": 0.2}


def test_asr_error_during_selection_does_not_stop_it(prepared, tmp_path, monkeypatch):
    """自动挑选时识别校验出错：关掉识别校验接着挑（所有模型都不算错字率），不能整个停下。"""
    import voicetwin.synth.select as sel

    cfg, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    c2 = make_cfg(ws)
    _FlakyChecker.calls = 0
    monkeypatch.setattr(sel, "CERChecker", _FlakyChecker)
    out = wf.run_select(c2, project.voice, "dummy", use_asr=True)
    assert out["selection"]["results"] and all(r["cer"] is None for r in out["selection"]["results"])
    assert _FlakyChecker.calls >= 3


def test_asr_error_during_generation_does_not_stop_it(prepared, tmp_path, monkeypatch):
    """生成时识别校验出错：后面只按声纹、语速和停顿挑，整篇照样做完。"""
    from voicetwin.eval import metrics

    cfg, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    c2 = make_cfg(ws)
    orig = metrics.Scorer.score
    calls = {"asr": 0}

    def flaky(self, *a, **k):
        if k.get("use_asr"):
            calls["asr"] += 1
            raise RuntimeError("CUDA out of memory. Tried to allocate 512.00 MiB")
        return orig(self, *a, **k)

    monkeypatch.setattr(metrics.Scorer, "score", flaky)
    res = wf.run_narrate(c2, project.voice, "大家好。今天我们讲第一课。", out=str(tmp_path / "a.wav"),
                         backend_name="dummy", quality="fast", asr_check=True)
    assert res.audio_path.exists() and calls["asr"] == 1  # 只出错一次，后面就不再用识别校验


def test_training_requires_confirmed_material(env):
    """老师的要求：必须先点「✅ 确认训练素材」才能训练；确认以后又改过（删除、改字）也要再确认一次。"""
    from voicetwin.errors import explain
    from voicetwin.webui import tasks

    cfg, project, root = env
    voice = project.voice
    review.confirm_path(project).unlink()  # 还没确认过
    with pytest.raises(RuntimeError) as ei:
        wf.run_train(cfg, voice, "gptsovits", select=False)
    f = explain(ei.value)
    assert f.key == "not_confirmed" and "确认训练素材" in f.advice and f.key in tasks.NO_REPORT_KEYS
    assert wf.training_blocker_for(cfg, voice).startswith("还没有确认训练素材")
    assert not (project.exports_dir / "gptsovits" / "train.list").exists()

    wf.review_confirm(cfg, voice)
    assert wf.training_blocker_for(cfg, voice) == ""
    rid = next(r["id"] for r in project.load_manifest() if r.get("keep"))
    wf.review_delete(cfg, voice, rid)  # 确认以后又删了一行
    with pytest.raises(RuntimeError) as ei:
        wf.run_train(cfg, voice, "gptsovits", select=False)
    assert explain(ei.value).key == "confirm_stale"

    wf.review_restore(cfg, voice, rid)  # 撤销删除：和确认时一样了，又可以训练
    assert wf.training_blocker_for(cfg, voice) == ""
    wf.review_delete(cfg, voice, rid)
    wf.review_confirm(cfg, voice)  # 再确认一次
    info = wf.run_train(cfg, voice, "gptsovits", select=False, sovits_save_every=2, gpt_save_every=2)
    lines = (project.exports_dir / "gptsovits" / "train.list").read_text(encoding="utf-8")
    wav = Path(project.abspath(next(r for r in project.load_manifest() if r["id"] == rid)["path"])).name
    assert wav not in lines and info.get("train_minutes") is not None


def test_train_tab_drops_stale_confirm_notice(env):
    """训练页上「还没有确认训练素材」的提示：确认以后回到训练页就去掉；别的内容（进度、出错说明）不动。"""
    pytest.importorskip("gradio")
    from voicetwin.webui import app as A

    cfg, project, root = env
    ui = A.WebUI(cfg)
    voice = project.voice
    review.confirm_path(project).unlink()
    stale = "⚠️ 还没有确认训练素材，所以没有开始训练。到「① 准备素材」……"
    assert ui.refresh_train_bar(voice, stale) != ""  # 还没确认：提示留着
    assert "还没有确认训练素材" in ui.train_plan_preview(voice, "gptsovits")
    wf.review_confirm(cfg, voice)
    assert ui.refresh_train_bar(voice, stale) == ""  # 确认好了：去掉
    assert "还没有确认训练素材" not in ui.train_plan_preview(voice, "gptsovits")
    other = "<div class='vt-error'>没有完成：GPT-SoVITS 没能启动</div>"
    assert ui.refresh_train_bar(voice, other) != ""  # 出错说明不动
