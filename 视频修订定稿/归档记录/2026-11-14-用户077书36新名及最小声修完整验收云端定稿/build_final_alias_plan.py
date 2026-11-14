"""Plan stable final-video aliases from the actual canonical accepted index.

``build(inventory, canonical_video_tree, catalog=None)`` performs no I/O and
does not modify its arguments. ``canonical_video_tree`` maps paths relative to
视频修订定稿 to ordinary recursive Git-tree entries. ``catalog`` may be the
70-row book-illustrations document, a row list, or a source-id keyed row map.

The caller adds ``video_entries`` (basenames only) to 最终定稿/视频, and writes
``text_files`` relative to 最终定稿. This module never creates Git objects,
updates refs, renders media, selects pending revisions, or publishes Releases.
"""

from collections.abc import Mapping
from copy import deepcopy
import json
import re
import unicodedata


TOTAL = 70
VIDEO_ROOT = "视频修订定稿/"
FINAL_VIDEO_ROOT = "最终定稿/视频/"
_SHA1 = re.compile(r"[0-9a-f]{40}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"(?:0[1-9]|[1-6][0-9]|70)\Z")


class PlanError(ValueError):
    """The supplied canonical inventory cannot safely produce an alias plan."""


def _require(condition, message):
    if not condition:
        raise PlanError(message)


def _identifier(value, label):
    # A strict format also rejects numeric duplicates such as 1 and 01.
    _require(isinstance(value, str) and _ID.fullmatch(value),
             f"{label} must be an exact two-digit ID from 01 to 70")
    return value


def _has_control(value):
    return any(unicodedata.category(c) in {"Cc", "Cf", "Cs"}
               or c in "\u2028\u2029" for c in value)


def _title(value, label="title_zh"):
    _require(isinstance(value, str) and bool(value.strip()), f"{label} is empty")
    _require(not _has_control(value) and "/" not in value and "\\" not in value,
             f"{label} contains a path separator or control character")
    _require(value not in {".", ".."}, f"{label} is unsafe")
    # Do not normalize punctuation, whitespace, or decomposed input silently.
    _require(unicodedata.normalize("NFC", value) == value,
             f"{label} must already be NFC; its original bytes will be preserved")
    return value


def _relative_video_path(value):
    _require(isinstance(value, str) and value.startswith(VIDEO_ROOT),
             "video_repo_path must start with 视频修订定稿/")
    _require(not _has_control(value) and "\\" not in value,
             "video_repo_path contains unsafe characters")
    parts = value.split("/")
    _require(all(p and p not in {".", ".."} for p in parts),
             "video_repo_path contains an empty or traversal component")
    _require(parts[1] != "最终定稿",
             "video_repo_path must refer to an original archive, not a final alias")
    _require(value.endswith(".mp4"), "video_repo_path must name an MP4")
    return value[len(VIDEO_ROOT):]


def _catalog_rows(catalog):
    if isinstance(catalog, list):
        return catalog
    _require(isinstance(catalog, Mapping), "catalog must contain the 70 book rows")
    if "illustrations" in catalog:
        if "count" in catalog:
            _require(type(catalog["count"]) is int and catalog["count"] == TOTAL,
                     "catalog count must be 70")
        return catalog["illustrations"]
    if "articles" in catalog:
        return catalog["articles"]
    rows = []
    for source_id, row in catalog.items():
        _require(isinstance(row, Mapping) and row.get("source_id") == source_id,
                 "catalog map keys must equal the explicit source_id values")
        rows.append(row)
    return rows


def _catalog_index(catalog):
    if catalog is None:
        return None
    rows = _catalog_rows(catalog)
    _require(isinstance(rows, list) and len(rows) == TOTAL,
             "catalog must contain exactly 70 rows")
    by_source, orders = {}, set()
    for row in rows:
        _require(isinstance(row, Mapping), "catalog row must be a mapping")
        sid = _identifier(row.get("source_id"), "catalog source_id")
        nid = _identifier(row.get("new_id"), "catalog new_id")
        title = _title(row.get("title_zh"), "catalog title_zh")
        _require(sid not in by_source and nid not in orders,
                 "catalog source_id and new_id values must each be unique")
        by_source[sid] = {"new_id": nid, "title_zh": title}
        orders.add(nid)
    expected = {f"{n:02d}" for n in range(1, TOTAL + 1)}
    _require(set(by_source) == orders == expected,
             "catalog must be a bijection of all 70 source and book IDs")
    return by_source


def _json(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def _json_block(value):
    raw = _json(value).rstrip("\n")
    # Preserve arbitrary factual notes without allowing embedded fences to end
    # their Markdown block. No editorial explanation is inferred from them.
    longest = max((len(m.group()) for m in re.finditer(r"`+", raw)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}json\n{raw}\n{fence}\n"


def _evidence_pointers(row, canonical_tree):
    result = {"original_video_repo_path": row.get("video_repo_path"),
              "archive_prefix": row.get("archive_prefix"),
              "asset_commit": row.get("asset_commit"),
              "existing_archive_evidence_files": []}
    prefix = row.get("archive_prefix")
    if not isinstance(prefix, str) or not prefix.startswith(VIDEO_ROOT):
        return result
    relative = prefix[len(VIDEO_ROOT):].rstrip("/") + "/"
    names = {"archive-manifest.json", "files-SHA256.json", "archive-handoff.json",
             "original-evidence-bindings.json", "report.json"}
    for path, node in canonical_tree.items():
        if (isinstance(path, str) and path.startswith(relative)
                and path.rsplit("/", 1)[-1] in names
                and isinstance(node, Mapping) and node.get("type") == "blob"
                and node.get("mode") == "100644"):
            result["existing_archive_evidence_files"].append(VIDEO_ROOT + path)
    result["existing_archive_evidence_files"].sort()
    return result


def _changelog(row, planned, canonical_tree):
    content = [f"# {planned['new_id']} {planned['title_zh']}\n",
               "本页照录正式累计清单中的当前版本与历史记录；未记录的修改内容不作推断。\n",
               "## 当前清单版本\n",
               _json_block({"final_alias_path": planned["alias_path"],
                            "existing_git_blob_sha": planned["git_blob_sha"],
                            "inventory_row": row}),
               "## 当前版本依据\n", _json_block(planned["evidence_pointers"]),
               "## 清单保留的较早版本\n"]
    previous = row.get("previous_versions", [])
    if not previous:
        content.append("本行清单未提供较早版本记录。\n")
    for number, version in enumerate(previous, 1):
        content.extend([f"### 原清单历史记录第 {number} 项\n", _json_block(version)])
        if isinstance(version, Mapping):
            content.extend(["该项记录的依据指针：\n",
                            _json_block(_evidence_pointers(version, canonical_tree))])
    return "\n".join(content)


def build(inventory, canonical_video_tree, catalog=None):
    """Return a deterministic alias/text plan, or raise :class:`PlanError`.

    Only ``inventory['articles']`` selects current videos. Historical or pending
    rows never create aliases. Missing source_run metadata is retained as null
    and explicitly listed; no run number is guessed from a path. No source or
    book ID is renumbered to close gaps.
    """
    _require(isinstance(inventory, Mapping), "inventory must be a mapping")
    _require(isinstance(canonical_video_tree, Mapping), "canonical_video_tree must be a mapping")
    rows = inventory.get("articles")
    _require(isinstance(rows, list), "inventory articles must be a list")
    count = inventory.get("archived_passed_count")
    _require(type(count) is int and count == len(rows) and 0 <= count <= TOTAL,
             "archived_passed_count must exactly equal the top-level article count")
    _require(type(inventory.get("requested_total", TOTAL)) is int
             and inventory.get("requested_total", TOTAL) == TOTAL,
             "requested_total must be 70")
    if "remaining_not_claimed_passed" in inventory:
        _require(type(inventory["remaining_not_claimed_passed"]) is int
                 and inventory["remaining_not_claimed_passed"] == TOTAL - count,
                 "remaining_not_claimed_passed disagrees with the article count")
    approved_catalog = _catalog_index(catalog)
    overlay=inventory.get('video_order_overlay')
    video_orders=None
    if overlay is not None:
        from video_order_authorization import validate
        video_orders=validate(overlay,approved_catalog)
    source_ids, order_ids, planned = set(), set(), []
    for row in rows:
        _require(isinstance(row, Mapping), "article row must be a mapping")
        sid = _identifier(row.get("source_id"), "source_id")
        nid = _identifier(row.get("new_id"), "new_id")
        _require(sid not in source_ids, f"duplicate source_id {sid}")
        _require(nid not in order_ids, f"duplicate new_id {nid}")
        source_ids.add(sid)
        order_ids.add(nid)
        _require(row.get("passed_per_article") is True, f"source {sid} is not explicitly passed")
        title = _title(row.get("title_zh"))
        if approved_catalog is not None:
            if approved_catalog[sid] != {"new_id": nid, "title_zh": title}:
                from video_title_authorization import accepted
                accepted(row,approved_catalog[sid])
        size = row.get("bytes")
        _require(type(size) is int and size > 0, f"source {sid} has an invalid byte count")
        _require(isinstance(row.get("sha256"), str) and _SHA256.fullmatch(row["sha256"]),
                 f"source {sid} has an invalid SHA256")
        _require(isinstance(row.get("asset_commit"), str)
                 and _SHA1.fullmatch(row["asset_commit"]), f"source {sid} has an invalid asset_commit")
        relative = _relative_video_path(row.get("video_repo_path"))
        node = canonical_video_tree.get(relative)
        _require(isinstance(node, Mapping), f"source {sid} original video blob is missing")
        _require(node.get("type") == "blob" and node.get("mode") == "100644",
                 f"source {sid} original video must be a 100644 blob")
        _require(type(node.get("size")) is int and node["size"] == size,
                 f"source {sid} original video size differs from the accepted row")
        _require(isinstance(node.get("sha"), str) and _SHA1.fullmatch(node["sha"]),
                 f"source {sid} has an invalid existing Git blob SHA")
        if "git_blob_sha" in row:
            _require(row["git_blob_sha"] == node["sha"], f"source {sid} Git blob SHA disagrees")
        previous = row.get("previous_versions", [])
        _require(isinstance(previous, list), f"source {sid} previous_versions must be a list")
        video_id=video_orders[sid]['video_order'] if video_orders is not None else nid
        basename = f"{video_id} {title}.mp4"
        current = {"source_id": sid, "new_id": video_id, "title_zh": title,
                   "bytes": size, "sha256": row["sha256"],
                   "source_run": deepcopy(row.get("source_run")),
                   "asset_commit": row["asset_commit"],
                   "original_path": row["video_repo_path"],
                   "alias_path": FINAL_VIDEO_ROOT + basename,
                   "git_blob_sha": node["sha"],
                   "previous_versions": deepcopy(previous),
                   "missing_metadata_fields": ["source_run"] if row.get("source_run") is None else [],
                   "evidence_pointers": _evidence_pointers(row, canonical_video_tree),
                   "current_inventory_row": deepcopy(dict(row))}
        if "title_en" in row:
            current["title_en"] = deepcopy(row["title_en"])
        if video_orders is not None:
            current.update(current_video_order=video_id,original_book_order=nid,quality_book_order_unchanged=True,video_order_authority_review_sha256=overlay['authority_review_sha256'])
        planned.append((video_id, basename, current, row))
    planned.sort(key=lambda item: int(item[0]))
    expected = {f"{number:02d}" for number in range(1, TOTAL + 1)}
    missing_source = sorted(expected - source_ids, key=int)
    missing_order = sorted(expected - order_ids, key=int)
    managed_text = ["README.md", "当前清单.json"] + [
        f"修改记录/{basename[:-4]}.md" for _, basename, _, _ in planned]
    if video_orders is not None:managed_text.append('视频顺序.json')
    manifest = {"kind": "validated-video-final-alias-plan-v1",
                "schema_version": 1, "requested_total": TOTAL,
                "current_count": count, "archived_passed_count": count,
                "complete": count == TOTAL,
                "selection": "top_level_canonical_inventory_articles_only",
                "validation_scope": "Existing canonical Git blob identity, mode and size; no new media validation or production",
                "catalog_validated": approved_catalog is not None,
                "missing_source_ids": missing_source,
                "missing_new_ids": missing_order,
                "managed_text_files": managed_text,
                "videos": [item[2] for item in planned]}
    readme = ("# 最终定稿\n\n"
              f"当前正式清单收录已验收视频 {count}/70 篇。视频按书中篇号排列，文件名保留原篇号与标题；尚缺的篇号保持空缺。\n\n"
              "视频目录中的文件引用正式归档中已有的同一 Git blob。原归档与较早版本继续保留，逐篇依据及历史见修改记录。\n\n"
              f"未收录的原始文章编号：{'、'.join(missing_source) or '无'}。\n\n"
              f"未收录的书中篇号：{'、'.join(missing_order) or '无'}。\n\n"
              "原始文章编号与书中篇号是两套对应编号，缺号不互相替代。本目录不包含待验收或待批准的新版本。\n")
    if video_orders is not None:
        manifest.update(video_order_overlay=deepcopy(overlay),new_id_role_in_this_video_manifest='current_video_order',original_book_order_field='original_book_order',missing_frozen_book_orders=deepcopy(missing_order))
        manifest['missing_new_ids']=sorted(expected-{item[0] for item in planned},key=int)
        readme=("# 最终定稿\n\n"+f"当前正式清单收录已验收视频 {count}/70 篇，按用户090确认的视频顺序排列。当前视频序号与原书序分别记录；原书、PDF和历史质量记录不重新编号。\n\n"+"视频文件引用实际验收归档中已有的同一 Git blob，旧版继续保留。当前视频顺序见视频顺序.json，逐篇依据见修改记录。\n\n"+f"未收录的当前视频序号：{'、'.join(manifest['missing_new_ids']) or '无'}。\n")
    text_files = {"README.md": readme, "当前清单.json": _json(manifest)}
    if video_orders is not None:text_files['视频顺序.json']=_json(overlay)
    for nid, basename, current, row in planned:
        text_files[f"修改记录/{basename[:-4]}.md"] = _changelog(row, current, canonical_video_tree)
    video_entries = [{"path": basename, "mode": "100644", "type": "blob", "sha": current["git_blob_sha"]}
                     for _, basename, current, _ in planned]
    return {"video_entries": video_entries, "text_files": text_files, "manifest": manifest}
