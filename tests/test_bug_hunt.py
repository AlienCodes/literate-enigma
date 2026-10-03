"""10-03 全面找 bug（老师要求：所有功能互不冲突、不能有 bug）找到的问题，每个一个测试（在修复以前的代码上都失败）。"""

import shutil
import threading

import numpy as np
import pytest

from voicetwin import workflows as wf
from voicetwin.data import review


def _copy_voice(prepared, tmp_path, name=None):
    from conftest import make_cfg

    cfg, project, _ = prepared
    ws = tmp_path / "ws"
    name = name or project.voice
    shutil.copytree(project.root, ws / name)
    models = ws / name / "models.json"
    if models.exists():
        models.unlink()
    cfg2 = make_cfg(ws)
    return cfg2, name, wf.open_project(cfg2, name, must_exist=True)


def _ids(project):
    return [r["id"] for r in project.load_manifest() if r.get("keep") and str(r.get("text") or "").strip()]


# ---------------------------------------------------------------------------- 两个按钮同时改校对表
def test_save_does_not_overwrite_a_row_saved_or_deleted_meanwhile(prepared, tmp_path, monkeypatch):
    """「保存修改」重新统计（读音频，要几秒）的时候，老师保存了另一行、删了一行：以前保存做完时把整个旧的校对表写回去，
    另一行改的字没了、删除的行又回来了（还会用来训练）。"""
    from voicetwin.data import prepare as prep_mod

    cfg, v, project = _copy_voice(prepared, tmp_path)
    x, y, z = _ids(project)[:3]
    inside, b_done = threading.Event(), threading.Event()
    orig = prep_mod.apply_filters

    def hooked(*a, **kw):
        if threading.current_thread().name == "A":
            inside.set()
            b_done.wait(30)
        return orig(*a, **kw)

    monkeypatch.setattr(prep_mod, "apply_filters", hooked)
    review.set_draft(project, x, text="甲：老师改好的第一句。")
    errors = []

    def a():
        try:
            wf.review_save(cfg, v)
        except Exception as exc:  # noqa: BLE001
            errors.append(repr(exc))

    def b():
        try:
            inside.wait(30)
            review.set_draft(project, y, text="乙：老师改好的另一句。")
            wf.review_save(cfg, v, ids=[y])
            wf.review_delete(cfg, v, z)
        except Exception as exc:  # noqa: BLE001
            errors.append(repr(exc))
        finally:
            b_done.set()

    ta, tb = threading.Thread(target=a, name="A"), threading.Thread(target=b, name="B")
    ta.start(); tb.start(); ta.join(); tb.join()
    assert errors == []
    recs = {r["id"]: r for r in project.load_manifest()}
    assert recs[x]["text"] == "甲：老师改好的第一句。"
    assert recs[y]["text"] == "乙：老师改好的另一句。"
    assert recs[z].get("deleted") and not recs[z].get("keep")


def test_table_save_keeps_reference_audio_that_may_be_in_use(prepared, tmp_path):
    """表格保存 / 删除时重新挑参考音频：以前先把 references/ 里的都删掉，正在「生成」的找不到参考音频，生成到一半失败。"""
    cfg, v, project = _copy_voice(prepared, tmp_path)
    refs = project.read_json(project.references_path, [])
    assert refs
    before = {p.name for p in project.refs_dir.glob("*.wav")}
    main = refs[0]["id"]
    wf.review_delete(cfg, v, main)  # 正好删掉了现在的主参考音频
    after = {p.name for p in project.refs_dir.glob("*.wav")}
    assert before <= after  # 一个都没删（生成正用着的还在）
    assert main not in [r["id"] for r in project.read_json(project.references_path, [])]


