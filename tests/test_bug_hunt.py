"""10-03 全面找 bug（老师要求：所有功能互不冲突、不能有 bug）找到的问题，每个一个测试（在修复以前的代码上都失败）。"""

import shutil
import threading

import numpy as np
import pytest

from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.data.lexicon_fix import has_jieba
from voicetwin.data.transcript_fix import has_pinyin

# 网页上的「一键全部文字校正」（once=True）没有拼音 / 分词工具时先说明、不开始（不白用掉这批素材唯一的一次）：
# 用到它的测试要这两个工具（整合包里都有）；没有工具时的说明另外有测试
need_tools = pytest.mark.skipif(not (has_pinyin() and has_jieba()), reason="没有装 pypinyin / jieba（整合包里有）")


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


@need_tools
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
    # 恢复删除的行：它还没用过一键校正（删除时没处理），按钮亮，只改这一句（每一句都只改一次）
    review.restore_clip(project, "c002")
    assert not wf.textfix_used(cfg, "等识别") and wf.textfix_new_ids(cfg, "等识别") == ["c002"]
    wf.run_transcript_fix(cfg, "等识别", once=True)
    draft = review.load_draft(project)
    assert "介词" in draft["c002"]["text"] and draft["c001"]["text"] == "我们看关系代词。"
    assert wf.textfix_used(cfg, "等识别")
    assert not wf.textfix_ever_used(cfg, "没有的声音")


@need_tools
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


# ============================================================================ 第三批（6 路全面检查找到的）
def _voice(tmp_path, texts, name="查错", ids=None):
    from conftest import make_cfg

    cfg = make_cfg(tmp_path / "ws")
    project = wf.Project(cfg, name).ensure()
    ids = ids or [f"c{i:03d}" for i in range(len(texts))]
    project.save_manifest([{"id": i, "path": f"clips/{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True,
                            "split": "train"} for i, t in zip(ids, texts)])
    return cfg, project


def _auto_check(project, cfg, heard):
    """🔍 自动查找：第二个识别引擎（假的 FunASR）听到的是 heard[id]。"""
    import unittest.mock as um

    from voicetwin.data import proofcheck as pc

    class FakeRunner(pc._EngineRunner):
        def recognize(self, rec, lang):
            return heard.get(rec["id"], rec["text"]), None, pc.ENGINE_FUNASR

    with um.patch.object(pc, "_EngineRunner", FakeRunner):
        return pc.find_suspects(project, cfg)


def _shown(project, rid):
    rec = {r["id"]: r for r in project.load_manifest()}[rid]
    return rec, review.analyze(rec, review.current_values(rec, review.load_draft(project).get(rid))["text"])


@need_tools
def test_auto_check_merges_with_one_click_results(tmp_path):
    """🔍 自动查找（加新素材时也自动查）以前把一键校正的结果冲掉：没采用的建议没了、母本证明没错的标红又回来了、
    新查出来的藏在 suspect_auto 里看不到——一键校正的按钮又是灰的，找不回来。"""
    cfg, project = _voice(tmp_path, ["这个主剧的结构也很完整", "其实严格意义上来说，whose不应该叫做关系代词。"])
    wf.run_transcript_fix(cfg, "查错", once=True)
    _, before = _shown(project, "c000")
    assert before["undo"]  # 一键校正改好的（主剧 → 主句）可以撤销
    res = _auto_check(project, cfg, {"c000": "这个主剧的结构也很完成"})  # 另一个引擎听成「完成」
    rec, info = _shown(project, "c000")
    assert info["undo"] and info["red"] and any(rep == "成" for _, _, rep in info["edits"])  # 留着撤销，新的也显示
    assert res["flagged"] == 1 and not review.analyze(*_shown(project, "c001")[:1])["red"]  # whose 不标红
    assert not wf.textfix_ever_used(cfg, "没有") and wf.textfix_used(cfg, "查错")  # 一个字都没多改、不算用了一次
    assert review.load_draft(project)["c000"]["text"] == "这个主句的结构也很完整"


