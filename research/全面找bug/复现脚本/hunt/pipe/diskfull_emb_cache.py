"""Real ENOSPC (tiny tmpfs mounted as the voice's cache/ folder): np.savez() writes cache/emb_<encoder>.npz in place
(no temp file).  When the disk fills up during that write, a half-written zip is left behind.  After the teacher
frees space, every 「保存修改」/「确认训练素材」/「开始准备素材」 fails with BadZipFile -> 「出现了意外错误」, forever."""
import os, shutil, subprocess, sys
from pathlib import Path
from common import HERE, cleanup, lecture, make_cfg, make_lecture, workspace
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.errors import explain

ws = workspace("diskfull"); cfg = make_cfg(ws); V = "张老师"
wf.run_prepare(cfg, V, [str(lecture(2))])
p = wf.Project(cfg, V)
mnt = HERE / "mnt"; mnt.mkdir(exist_ok=True)
subprocess.run(["mount", "-t", "tmpfs", "-o", "size=256k", "tmpfs", str(mnt)], check=True)
try:
    for f in p.cache_dir.iterdir():
        shutil.move(str(f), str(mnt / f.name))
    p.cache_dir.rmdir(); os.symlink(mnt, p.cache_dir)
    npz = next(mnt.glob("emb_*.npz")); print("existing cache:", npz.name, npz.stat().st_size, "bytes")
    # fill the small disk completely
    fd = os.open(str(mnt / "filler.bin"), os.O_WRONLY | os.O_CREAT)
    try:
        while True:
            os.write(fd, b"\0" * 4096)
    except OSError:
        pass
    os.close(fd)
    print("free bytes now:", shutil.disk_usage(str(mnt)).free)
    new_dir = HERE / "lecture_cache" / "second"
    if not (new_dir / "第2课.wav").exists():
        make_lecture(new_dir / "第2课.wav", repeats=1, seed=7)
    try:
        wf.run_prepare(cfg, V, [str(lecture(2)), str(new_dir)])
        print("prepare OK (disk did not fill?)")
    except Exception as exc:
        print("prepare with full disk:", type(exc).__name__, "| teacher sees:", explain(exc).title)
    print("npz after failure:", npz.stat().st_size, "bytes; valid zip:", __import__("zipfile").is_zipfile(npz))
    (mnt / "filler.bin").unlink()   # teacher empties the recycle bin
    print("free bytes after cleanup:", shutil.disk_usage(str(mnt)).free)
    ids = [r["id"] for r in p.load_manifest() if r.get("text")]
    review.set_draft(p, ids[0], text="老师改好的一句话。")
    for name, fn in [("保存修改", lambda: wf.review_save(cfg, V)), ("确认训练素材", lambda: wf.review_confirm(cfg, V)),
                     ("开始准备素材", lambda: wf.run_prepare(cfg, V, [str(lecture(2)), str(new_dir)]))]:
        for attempt in (1, 2):
            try:
                fn(); print(f"  {name} (try {attempt}): OK")
            except Exception as exc:
                f = explain(exc); print(f"  {name} (try {attempt}): FAIL {type(exc).__name__}: {exc} | teacher sees: {f.title}")
finally:
    if p.cache_dir.is_symlink():
        p.cache_dir.unlink()
    subprocess.run(["umount", str(mnt)])
    cleanup()
