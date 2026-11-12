#!/usr/bin/env python3
"""Read-only audit using the repository's unchanged canonical alignment functions."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / ".github/alignment-audit70"
OUT = ROOT / "alignment-audit70-output"
RUNTIME = ROOT / "alignment-audit70-runtime"
SOURCE = json.loads((TASK / "source.json").read_text())["source_sha"]
OUT.mkdir(exist_ok=True)
os.environ["VIDEO_S"] = "2"

def run(args, **kw):
    return subprocess.run([str(x) for x in args], check=True, **kw)

def git_bytes(path):
    return run(["git", "show", SOURCE + ":" + path], cwd=ROOT, capture_output=True).stdout

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

tools_dir = RUNTIME / "视频/工具"
scripts_dir = RUNTIME / "视频/脚本"
tools_dir.mkdir(parents=True, exist_ok=True)
scripts_dir.mkdir(parents=True, exist_ok=True)
provenance = {}
for name in ("render.py", "对正量.py", "逐词对齐.py"):
    path = "视频/工具/" + name
    raw = git_bytes(path)
    (tools_dir / name).write_bytes(raw)
    provenance[path] = sha(raw)
for name in ("Inter.ttf", "NotoSansSC.ttf"):
    path = "视频/工具/fonts/" + name
    raw = git_bytes(path)
    target = tools_dir / "fonts" / name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(raw)
    provenance[path] = sha(raw)
for path in ("视频/工具/新管/规则表.json", "视频/制作硬性标准与踩坑总结.md"):
    raw = git_bytes(path)
    provenance[path] = sha(raw)
    if path.endswith(".json"):
        registry = json.loads(raw)
    else:
        hard_rules = raw.decode()
assert any(x["编号"] == "L20" for x in registry["规则"])
assert "| T39 |" in hard_rules and "画22" in hard_rules
documents = {}
for number in range(1, 71):
    no = f"{number:02}"
    raw = git_bytes(f"视频/脚本/{no}.json")
    (scripts_dir / f"{no}.json").write_bytes(raw)
    documents[no] = (json.loads(raw), sha(raw))
os.chdir(tools_dir)
sys.path.insert(0, str(tools_dir))
R = load_module("render", tools_dir / "render.py")
DZ = load_module("alignment_measure_canonical", tools_dir / "对正量.py")
ZD = load_module("word_alignment_canonical", tools_dir / "逐词对齐.py")
assert DZ.门起 == 24 and DZ.阈值 == 4.0 and R.ALIGN_FROM == 24
assert ZD.起 == 26 and ZD.同序起 == 55
assert not ZD.自检(), ZD.自检()
selftest = run([sys.executable, "对正量.py", "--自检"], capture_output=True, text=True)
(OUT / "canonical-selftest.txt").write_text(selftest.stdout + selftest.stderr)
original_measure = DZ.measure
measurement_cache = {}
def measure_cached(data, aligned):
    key = (sha(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()), aligned)
    if key not in measurement_cache:
        measurement_cache[key] = original_measure(data, aligned)
    return measurement_cache[key]
DZ.measure = measure_cached

def add_context(row, data):
    out = dict(row)
    sentence = data["sentences"][int(row["句"]) - 1]
    out["english_sentence"] = " ".join(c["en"] for c in sentence["chunks"])
    return out

def case(no, data):
    started = time.monotonic()
    try:
        rows, other_column, whole_block = DZ.measure(data, None)
        R.apply_script(data)
        enabled = bool(R.ALIGN_RULE[0])
        errors = DZ.gate(no, data)  # actual canonical gate, using cached identical measurements
        over = [row for row in rows if abs(row["偏"]) > DZ.阈值]
        actionable = [add_context(row, data) for row in over if not row["原因"]]
        constrained = [row for row in over if row["原因"]]
        active = int(no) >= DZ.门起
        status = ("historical_alignment_disabled_no_L20_pass_claim" if not active else
                  "fail" if errors else
                  "pass_with_geometry_limits" if constrained else "pass")
        offsets = sorted(abs(row["偏"]) for row in rows)
        return dict(status=status, alignment_enabled=enabled, L20_gate_applies=active,
                    L20_gate_errors=errors, measured_key_pairs=len(rows),
                    abs_offset_mean_1080p=round(sum(offsets)/len(offsets), 3) if offsets else None,
                    abs_offset_median_1080p=offsets[len(offsets)//2] if offsets else None,
                    abs_offset_max_1080p=offsets[-1] if offsets else None,
                    pairs_over_4px=len(over), actionable_over_4px=actionable if active else [],
                    historical_over_4px=over if not active else [],
                    geometry_limited_over_4px=constrained if active else [],
                    canonical_unmeasured_other_column=other_column,
                    canonical_unmeasured_whole_block=whole_block,
                    measured_pairs=rows, elapsed_seconds=round(time.monotonic()-started, 3))
    except (Exception, SystemExit) as exc:
        return dict(status="canonical_layout_exception", L20_gate_applies=int(no) >= DZ.门起,
                    error_type=type(exc).__name__, error=str(exc),
                    traceback=traceback.format_exc(), elapsed_seconds=round(time.monotonic()-started, 3))

def group_item(data, si, en, zh, words=None, why=None):
    key = ZD.键(si, en)
    confirmations = data.get("核对确认", {}).get("合组", {})
    reason = confirmations.get(key, "") or confirmations.get(ZD.旧键(si, en), "")
    return dict(sentence=si, english=en, chinese=zh, words=words, why=why,
                canonical_key=key, documented_unsplittable=bool(re.match(r"^对齐不了[：:].{4,}", reason)),
                explanation=reason)

report = dict(
    source_sha=SOURCE, kind="read-only-script-layout-and-grouping-audit",
    rules=dict(L20_start=24, L20_threshold_1080p_px=4, L20_scope="24–70; 01–23 historically disabled, no pass claim",
               G47_start=26, G47_scope="26–70; 01–25 historical inventory only",
               T39_K128_start=55, T39_K128_severity="canonical warning only",
               limits="Canonical measure skips cross-column and whole-block pairs; these counts are reported, never silently treated as measured passes."),
    provenance_sha256=provenance, registry_version=registry["版本"],
    canonical_selftests_passed=True, articles=[])
video_paths = run(["git", "-c", "core.quotepath=off", "ls-tree", "-rz", "--name-only",
                   SOURCE, "--", "最终版4K视频"], cwd=ROOT, capture_output=True).stdout.decode().split("\0")
for no, (data, original_sha) in documents.items():
    detached = copy.deepcopy(data)
    last = detached["sentences"][-1]["chunks"][-1]
    old_note = last.get("note")
    # Use the newly fixed canonical entry point, including its narrowly scoped
    # removal of an obsolete final-summary "整屏" approval.
    summary = R.拆出简述页(detached)
    final_key = f"S{len(data['sentences'])}"
    old_approval = data.get("说明放宽特批", {})
    new_approval = detached.get("说明放宽特批", {})
    approval_removed = old_approval != new_approval
    if approval_removed:
        assert summary and old_approval.get(final_key, {}).get("倍数") == "整屏"
        expected = copy.deepcopy(old_approval)
        expected.pop(final_key)
        assert new_approval == expected
    # No translation, chunk, align group, line break or audio field may change.
    restored = copy.deepcopy(detached)
    if "note" in data["sentences"][-1]["chunks"][-1]:
        restored["sentences"][-1]["chunks"][-1]["note"] = old_note
    else:
        restored["sentences"][-1]["chunks"][-1].pop("note", None)
    if approval_removed:
        restored["说明放宽特批"] = copy.deepcopy(old_approval)
    assert restored == data
    before = case(no, data)
    after = case(no, detached) if summary else copy.deepcopy(before)
    multi = [group_item(data, si, en, zh, words=words) for si, en, zh, words in ZD.多实词组(data)]
    same = [group_item(data, si, en, zh, why=why) for si, en, zh, why in ZD.同序组(data)]
    item = dict(article=no, title=data["title_zh"], source_script_sha256=original_sha,
                source_4k_video_exists=any(p.startswith("最终版4K视频/" + no + " - ") and p.endswith(".mp4") for p in video_paths),
                original=before, detached_summary_simulation=after,
                summary_was_removed=bool(summary), only_final_note_changed=not approval_removed,
                obsolete_final_summary_approval_removed=approval_removed,
                body_translation_groups_breaks_audio_fields_identical=True,
                G47_gate_applies=int(no) >= ZD.起, G47_gate_errors=ZD.查(data, no),
                multi_content_word_groups=multi,
                T39_K128_warning_applies=int(no) >= ZD.同序起, T39_K128_warnings=ZD.同序(data, no),
                same_order_group_candidates=same)
    if no == "05":
        item["scope_note"] = "Current repository script is a draft without a final4K video; final05 must be re-audited after its own production."
    # Source material and canonical program files were read/copied, never edited.
    assert sha((scripts_dir / f"{no}.json").read_bytes()) == original_sha
    report["articles"].append(item)
    dump(OUT / "report.partial.json", report)
    print(no, before["status"], "=>", after["status"],
          "G47", len(item["G47_gate_errors"]), "T39 warnings", len(item["T39_K128_warnings"]), flush=True)

def totals(variant):
    articles = report["articles"]
    valid = [a for a in articles if a[variant]["status"] != "canonical_layout_exception"]
    active = [a for a in valid if a[variant]["L20_gate_applies"]]
    historical = [a for a in valid if not a[variant]["L20_gate_applies"]]
    return dict(articles=len(articles), measured_articles=len(valid),
                canonical_layout_exceptions=[dict(article=a["article"], error=a[variant]["error"])
                                             for a in articles if a[variant]["status"] == "canonical_layout_exception"],
                L20_applicable_articles=len(active), L20_pass_articles=[a["article"] for a in active if not a[variant]["L20_gate_errors"]],
                L20_fail_articles=[dict(article=a["article"], errors=a[variant]["L20_gate_errors"],
                                       details=a[variant]["actionable_over_4px"]) for a in active if a[variant]["L20_gate_errors"]],
                measured_key_pairs=sum(a[variant]["measured_key_pairs"] for a in valid),
                active_geometry_limited_pairs=sum(len(a[variant]["geometry_limited_over_4px"]) for a in active),
                historical_articles_without_L20_pass_claim=[a["article"] for a in historical],
                historical_pairs_over_4px=sum(len(a[variant]["historical_over_4px"]) for a in historical),
                unmeasured_other_column_pairs=sum(a[variant]["canonical_unmeasured_other_column"] for a in valid),
                unmeasured_whole_block_pairs=sum(a[variant]["canonical_unmeasured_whole_block"] for a in valid))
summary = dict(source_sha=SOURCE, audit_kind=report["kind"], rules=report["rules"],
               original=totals("original"), detached_summary_simulation=totals("detached_summary_simulation"),
               G47_failures=[dict(article=a["article"], errors=a["G47_gate_errors"]) for a in report["articles"] if a["G47_gate_errors"]],
               T39_K128_warnings=[dict(article=a["article"], warnings=a["T39_K128_warnings"]) for a in report["articles"] if a["T39_K128_warnings"]],
               historical_group_inventory=dict(
                   G47_01_to_25_groups=sum(len(a["multi_content_word_groups"]) for a in report["articles"] if int(a["article"]) < ZD.起),
                   same_order_01_to_54_groups=sum(len(a["same_order_group_candidates"]) for a in report["articles"] if int(a["article"]) < ZD.同序起)),
               body_translation_grouping_breaks_audio_modified=False,
               data_audit_only_not_a_pixel_audit_of_all_published_MP4s=True,
               final05_requires_its_own_followup=True,
               obsolete_final_summary_approval_removed_articles=[a["article"] for a in report["articles"] if a["obsolete_final_summary_approval_removed"]])
dump(OUT / "report.json", report)
dump(OUT / "summary.json", summary)
(OUT / "report.partial.json").unlink()
print(json.dumps(summary, ensure_ascii=False), flush=True)