@need_tools
@pytest.mark.parametrize("when", ["checking", "merging"])
def test_stopped_auto_check_keeps_the_one_click_results(tmp_path, when):
    """第四轮找 bug：🔍（或者准备素材里的自动查错字）查到一半点了「停止」：一键校正已经核对过、去掉了的标红和错的建议
    （最 → 很）又回来了，一键校正的按钮是灰的，只能再从头 🔍 一遍。现在停止时这些行放回一键校正的结果。"""
    import unittest.mock as um

    from voicetwin.data import proofcheck as pc
    from voicetwin.utils import progress as pg

    cfg, project = _voice(tmp_path, ["它最经常用在定语从句里面", "这个句子完全没有错误我们继续", "我们来看下一个例子好不好"])
    heard = {"c000": "它很经常用在定语从句里面"}
    _auto_check(project, cfg, heard)
    assert _shown(project, "c000")[1]["edits"] == [(1, 2, "很")]
    txt = tmp_path / "讲稿.txt"
    txt.write_text("它最经常用在定语从句里面，大家要记住。\n", encoding="utf-8")
    wf.run_transcript_fix(cfg, "查错", once=True, files=[str(txt)])  # 母本证明「最」没错：标红和建议去掉
    _, info = _shown(project, "c000")
    assert not info["red"] and not info["edits"] and wf.textfix_used(cfg, "查错")

    class FakeRunner(pc._EngineRunner):
        def recognize(self, rec, lang):
            return heard.get(rec["id"], rec["text"]), None, pc.ENGINE_FUNASR

    def prog(_f, msg):  # 第 2 条查完 / 开始合在一起的时候点「停止」
        if msg.startswith("已检查 2 /" if when == "checking" else "和你的母本对照"):
            pg.request_cancel()

    try:
        with um.patch.object(pc, "_EngineRunner", FakeRunner), pytest.raises(pg.TaskCancelled):
            pc.find_suspects(project, cfg, progress=prog)
    finally:
        pg.clear_cancel()
    _, info = _shown(project, "c000")
    assert not info["red"] and not info["edits"]  # 还是一键校正核对过的样子


def test_auto_check_does_not_suggest_what_the_teacher_undid(tmp_path):
    """老师点过「采用」又撤销的改法（王 → 黄）：以前再点 🔍 又建议回来。"""
    cfg, project = _voice(tmp_path, ["今天王芳同学回答得很好"])
    _auto_check(project, cfg, {"c000": "今天黄芳同学回答得很好"})
    review.adopt_suggestion(project, "c000")
    review.unadopt_suggestion(project, "c000")
    assert review.load_rejected(project)["c000"]
    _auto_check(project, cfg, {"c000": "今天黄芳同学回答得很好"})
    _, info = _shown(project, "c000")
    assert not info["edits"] and not info["red"]


def test_check_count_matches_the_table(tmp_path):
    """老师已经改好、还没保存的字（十 → 四），另一个引擎还是听成「十」：以前说「1 条可能有错（已标红）」，表格里一个红字都没有。"""
    cfg, project = _voice(tmp_path, ["我们今天讲十个函数", "下面我们来看第二个例子"])
    review.set_draft(project, "c000", text="我们今天讲四个函数")
    res = _auto_check(project, cfg, {"c000": "我们今天讲是个函数"})
    from voicetwin.webui import app as A

    red_rows = [rid for rid in ("c000", "c001") if _shown(project, rid)[1]["active"]]
    assert res["flagged"] == len(red_rows)
    count = A._clips_count_md(cfg, "查错")
    assert ("条可能有错" in count) == bool(red_rows)


