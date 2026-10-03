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


# ============================================================================ 第二批
# ---------------------------------------------------------------------------- 讲稿
def test_one_long_line_with_a_dot_is_read_as_script_text(prepared, tmp_path):
    """讲稿框里粘贴一整段（一行、超过 255 个字节、里面有「.」：Python 3.9、英文句子）：以前程序把它当文件名去问硬盘，
    Linux / Mac 报「文件名太长」，老师看到不相干的提示，生成不了。"""
    from voicetwin.synth.script import parse_script

    cfg, v, project = _copy_voice(prepared, tmp_path)
    text = "今天我们讲 Python 3.9 里面的列表推导式，" + "它可以让代码变得更加简洁也更容易阅读，" * 4 + "好。"
    assert len(text.encode()) > 255
    res = wf.run_narrate(cfg, v, text, out=str(tmp_path / "o.wav"), quality="fast")
    assert res.duration > 1
    long_md = "很长的一行讲稿" * 40 + "，详见讲义.md"  # 结尾像文件名，也当讲稿文字
    assert parse_script(long_md)


# ---------------------------------------------------------------------------- 命令行 / 全自动
def test_command_line_can_confirm_material(prepared, tmp_path, capsys):
    """命令行没有「确认训练素材」：voicetwin train 永远说「还没有确认」，命令行用户没法训练。"""
    from voicetwin.cli import main
    from voicetwin.data import review as rv

    cfg, v, project = _copy_voice(prepared, tmp_path)
    (project.root / "review_confirmed.json").unlink(missing_ok=True)
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(f"workspace: '{project.root.parent.as_posix()}'\nbackend: dummy\nspeaker_encoder: mfcc\n"
                        f"similarity:\n  model_dir: '{(tmp_path / '_sv').as_posix()}'\n", encoding="utf-8")
    assert wf.training_blocker(project)
    main(["-c", str(cfg_file), "confirm", "-v", v])
    assert "训练素材已确认" in capsys.readouterr().out
    assert rv.load_confirmed(project) and not wf.training_blocker(project)
    assert "voicetwin confirm" in str(__import__("voicetwin.cli", fromlist=["EPILOG"]).EPILOG)


def test_auto_confirms_the_material_it_prepared(tmp_path, lecture_dir):
    """全自动（auto）没有人工校对这一步：以前准备好的素材没确认，训练引擎永远不开始训练。"""
    from conftest import make_cfg
    from voicetwin.data import review as rv

    cfg = make_cfg(tmp_path / "ws")
    wf.run_auto(cfg, "全自动", [str(lecture_dir)], skip_train=True)
    project = wf.open_project(cfg, "全自动", must_exist=True)
    assert rv.load_confirmed(project) and not wf.training_blocker(project)


# ---------------------------------------------------------------------------- 坏文件、一时读不了的文件
def test_damaged_files_do_not_stop_the_program(prepared, tmp_path):
    """写到一半断电 / 硬盘满了留下的半个文件（manifest 最后一行断在一个汉字中间、草稿 / 撤销记录 / 处理记录是半个）：
    以前校对表打不开、保存 / 确认 / 准备素材一直报「出现了意外错误」。"""
    from voicetwin.data import transcript_fix as tf

    cfg, v, project = _copy_voice(prepared, tmp_path)
    n = len(project.load_manifest())
    raw = project.manifest_path.read_bytes()
    cut = '{"id": "c999", "text": "断在汉字中间'.encode("utf-8")[:-1]
    project.manifest_path.write_bytes(raw + cut)
    assert len(project.load_manifest()) == n  # 坏的那行跳过，别的照常
    assert (project.root / "manifest.jsonl.bad").exists()
    for name in ("review_draft.json", "review_rejected.json", tf.USED_FILE):
        (project.root / name).write_bytes('{"c000": {"text": "半'.encode("utf-8")[:-2])
    (project.root / "profile.json").write_text("", encoding="utf-8")
    assert review.load_draft(project) == {} and review.load_rejected(project) == {}
    assert (project.root / "review_draft.json.bad").exists()
    assert project.read_json(project.root / "profile.json", {"x": 1}) == {"x": 1}
    first = _ids(project)[0]
    review.set_draft(project, first, text="坏文件以后照样能改。")
    wf.review_save(cfg, v)
    assert wf.review_confirm(cfg, v)["confirmed"]
    assert {r["id"]: r for r in project.load_manifest()}[first]["text"] == "坏文件以后照样能改。"
    wf.textfix_used(cfg, v)  # 一键校正的记录坏了也不报错