def test_broken_voice_print_cache_does_not_block_save_or_confirm(prepared, tmp_path):
    """声纹缓存是半个文件（硬盘满了、断电）：以前保存修改 / 确认训练素材一直报「出现了意外错误」（BadZipFile）。"""
    cfg, v, project = _copy_voice(prepared, tmp_path)
    caches = list(project.cache_dir.glob("emb_*.npz"))
    assert caches
    for c in caches:
        c.write_bytes(c.read_bytes()[: max(1, len(c.read_bytes()) // 2)])
    review.set_draft(project, _ids(project)[0], text="改好的一句话。")
    wf.review_save(cfg, v)
    assert wf.review_confirm(cfg, v)["confirmed"]
    for c in project.cache_dir.glob("emb_*.npz"):
        with np.load(c) as data:  # 重新写好了，能读
            assert data.files


# ---------------------------------------------------------------------------- 一键全部文字校正
def test_text_typed_into_a_row_without_recognized_text_is_never_changed(tmp_path):
    """识别时没有文字（表格说「可以双击自己打上去」）、老师自己打的字：一键校正把「借词」「艾子」改了，也不显示成改过的。"""
    from conftest import make_cfg

    cfg = make_cfg(tmp_path / "ws")
    project = wf.Project(cfg, "空行").ensure()
    project.save_manifest([{"id": "c000", "path": "clips/c000.wav", "text": "", "lang": "zh", "duration": 3.0,
                            "keep": False, "split": "train"}])
    typed = "这里的借词和艾子都是我自己打的字。"
    review.set_draft(project, "c000", text=typed, keep=True)
    for save in (False, True):
        if save:
            review.save_rows(project)
            assert project.load_manifest()[0].get("orig_text") == ""  # 最初是空的，也记下
        wf.run_transcript_fix(cfg, "空行")
        rec = project.load_manifest()[0]
        cur = review.current_values(rec, review.load_draft(project).get("c000"))["text"]
        assert cur == typed
        assert review.analyze(rec, cur)["blue"] == [(0, len(typed))]  # 整句都是老师打的（蓝色）


def test_rows_not_processed_by_the_one_click_are_not_marked_used(tmp_path):
    """还没识别出文字的句子：一键校正没处理它，却记成「用过了」——识别完以后按钮一直是灰的、这句永远不改。"""
    from conftest import make_cfg

    cfg = make_cfg(tmp_path / "ws")
    project = wf.Project(cfg, "等识别").ensure()
    project.save_manifest([
        {"id": "c000", "path": "clips/c000.wav", "text": "这个借词是一个定语从剧。", "lang": "zh", "duration": 3.0,
         "keep": True, "split": "train"},
        {"id": "c001", "path": "clips/c001.wav", "text": "", "lang": "zh", "duration": 3.0, "keep": True,
         "split": "train"},
        {"id": "c002", "path": "clips/c002.wav", "text": "删掉的借词。", "lang": "zh", "duration": 3.0, "keep": True,
         "split": "train", "deleted": True},
    ])
    res = wf.run_transcript_fix(cfg, "等识别", once=True)
    assert res["checked"] == 1 and wf.textfix_used(cfg, "等识别")
    recs = project.load_manifest()
    recs[1]["text"] = "我们看关系带词。"  # 识别完了（新素材）
    project.save_manifest(recs)
    assert not wf.textfix_used(cfg, "等识别")
    wf.run_transcript_fix(cfg, "等识别", once=True)
    draft = review.load_draft(project)
    assert "关系代词" in draft["c001"]["text"] and set(draft) == {"c000", "c001"}  # 只改了新识别出来的那句
    review.restore_clip(project, "c002")  # 恢复删除的行：不算新素材，按钮不亮
    assert wf.textfix_used(cfg, "等识别")
    assert not wf.textfix_ever_used(cfg, "没有的声音")


def test_auto_check_after_new_material_keeps_old_fixes(tmp_path):
    """加了新素材、准备素材自动查一遍错字：以前改好、保存过的行「已采用」的按钮没了，还建议把改好的字改回去（系 → 键）。"""
    from conftest import make_cfg
    from voicetwin.data import proofcheck as pc

    cfg = make_cfg(tmp_path / "ws")
    project = wf.Project(cfg, "新素材").ensure()
    orig = {"c000": "它是一个关键代词", "c001": "这个借词是一个定语从剧。"}
    project.save_manifest([{"id": k, "path": f"clips/{k}.wav", "text": t, "lang": "zh", "duration": 3.0,
                            "keep": True, "split": "train"} for k, t in orig.items()])
    wf.run_transcript_fix(cfg, "新素材", once=True)
    review.save_rows(project)
    before = {r["id"]: review.analyze(r, r["text"])["undo"] for r in project.load_manifest()}
    assert all(before.values())
    recs = project.load_manifest()
    recs.append({"id": "d000", "path": "clips/d000.wav", "text": "新的一句话里有借词。", "lang": "zh", "duration": 3.0,
                 "keep": True, "split": "train"})
    project.save_manifest(recs)
    other = dict(orig, d000="新的一句话里有借词。")  # 另一个引擎还是听成原来的错字

    class FakeRunner(pc._EngineRunner):
        def recognize(self, rec, lang):
            return other[rec["id"]], None, pc.ENGINE_FUNASR

    import unittest.mock as um

    with um.patch.object(pc, "_EngineRunner", FakeRunner):
        pc.find_suspects(project, cfg)
    for r in project.load_manifest():
        if r["id"] in orig:
            info = review.analyze(r, r["text"])
            assert info["undo"] and not info["edits"] and not info["red"], r["id"]