def test_red_stays_visible_over_a_changed_word():
    """又改过、又可能有错的字：以前红色被蓝色盖住，看不到红字，也没有「这句没错」。"""
    from voicetwin.webui import app as A

    html_ = A._colored_html({"text": "我们看宾语从句", "red": [(2, 3)], "blue": [(2, 3)], "deleted": []})
    assert "vt-red" in html_ and "宾" in html_ and 'class="vt-red vt-red-blue"' in html_
    assert A._colored_html({"text": "abc", "red": [(0, 1)], "blue": [(1, 2)], "deleted": []}).count("<span") == 2


def test_teachers_english_words_are_not_flagged(tmp_path):
    """老师教英语语法：whose、why、he、way 到处都是。以前当成「把中文听成了英文」标红，还建议换成「户字」「外」「喜」。"""
    texts = ["今天我们来讲whose引导的定语从句", "关系副词主要有三个，when,where和why。", "在这个定语从句里面，主语是he。"]
    cfg, project = _voice(tmp_path, texts)
    res = _auto_check(project, cfg, {"c000": "今天我们来讲户字引导的定语从句", "c001": "关系副词主要有三个当外耳和外",
                                     "c002": "在这个定语从句里面主语是喜"})
    assert res["flagged"] == 0
    from voicetwin.data import proofcheck as pc

    assert not pc.heuristics("whose后面接名词", vocab=pc.english_vocab([]))  # 母本里的词
    assert pc.heuristics("whose后面接名词")  # 没有词表时规则照旧


def test_repeat_mark_goes_away_after_deleting_the_repeat(tmp_path):
    """「定语从句定语从句很重要」老师删掉一遍：以前一直标着「重复了 2 遍」。"""
    cfg, project = _voice(tmp_path, ["定语从句定语从句很重要"])
    _auto_check(project, cfg, {})
    _, info = _shown(project, "c000")
    assert info["red"]
    review.set_draft(project, "c000", text="定语从句很重要")
    assert not _shown(project, "c000")[1]["red"]
    review.save_rows(project)
    assert not _shown(project, "c000")[1]["red"]


@pytest.mark.parametrize("text,fixed", [
    ("I have a sister I have a sister who is a doctor.", "I have a sister who is a doctor."),
    ("翻译成英文就是I have a sister I have a sister who is a doctor。", "翻译成英文就是I have a sister who is a doctor。"),
    ("we need the the the answer here", "we need the the answer here"),
])
def test_english_repeat_mark_goes_away_after_deleting_one_copy(tmp_path, text, fixed):
    """第四轮找 bug：英文例句说了两遍（一遍和一遍之间隔着空格），老师删掉一遍以后还标着「「I have a si…」连着重复了 2 遍」。"""
    cfg, project = _voice(tmp_path, [text])
    _auto_check(project, cfg, {})
    assert _shown(project, "c000")[1]["red"]
    review.set_draft(project, "c000", text=fixed)
    assert not _shown(project, "c000")[1]["red"]
    review.save_rows(project)
    _, info = _shown(project, "c000")
    assert not info["red"] and not info["active"]


@pytest.mark.parametrize("how", ["rejected", "typed"])
def test_reasons_of_dropped_suggestions_are_not_shown_after_auto_check(tmp_path, how):
    """第四轮找 bug：老师撤销过「王 → 黄」（或者自己改成了「汪」），再 🔍 以后「王」不标红、也不建议「黄」了，
    可说明里还写着「另一个识别引擎听到的是「黄」」，像是还想改。"""
    t = "今天王芳同学回答得很好"
    cfg, project = _voice(tmp_path, [t])
    heard = {"c000": "今天黄芳同学回答得很早"}
    _auto_check(project, cfg, heard)
    assert len(_shown(project, "c000")[1]["reasons"]) == 2
    if how == "rejected":
        review._save_rejected(project, {"c000": [["王", "黄"]]})
    else:
        review.set_draft(project, "c000", text=t.replace("王", "汪"))
        review.save_rows(project)
    _auto_check(project, cfg, heard)
    rec, info = _shown(project, "c000")
    assert [e[2] for e in info["edits"]] == ["早"]
    assert info["reasons"] == ["另一个识别引擎听到的是「早」"]
    assert pc_keys_ok(rec["suspect"])