def test_damaged_sources_record_does_not_cut_the_videos_again(prepared, tmp_path, lecture_dir):
    """sources.json（处理过哪些视频）坏了：以前准备素材直接出错；当成都没处理过的话，同一段话会切两遍、训练两次。"""
    cfg, v, project = _copy_voice(prepared, tmp_path)
    n = len(project.load_manifest())
    project.sources_path.write_text('{"lesson_1": {"done": tr', encoding="utf-8")
    again = wf.run_prepare(cfg, v, [str(lecture_dir)])
    assert len(project.load_manifest()) == n and again["files_new"] == 0
    assert (project.root / "sources.json.bad").exists()


def test_unreadable_side_files_are_not_treated_as_empty(prepared, tmp_path, monkeypatch):
    """草稿文件一时读不了（Windows 上杀毒软件 / OneDrive 占着）：以前当作没有草稿，再改一句就只剩这一句，
    别的没保存的修改全没了。现在报错说明（等几秒再点），修改都还在。"""
    from pathlib import Path

    from voicetwin.utils import atomic

    cfg, v, project = _copy_voice(prepared, tmp_path)
    x, y, z = _ids(project)[:3]
    review.set_draft(project, x, text="第一句没保存的修改。")
    review.set_draft(project, y, text="第二句没保存的修改。")
    monkeypatch.setattr(atomic, "RETRY_WAITS", [0.01])
    real = Path.read_text

    def locked(self, *a, **kw):
        if self.name == review.DRAFT_FILE:
            raise PermissionError(13, "另一个程序正在使用此文件")
        return real(self, *a, **kw)

    monkeypatch.setattr(Path, "read_text", locked)
    with pytest.raises(OSError, match="等几秒再点一次"):
        review.set_draft(project, z, text="第三句。")
    monkeypatch.setattr(Path, "read_text", real)
    draft = review.load_draft(project)
    assert draft[x]["text"] == "第一句没保存的修改。" and draft[y]["text"] == "第二句没保存的修改。"


# ---------------------------------------------------------------------------- 准备素材
def _lecture_copy(lecture_dir, dest):
    shutil.copytree(lecture_dir, dest)
    return dest


def test_moved_videos_are_not_cut_again(tmp_path, lecture_dir):
    """同样的视频换了位置（移动硬盘换了盘符、解压到新文件夹）：以前当成新视频再切一遍，同一段话用两次
    （其中一份还是没改过的错字）。旧版本留下的记录（没有内容指纹）：同名、同样大小、原来的位置没了才算；
    同名的另一个视频照样处理。"""
    import json

    from conftest import make_cfg

    cfg = make_cfg(tmp_path / "ws")
    e = _lecture_copy(lecture_dir, tmp_path / "E盘" / "讲课")
    wf.run_prepare(cfg, "搬家", [str(e)])
    project = wf.open_project(cfg, "搬家", must_exist=True)
    n = len(project.load_manifest())
    f = tmp_path / "F盘" / "讲课"
    shutil.move(str(e.parent), str(f.parent))
    assert wf.run_prepare(cfg, "搬家", [str(f)])["files_new"] == 0 and len(project.load_manifest()) == n
    # 旧版本的记录：去掉内容指纹，再搬一次
    db = json.loads(project.sources_path.read_text(encoding="utf-8"))
    for info in db.values():
        info.pop("key", None)
    project.sources_path.write_text(json.dumps(db, ensure_ascii=False), encoding="utf-8")
    g = tmp_path / "G盘" / "讲课"
    shutil.move(str(f.parent), str(g.parent))
    assert wf.run_prepare(cfg, "搬家", [str(g)])["files_new"] == 0 and len(project.load_manifest()) == n
    # 同名但不一样的视频（大小不同）：是新素材
    other = tmp_path / "H盘" / "讲课"
    other.mkdir(parents=True)
    src = next(p for p in sorted(g.iterdir()) if p.suffix == ".wav")
    data = src.read_bytes()
    (other / src.name).write_bytes(data + data[44:44 + 88200])
    assert wf.run_prepare(cfg, "搬家", [str(other)])["files_new"] == 1


