"""User-requested article 05 keyword-only changes. Does not modify audio inputs."""
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

REQUEST = {
    "original_article": "05",
    "playback_number": "09",
    "title_zh": "血里的指纹",
    "title_en": "The Fingerprint in the Blood",
    "highlight_additions": ["screening", "baker", "co-worker (second occurrence)", "convicted of"],
    "pdf": "deferred: waiting for user layout feedback; do not rebuild PDFs",
    "article01_footnote": "proposal only; await user acceptance before rendering article01",
}

def visible(text):
    return re.sub(r"\*\*([^*]+)\*\*\([^)]*\)", r"\1", text).replace("**", "")

def apply(data, root, work, output, status):
    old = copy.deepcopy(data)
    changes = [
        (11, 1, "DNA screening,", "DNA **screening**,", "DNA筛查，", "DNA**筛查**(screening)，"),
        (13, 0, "a local baker,", "a local **baker**,", "一名当地的面包师，", "一名当地的**面包师**(baker)，"),
        (14, 1, "the co-worker", "the **co-worker**", "这名同事", "这名**同事**(co-worker)"),
        (16, 2, "convicted of", "**convicted of**", "被判谋杀罪", "**被判**(convicted of)谋杀**罪**(convicted of)"),
    ]
    rows = []
    literal_changes = []
    for si, ci, a, b, z, zz in changes:
        c = data["sentences"][si]["chunks"][ci]
        assert c["en"].count(a) == 1 and c["zh"].count(z) == 1, (si, ci, c)
        c["en"] = c["en"].replace(a, b)
        c["zh"] = c["zh"].replace(z, zz)
        count = 0
        for pair in c["align"]:
            if a in pair[0]:
                assert z in pair[1], (si, ci, pair)
                before_pair = list(pair)
                pair[0] = pair[0].replace(a, b)
                pair[1] = pair[1].replace(z, zz)
                literal_changes.extend(zip(before_pair, pair))
                count += 1
        assert count == 1
        rows.append({"sentence": si + 1, "chunk": ci + 1, "english": b, "chinese": zz})
    for os, ns in zip(old["sentences"], data["sentences"]):
        assert os["para"] == ns["para"] and len(os["chunks"]) == len(ns["chunks"])
        for oc, nc in zip(os["chunks"], ns["chunks"]):
            for key in ("en", "zh"):
                assert visible(oc[key]) == visible(nc[key]), (key, oc, nc)
            assert oc.get("note") == nc.get("note")
            assert len(oc["align"]) == len(nc["align"])
            for op, np in zip(oc["align"], nc["align"]):
                assert list(map(visible, op)) == list(map(visible, np))
    # Preserve gen05 as the authoritative data source, using precisely the same pairs.
    gen = root / "视频/工具/初稿生成/gen05.py"
    source = gen.read_text()
    for before_literal, after_literal in literal_changes:
        before_token = json.dumps(before_literal, ensure_ascii=False)
        after_token = json.dumps(after_literal, ensure_ascii=False)
        assert source.count(before_token) == 1, (before_literal, source.count(before_token))
        source = source.replace(before_token, after_token)
    gen.write_text(source)
    # Add full lexical definitions required by the existing article synchronizer.
    article = root / "新版定稿/05-the-fingerprint-in-the-blood.md"
    text = article.read_text()
    definitions = [
        ("screening", "n. 筛查；筛选（screen 的名词形式；DNA screening：DNA筛查）", "4"),
        ("baker", "n. 面包师，烘焙师", "4"),
        ("convicted of", "v. (convict sb of sth 的被动形式) 被判……罪（be convicted of murder：被判谋杀罪）", "5"),
    ]
    for word, meaning, para in definitions:
        if not re.search(r"^\| " + re.escape(word) + r" \|", text, re.M):
            marker = "\n## 史实与来源"
            assert marker in text
            text = text.replace(marker, f"| {word} | {meaning} | {para} |\n" + marker, 1)
    article.write_text(text)
    # Record the current explicit instruction as the existing finalizer requires.
    approvals = root / "视频/工具/用户同意记录.json"
    authorization = json.loads(approvals.read_text())
    authorization["记录"].append({
        "篇": "05", "日期": "2026-11-13",
        "原话": "视频可以先重新生成，视频可以先重新生成一下，就是把那几个重点词汇标注一下，标注一下。",
        "用于": "第05篇定稿：screening、baker、co-worker第二次出现、convicted of；只改重点词标注，PDF暂缓",
        "来源": "2026-11-13 当前会话，用户提供四处截图后明确要求先重做视频",
    })
    approvals.write_text(json.dumps(authorization, ensure_ascii=False, indent=2) + "\n")
    status["requested_keyword_changes"] = rows
    status["visible_body_and_grouping_unchanged"] = True
    status["pdf_rebuilt"] = False
    (output / "keyword-request.json").write_text(json.dumps(REQUEST, ensure_ascii=False, indent=2) + "\n")

def export(root, work, output, status):
    assert status["passed"] and status["voice_unchanged"]
    assert status["video_frames"] == 4483
    old = output / "05-4K-读完即转简述2秒.mp4"
    new = output / "09 血里的指纹 The Fingerprint in the Blood.mp4"
    old.rename(new)
    # Compare the accepted source audio hash: no models, raw audio or GT leave Actions.
    audio = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(new), "-map", "0:a:0", "-c:a", "copy", "-f", "hash", "-hash", "sha256", "-"
    ], text=True).strip()
    assert audio == "SHA256=bcd2beed53991673332a36c89646629c55a596d4f97e329d869d53ef5cf3b368", audio
    status["accepted_previous_audio_bit_identical"] = True
    status["accepted_audio_sha256"] = audio.split("=", 1)[1]
    status["filename"] = new.name
    sources = output / "sources"
    sources.mkdir(exist_ok=True)
    for src, dst in [
        (work / "scripts/05.json", "05.json"),
        (root / "视频/工具/初稿生成/gen05.py", "gen05.py"),
        (root / "新版定稿/05-the-fingerprint-in-the-blood.md", "05-the-fingerprint-in-the-blood.md"),
        (root / "视频/工具/用户同意记录.json", "用户同意记录.json"),
    ]:
        shutil.copy2(src, sources / dst)
    status["source_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources.iterdir()}