def pc_keys_ok(sus):
    """存进校对表的标记里没有原因的位置（只在查错字的过程中用）。母本优先以后每一句查完都和母本对照，
    存的是对照以后的标记（多了 text / src 这些，和一键校正的一样）。"""
    from voicetwin.data import proofcheck as pc

    return pc.REASON_POS not in sus and {"spans", "alt", "reasons", "score"} <= set(sus)


def test_manual_language_survives_edits_and_needs_reconfirm(tmp_path):
    """老师手动选的「英文」：以前改一个字就悄悄变回「中文」、保存时说「0 处语言」；确认训练素材以后改语言也不用重新确认。"""
    from voicetwin.data import review as rv

    cfg, project = _voice(tmp_path, ["Next, let's look at the 定语 clause example."])
    assert project.load_manifest()[0]["lang"] == "zh"
    rv.save_confirmed(project, project.load_manifest())  # 「✅ 确认训练素材」记下的（不重新统计音频）
    assert not wf.training_blocker(project)
    rv.set_draft(project, "c000", lang="en")
    rv.set_draft(project, "c000", text="Next, let's look at the 定语 clause examples.")
    assert rv.load_draft(project)["c000"]["lang"] == "en"
    res = rv.save_rows(project)
    assert res["changed"]["lang"] == 1 and project.load_manifest()[0]["lang"] == "en"
    assert "又改过" in wf.training_blocker(project)  # 语言也算：要重新确认
    rv.set_draft(project, "c000", text="Next, let's look at the 定语 clause example now.")
    assert rv.load_draft(project)["c000"]["lang"] == "en"
    # 旧版本的确认记录（没有语言）：升级以后不用为了这个重新确认
    import json

    rv.save_rows(project)
    recs = project.load_manifest()
    old = {"time": "2026-10-02 10:00:00", "signature": rv.material_signature(recs, 1)}
    rv.confirm_path(project).write_text(json.dumps(old), encoding="utf-8")
    assert rv.confirmed_matches(rv.load_confirmed(project), recs)


def test_header_does_not_say_confirmed_while_edits_are_unsaved(prepared, tmp_path):
    from voicetwin.webui import app as A

    cfg, v, project = _copy_voice(prepared, tmp_path)
    assert wf.review_confirm(cfg, v)["confirmed"]
    assert "✅ **训练素材已确认**" in A._clips_count_md(cfg, v)
    review.set_draft(project, _ids(project)[0], text="确认以后又改了一句。")
    md = A._clips_count_md(cfg, v)
    assert "✅ **训练素材已确认**" not in md and "还没保存" in md


def test_find_ignores_only_suspect_filter(prepared, tmp_path):
    """勾着「只看可能有错的」查找：以前表格空着、状态却说找到 N 处，「替换这一处」换掉的是看不见的句子。"""
    from voicetwin.webui import app as A

    cfg, v, project = _copy_voice(prepared, tmp_path)
    q = next(t for t in ("我们", "Python", "的") if any(t in r["text"] for r in project.load_manifest()))
    ui = A.WebUI(cfg)
    ui.do_find(v, q, True, True)  # 勾着「只看可能有错的」（这个声音一句标红的都没有）
    rows = A._clips_table(cfg, v, True)
    assert rows and len(rows) == len({m[0] for m in review.find_matches(project, q, True)})