def test_folder_that_contains_the_workspace_does_not_add_own_clips(tmp_path, lecture_dir):
    """老师填的文件夹正好包含声音分身的工作区（比如整个 D 盘的一个大文件夹）：以前把程序自己切好的片段、
    生成的音频当成新素材（20 条变成 68 条）。网页上传的视频（uploads）照样算素材。"""
    from conftest import make_cfg

    top = tmp_path / "D盘"
    cfg = make_cfg(top / "VoiceTwin" / "workspace")
    _lecture_copy(lecture_dir, top / "讲课")
    wf.run_prepare(cfg, "大文件夹", [str(top / "讲课")])
    project = wf.open_project(cfg, "大文件夹", must_exist=True)
    n = len(project.load_manifest())
    up = project.root / "uploads"
    up.mkdir(exist_ok=True)
    src = next(p for p in sorted((top / "讲课").iterdir()) if p.suffix == ".wav")
    data = src.read_bytes()
    (up / "上传的第2课.wav").write_bytes(data + data[44:44 + 88200])
    res = wf.run_prepare(cfg, "大文件夹", [str(top)])
    assert res["files_new"] == 1  # 只有上传的那一个是新的；clips / references / outputs 里的都不算
    assert not any("clips" in str(r.get("source", "")) for r in project.load_manifest())
    assert len(project.load_manifest()) > n


def test_csv_open_in_excel_does_not_fail_prepare(prepared, tmp_path, lecture_dir, monkeypatch):
    """准备素材快做完时 transcripts.csv 正被 Excel 打开着（写不了）：以前整个准备素材报错（素材其实已经准备好了）。"""
    from voicetwin.project import Project

    cfg, v, project = _copy_voice(prepared, tmp_path)

    def locked(self, records=None):
        raise PermissionError(13, "另一个程序正在使用此文件", str(self.csv_path))

    monkeypatch.setattr(Project, "export_csv", locked)
    res = wf.run_prepare(cfg, v, [str(lecture_dir)])
    assert any("Excel" in w for w in res["warnings"])


def test_old_csv_does_not_undo_web_edits(prepared, tmp_path):
    """transcripts.csv 上次没能更新（被 Excel 打开着），网页上又改好、保存了：以前读回 CSV 时，CSV 里的旧字把网页上
    改好的字改回去。现在只用 Excel 里真改过的格子。"""
    import csv as _csv

    cfg, v, project = _copy_voice(prepared, tmp_path)
    project.export_csv()
    x, y = _ids(project)[:2]
    recs = project.load_manifest()
    for r in recs:
        if r["id"] == x:
            r["text"] = "网页上后来改好的字。"  # CSV 没能跟着更新
    project.save_manifest(recs)
    rows = list(_csv.DictReader(open(project.csv_path, encoding="utf-8-sig")))
    for r in rows:
        if r["id"] == y:
            r["text"] = "表格软件里改的字。"
    with open(project.csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    changed = project.import_csv()
    got = {r["id"]: r["text"] for r in project.load_manifest()}
    assert got[x] == "网页上后来改好的字。" and got[y] == "表格软件里改的字。" and changed["text"] == 1


# ---------------------------------------------------------------------------- 声音名称、生成缓存
@pytest.mark.parametrize("name", ["..", ".", " . ", "老师\t2"])
def test_bad_voice_names_are_refused(tmp_path, name):
    """「..」会变成工作区的上一级文件夹（删除这个声音会删错地方）；Tab、换行做不了文件夹名。"""
    from conftest import make_cfg

    cfg = make_cfg(tmp_path / "ws")
    with pytest.raises(ValueError):
        wf.Project(cfg, name)
    assert wf.Project(cfg, "张老师.").voice == "张老师"  # Windows 的文件夹名结尾不能是点


def test_broken_sentence_cache_is_generated_again(prepared, tmp_path):
    """生成到一半关了窗口 / 断电，某一句的缓存是半个文件：以前这篇讲稿每次生成都在这一句失败。"""
    cfg, v, project = _copy_voice(prepared, tmp_path)
    text = "第一句话在这里。第二句话也在这里。"
    wf.run_narrate(cfg, v, text, out=str(tmp_path / "a.wav"), quality="fast")
    wavs = list((project.cache_dir / "segments").rglob("*.wav"))
    assert wavs
    for w in wavs:
        w.write_bytes(w.read_bytes()[:30])
    res = wf.run_narrate(cfg, v, text, out=str(tmp_path / "b.wav"), quality="fast")
    assert res.duration > 1
