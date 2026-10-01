"""网页界面的辅助函数（不需要 gradio）和环境检查里的显卡判断。"""

from voicetwin.webui.app import CLIP_HEADERS, _clips_count_md, _clips_table
from voicetwin.workflows import nvidia_smi_status


def test_clip_table_has_row_numbers_and_count(prepared):
    cfg, project, _ = prepared
    rows = _clips_table(cfg, project.voice)
    records = project.load_manifest()
    assert len(rows) == len(records) > 0
    assert all(len(r) == len(CLIP_HEADERS) for r in rows)
    assert [r[0] for r in rows] == list(range(1, len(records) + 1))
    assert rows[0][1] == records[0]["id"]

    md = _clips_count_md(cfg, project.voice)
    kept = sum(1 for r in records if r.get("keep", True))
    assert f"一共 **{len(records)}** 条片段" in md
    assert f"保留 **{kept}** 条" in md
    assert f"不保留 **{len(records) - kept}** 条" in md


def test_clip_count_for_voice_without_clips(tmp_path):
    from conftest import make_cfg

    cfg = make_cfg(tmp_path)
    assert "还没有片段" in _clips_count_md(cfg, "新声音")
    assert _clips_count_md(cfg, "") == ""


def test_nvidia_smi_driver_failure_is_not_ok():
    msg = ("NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver. "
           "Make sure that the latest NVIDIA driver is installed and running.")
    ok, detail = nvidia_smi_status(9, msg)
    assert ok is False and "驱动" in detail
    # 有些版本出错时退出码仍是 0
    assert nvidia_smi_status(0, msg)[0] is False
    assert nvidia_smi_status(0, "")[0] is False
    assert nvidia_smi_status(0, "NVIDIA GeForce RTX 5070, 12227 MiB, 576.02") == (
        True, "NVIDIA GeForce RTX 5070, 12227 MiB, 576.02")