def test_undo_replace_is_not_carried_over(tmp_path):
    """「撤销刚才的替换」：确认训练素材以后、一键校正以后、升级以后都不能再撤销（以前几天前的替换会把确认好的字改回去）；
    已经改回去的句子不再说「又改过」。"""
    import json

    cfg, project = _voice(tmp_path, ["我们先来看借词后面接宾语的情况。", "我们再看一个例子。"])
    review.replace_matches(project, "我们", "咱们")
    review.discard_draft(project, "c000")  # 这一行自己撤销了
    assert review.undo_replace(project) == {"rows": 1, "kept": 0}
    review.replace_matches(project, "我们", "咱们")
    assert review.has_undo(project)
    import unittest.mock as um

    with um.patch.object(wf, "apply_review", lambda *a, **k: {}):  # 不重新统计音频（这里没有录音文件）
        assert wf.review_confirm(cfg, "查错")["confirmed"]
    assert not review.has_undo(project) and review.undo_replace(project) == {"rows": 0, "kept": 0}
    review.replace_matches(project, "咱们", "我们")
    p = project.root / review.UNDO_FILE
    data = json.loads(p.read_text(encoding="utf-8"))
    data["version"] = "18.4"  # 旧版本留下的
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    assert not review.has_undo(project) and not p.exists()


def test_one_click_refuses_without_pinyin_tools(tmp_path, monkeypatch):
    """没有拼音 / 分词工具（独立安装）：以前只改一点点，还用掉了这批素材唯一的一次。现在先说明、不开始。"""
    from voicetwin.data import lexicon_fix, transcript_fix as tf

    cfg, project = _voice(tmp_path, ["这个借词是一个定语从剧。"])
    monkeypatch.setattr(tf, "has_pinyin", lambda: False)
    with pytest.raises(ValueError, match="拼音"):
        wf.run_transcript_fix(cfg, "查错", once=True)
    assert not wf.textfix_ever_used(cfg, "查错") and not review.load_draft(project)
    monkeypatch.setattr(tf, "has_pinyin", lambda: True)
    monkeypatch.setattr(lexicon_fix, "has_jieba", lambda: False)
    with pytest.raises(ValueError, match="分词"):
        wf.run_transcript_fix(cfg, "查错", once=True)


@need_tools
def test_one_click_texts_tell_why_and_what(tmp_path):
    """按钮灰的时候说明为什么（还没有能校正的句子 / 用过了）；第二批起写「检查了新加的 N 条」；
    下载 txt 的提示不叫老师去点灰色的按钮，路径不多出反斜杠。"""
    from voicetwin.webui import app as A

    cfg, project = _voice(tmp_path, [""])
    ui = A.WebUI(cfg)
    assert A.TEXTFIX_NOTHING_INFO in ui.textfix_info("查错") and not ui.textfix_btn("查错")["interactive"]
    recs = project.load_manifest()
    recs[0]["text"] = "这个借词是一个定语从剧。"
    recs.append({"id": "c001", "path": "clips/c001.wav", "text": "我们看关系带词。", "lang": "zh", "duration": 3.0,
                 "keep": True, "split": "train"})
    project.save_manifest(recs)
    r1 = wf.run_transcript_fix(cfg, "查错", once=True)
    assert "新加的" not in A.WebUI._textfix_md(r1)
    assert A.TEXTFIX_LOCKED_INFO in ui.textfix_info("查错") and not ui.textfix_files("查错")["interactive"]
    recs = project.load_manifest()
    recs.append({"id": "c002", "path": "clips/c002.wav", "text": "新的借词。", "lang": "zh", "duration": 3.0,
                 "keep": True, "split": "train"})
    project.save_manifest(recs)
    assert "还没用过一键校正" in ui.textfix_info("查错") and ui.textfix_files("查错")["interactive"]
    r2 = wf.run_transcript_fix(cfg, "查错", once=True)
    assert "检查了新加的 1 条" in A.WebUI._textfix_md(r2)
    out = ui.do_download_text("查错")
    md = out[A.WebUI.DLTXT_OUT.index("dl_txt_md")]
    assert "\\_" not in md and "再点「📝 一键全部文字校正」" not in md


def test_srt_times_and_timed_dubbing():
    """字幕时间：59.9999 秒以前写成 00:00:60,000（剪映不认）；按字幕配音时两句会叠在一起、或者一点停顿都没有。"""
    from voicetwin.data.subtitles import _fmt_time
    from voicetwin.synth import engine

    assert _fmt_time(59.9999) == "00:01:00,000" and _fmt_time(3599.9996) == "01:00:00,000"
    assert engine.TIMED_MIN_GAP > 0 and engine.TIMED_MIN_CLAUSE_GAP > 0


