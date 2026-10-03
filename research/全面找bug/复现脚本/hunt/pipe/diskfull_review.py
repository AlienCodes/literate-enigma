"""Whole workspace on a tiny tmpfs, disk completely full: proofreading actions must fail with the Chinese disk
message and lose nothing (manifest + existing drafts intact)."""
import os, shutil, subprocess, json
from common import HERE, cleanup, lecture, make_cfg, workspace
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.errors import explain
mnt = HERE / "mnt2"; mnt.mkdir(exist_ok=True)
subprocess.run(["mount", "-t", "tmpfs", "-o", "size=48m", "tmpfs", str(mnt)], check=True)
try:
    ws = mnt / "ws"; cfg = make_cfg(ws); V = "张老师"
    wf.run_prepare(cfg, V, [str(lecture(2))])
    p = wf.Project(cfg, V)
    ids = [r["id"] for r in p.load_manifest() if r.get("text")]
    review.set_draft(p, ids[0], text="第一条草稿，还没保存。")
    man_before = p.manifest_path.read_bytes(); draft_before = review.load_draft(p)
    print("du:", subprocess.run(["du", "-sh", str(ws)], capture_output=True, text=True).stdout.strip())
    fd = os.open(str(mnt / "filler.bin"), os.O_WRONLY | os.O_CREAT)
    try:
        while True: os.write(fd, b"\0" * 65536)
    except OSError: pass
    try:
        while True: os.write(fd, b"\0" * 512)
    except OSError: pass
    os.close(fd)
    print("free:", shutil.disk_usage(str(mnt)).free)
    def t(name, fn):
        try:
            r = fn(); print(f"  {name}: OK {str(r)[:80]}")
        except Exception as exc:
            print(f"  {name}: FAIL {type(exc).__name__} | teacher sees: {explain(exc).title}")
    t("edit row 2 (set_draft)", lambda: review.set_draft(p, ids[1], text="第二条草稿。"))
    t("保存修改", lambda: wf.review_save(cfg, V)["saved"])
    t("删除这一行", lambda: wf.review_delete(cfg, V, ids[3])["id"])
    t("确认训练素材", lambda: wf.review_confirm(cfg, V)["confirmed"])
    t("下载改好的文字", lambda: wf.export_review_text(cfg, V)["lines"])
    t("生成", lambda: wf.run_narrate(cfg, V, "大家好，这是一句话。", quality="fast").duration)
    leftovers = [f.name for f in p.root.iterdir() if f.name.endswith(".tmp")]
    print("manifest unchanged:", p.manifest_path.read_bytes() == man_before, "| drafts kept:", review.load_draft(p) == draft_before,
          "| leftover .tmp files:", leftovers)
    (mnt / "filler.bin").unlink()
    t("保存修改 after cleanup", lambda: wf.review_save(cfg, V)["saved"])
    t("确认训练素材 after cleanup", lambda: wf.review_confirm(cfg, V)["confirmed"])
    t("生成 after cleanup", lambda: round(wf.run_narrate(cfg, V, "大家好，这是一句话。", quality="fast").duration, 2))
finally:
    import logging
    for h in logging.getLogger("voicetwin").handlers[:]:
        try: h.close()
        except Exception: pass
        logging.getLogger("voicetwin").removeHandler(h)
    subprocess.run(["umount", "-l", str(mnt)])
    cleanup()
