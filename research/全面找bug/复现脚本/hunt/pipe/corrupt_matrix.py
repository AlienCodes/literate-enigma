"""Damaged side files (what an interrupted / disk-full write or a power cut leaves behind) vs. the main entry points.

For each file we copy a freshly prepared voice, damage that one file, and call the entry points the web page /
CLI use. We print OK or the exception + the Chinese title errors.explain() would show the teacher.
"""
import json
import shutil
import sys
import traceback
from pathlib import Path

from common import cleanup, lecture, make_cfg, workspace

from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.errors import explain

VOICE = "损坏测试"
OTHER = "另一个好好的声音"
base_ws = workspace("corrupt_base")
cfg0 = make_cfg(base_ws)
wf.run_prepare(cfg0, VOICE, [str(lecture(2))])
wf.review_confirm(cfg0, VOICE)
# one narration so a segment cache exists
wf.run_narrate(cfg0, VOICE, "大家好，这是第一句话。", out=str(base_ws / "o.wav"), quality="fast")
shutil.copytree(base_ws / VOICE, base_ws / OTHER)

TARGETS = {
    "manifest.jsonl (last line cut)": ("manifest.jsonl", "cut_last"),
    "manifest.jsonl (empty)": ("manifest.jsonl", "empty"),
    "prepare_summary.json (empty)": ("prepare_summary.json", "empty"),
    "models.json (half)": ("models.json", "half"),
    "profile.json (empty)": ("profile.json", "empty"),
    "references.json (half)": ("references.json", "half"),
    "sources.json (empty)": ("sources.json", "empty"),
    "cache/emb_mfcc-stats.npz (half)": ("cache/emb_mfcc-stats.npz", "half"),
    "segment cache meta (half)": ("SEGMETA", "half"),
}


def damage(root: Path, rel: str, how: str) -> None:
    if rel == "SEGMETA":
        files = sorted((root / "cache" / "segments").rglob("*.json"))
        p = files[0]
    else:
        p = root / rel
    if not p.exists():
        if rel == "models.json":
            p.write_text(json.dumps({"dummy": {"selected": {"id": "x"}}}), encoding="utf-8")
        else:
            print(f"   (file {rel} did not exist)")
            return
    data = p.read_bytes()
    if how == "empty":
        p.write_bytes(b"")
    elif how == "half":
        p.write_bytes(data[: len(data) // 2])
    elif how == "cut_last":
        lines = data.split(b"\n")
        lines[-2] = lines[-2][: len(lines[-2]) // 2]
        p.write_bytes(b"\n".join(lines))


def call(name, fn):
    try:
        r = fn()
        print(f"   {name:<28} OK" + (f"  -> {r}" if r not in (None, "") else ""))
    except BaseException as exc:  # noqa
        f = explain(exc)
        print(f"   {name:<28} FAIL {type(exc).__name__}: {str(exc)[:70]!r}\n   {'':<28}      teacher sees: 「{f.title}」 {f.advice[:60]}")


only = sys.argv[1:] or list(TARGETS)
for label in only:
    rel, how = TARGETS[label]
    ws = workspace("corrupt_case")
    shutil.copytree(base_ws / VOICE, ws / VOICE)
    shutil.copytree(base_ws / OTHER, ws / OTHER)
    cfg = make_cfg(ws)
    proj_root = ws / VOICE
    damage(proj_root, rel, how)
    print(f"== {label}")
    call("list_voices (dropdown)", lambda: [v["voice"] for v in wf.list_voices(cfg)])
    call("voice_library", lambda: len(wf.voice_library(cfg)))
    call("training_blocker_for", lambda: wf.training_blocker_for(cfg, VOICE)[:30])
    p = wf.Project(cfg, VOICE)

    def save():
        ids = [r["id"] for r in p.load_manifest() if r.get("text")]
        review.set_draft(p, ids[0], text="老师改好的一句话。")
        return wf.review_save(cfg, VOICE)["saved"]

    call("set_draft + review_save", save)
    call("review_confirm", lambda: wf.review_confirm(cfg, VOICE)["confirmed"])
    call("run_narrate (fast)", lambda: wf.run_narrate(cfg, VOICE, "大家好，这是第一句话。", out=str(ws / "n.wav"),
                                                      quality="fast").duration)
    call("run_prepare again", lambda: wf.run_prepare(cfg, VOICE, [str(lecture(2))])["clips_kept"])
cleanup()