def test_mp3_does_not_delete_the_wav_and_names_do_not_clash(prepared, tmp_path):
    """同一分钟里先生成 WAV 再生成 MP3：以前刚听过的 WAV 被删掉了，字幕和报告也被覆盖。"""
    from voicetwin.webui import app as A

    cfg, v, project = _copy_voice(prepared, tmp_path)
    a = A._output_path(project, "第3课", "wav", "x")
    first = wf.run_narrate(cfg, v, "第一句话在这里。", out=str(a), quality="fast")
    b = A._output_path(project, "第3课", "mp3", "x")
    assert b.stem != a.stem
    second = wf.run_narrate(cfg, v, "第一句话在这里。", out=str(a.with_suffix(".mp3")), quality="fast")
    # 文件名最后是实际用的模型名（测试引擎写 dummy）：同名的 WAV 和 MP3 都在，谁也没删掉谁
    assert first.audio_path.name == a.stem + "_dummy.wav" and second.audio_path.name == a.stem + "_dummy.mp3"
    assert first.audio_path.exists() and second.audio_path.exists()


def test_failed_retrain_keeps_the_old_material_warning(tmp_path):
    """重新训练失败 / 中途停止：以前「现在的模型是用改之前的文字训练的」提醒悄悄没了（训练开始时就记下了新素材）。"""
    import hashlib

    from voicetwin.backends import gptsovits as g

    class B:
        name, exp_name, version = "gptsovits", "x", "v2ProPlus"

    b = B()
    b.project = type("P", (), {})()
    b.project.load_models = lambda: {"gptsovits": {"sovits": ["a.pth"], "list_sha1": "旧的"}}
    stamp_dir = tmp_path / "logs"
    stamp_dir.mkdir()
    # 失败的那次训练开始时写的（就是现在的素材）
    (stamp_dir / "voicetwin_list.sha1").write_text(hashlib.sha1(b"new" + B.version.encode()).hexdigest())
    b._opt_dir = lambda: stamp_dir
    import voicetwin.data.exporters as ex

    orig_tr, orig_txt = ex.train_records, ex.gptsovits_list_text
    try:
        ex.train_records = lambda project: [{"id": "c0"}]
        ex.gptsovits_list_text = lambda project, speaker, recs, **kw: "new"  # kw：legacy_punct（以前的句末标点规则）
        note = g.GPTSoVITSBackend.trained_material_note(b)
    finally:
        ex.train_records, ex.gptsovits_list_text = orig_tr, orig_txt
    assert "改之前" in note


def test_empty_script_is_not_a_program_fault():
    """讲稿里只有 ``` 代码、[停顿]、表情：以前说「讲稿是空的」，还生成一份「问题报告」叫老师发给帮忙的人。"""
    from voicetwin.errors import explain
    from voicetwin.webui import tasks

    f = explain(ValueError("讲稿里没有可以朗读的内容"))
    assert f.key in tasks.NO_REPORT_KEYS and "代码" in f.advice


# ---------------------------------------------------------------------------- 第四轮找 bug（g3：确认训练素材）
def _v1_confirm(project):
    """v18.2 ~ v18.4 存的确认记录：签名里没有语言，也没有 sig_version。"""
    import json

    recs = project.load_manifest()
    review.confirm_path(project).write_text(json.dumps({"time": "2026-09-30 10:00:00",
                                                        "signature": review.material_signature(recs, 1),
                                                        "counts": review.material_counts(recs)}), encoding="utf-8")


def test_old_confirmation_is_upgraded_so_a_language_change_counts(tmp_path):
    """v18.4 确认过，升级以后只把一句的语言从中文改成英文、保存：以前旧记录一直按旧算法（没有语言）比，照样能开始训练，
    表格上方还写「✅ 已确认」。现在旧记录还对得上时原样换成新算法（升级不用重新确认），之后改语言要重新确认。"""
    import json

    cfg, project = _voice(tmp_path, ["Next, let's look at the 定语 clause example.", "第二句话。"])
    _v1_confirm(project)
    assert not wf.training_blocker(project)  # 升级以后不用重新确认
    conf = json.loads(review.confirm_path(project).read_text(encoding="utf-8"))
    assert conf["sig_version"] == review.SIGNATURE_VERSION and conf["time"] == "2026-09-30 10:00:00"
    review.set_draft(project, "c000", lang="en")
    assert review.save_rows(project)["changed"]["lang"] == 1
    assert "又改过" in wf.training_blocker(project)
    # 没打开过校对表、第一个读到确认记录的就是「保存修改」：保存之前先换好
    cfg, project = _voice(tmp_path / "b", ["Next, let's look at the 定语 clause example.", "第二句话。"])
    _v1_confirm(project)
    review.set_draft(project, "c000", lang="en")
    review.save_rows(project)
    assert "又改过" in wf.training_blocker(project)
    # 在 Excel 里改的语言（读回 transcripts.csv）也一样
    cfg, project = _voice(tmp_path / "c", ["Next, let's look at the 定语 clause example.", "第二句话。"])
    project.export_csv()
    _v1_confirm(project)
    text = project.csv_path.read_text(encoding="utf-8-sig").replace(",zh,", ",en,", 1)
    project.csv_path.write_text(text, encoding="utf-8-sig")
    assert project.import_csv()["lang"] == 1
    assert "又改过" in wf.training_blocker(project)
    # 确认以后在旧版本里就改过（已经对不上）：不换，照样要求重新确认
    cfg, project = _voice(tmp_path / "d", ["第一句话。", "第二句话。"])
    _v1_confirm(project)
    recs = project.load_manifest()
    recs[0]["text"] = "第一句话改了。"
    project.save_manifest(recs)
    assert "又改过" in wf.training_blocker(project)
    assert "sig_version" not in json.loads(review.confirm_path(project).read_text(encoding="utf-8"))


def test_confirm_keeps_the_undo_of_a_replace_made_while_confirming(tmp_path):
    """点了「✅ 确认训练素材」（重新统计音频要几秒，页面没有进度），这期间又点了「全部替换」：以前确认做完把这次替换的
    撤销记录也删了，「↩️ 撤销刚才的替换」说没有可以撤销的；确认前做的替换照样删（不能再把确认好的字改回去）。"""
    import unittest.mock as um

    from voicetwin.webui import app as A

    cfg, project = _voice(tmp_path, ["我们先来看借词后面接宾语的情况。", "我们再看一个例子。"])
    review.replace_matches(project, "借词", "介词")  # 确认以前做的替换

    def slow_apply(cfg_, voice_, read_csv=True):
        review.replace_matches(project, "我们", "咱们")  # 确认还没做完，老师点了「全部替换」
        return {}

    with um.patch.object(wf, "apply_review", slow_apply):
        res = wf.review_confirm(cfg, "查错")
    assert res["confirmed"] and res["unsaved"] == 2
    assert review.has_undo(project) and review.undo_replace(project) == {"rows": 2, "kept": 0}
    assert review.unsaved_count(project) == 0 and "介词" in project.load_manifest()[0]["text"]
    # 网页上说清楚：确认的是改之前的样子
    with um.patch.object(wf, "apply_review", slow_apply):
        md = A.WebUI(cfg).do_confirm("查错")[0]
    assert "又改了 2 句" in md and "撤销刚才的替换" in md
    # 确认期间没有新的替换：照样删（确认以后不能再把确认好的字改回去）
    review.save_rows(project)
    review.replace_matches(project, "咱们", "我们")
    with um.patch.object(wf, "apply_review", lambda *a, **k: {}):
        assert wf.review_confirm(cfg, "查错")["unsaved"] == 0
    assert not review.has_undo(project)
