#!/usr/bin/env python3
"""Read-only scan of publication PDFs in their stored default OCG state.

Usage:
  python qa_visible_language.py BOOK.pdf CHAPTER.pdf --out language-qa.json \
      --preview-list visual-review-pages.json

No PDF, layer configuration, source text or metadata is changed. The scan reads
extractable visible text; rasterized text requires the separate visual review
for which this script supplies candidate page numbers. An overall pass requires
no remaining template findings, and the specified provenance OCG must exist
exactly once and be explicitly default-off. A clean text scan is not a visual
or pixel-preservation approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

try:
    import pymupdf as fitz
except ImportError:
    import fitz


LAYER_NAME = "来源署名｜朋克英语"

# Match complete editorial / software templates. Ordinary story words such as
# 请、制作、程序、生成 are deliberately NOT forbidden. Regexes run on the exact
# extracted string, not a cleaned string, and reports retain original matches.
RULE_SPECS = (
    ("booklet_label", "blocking", r"阅读小册"),
    ("reordering_process_label", "blocking", r"新顺序(?:版|合订本|目录)?"),
    ("click_navigation_instruction", "blocking", r"点击\s*(?:目录|篇目|篇名|章节|条目|即可|可跳转)[^\n。；]{0,50}"),
    ("renumbering_process_instruction", "blocking", r"篇号\s*已按[^。\n]{0,100}"),
    ("renumbering_process_instruction", "blocking", r"按新篇号\s*[0-9０-９]{1,2}\s*[—–－-]\s*[0-9０-９]{1,2}[^。\n]{0,50}"),
    ("content_sequence_instruction", "blocking", r"每篇依次包含[^。；]{0,140}"),
    ("reading_order_instruction", "blocking", r"按推荐顺序阅读[^。\n]{0,60}"),
    ("old_number_instruction", "blocking", r"保留原篇号"),
    ("memorization_instruction", "blocking", r"先记这\s*[0-9０-９一二三四五六七八九十百]+\s*项[^。\n]{0,80}"),
    ("memorization_instruction", "blocking", r"连着下方的原文短语一起回想"),
    ("vocabulary_template_instruction", "blocking", r"(?:补充词汇共|补齐另外)\s*[0-9０-９一二三四五六七八九十百]+\s*项(?:。\s*(?:这里)?保留每个表达在本文中的意思。?)?"),
    ("vocabulary_template_instruction", "blocking", r"(?:这里)?保留每个表达在本文中的意思"),
    ("answer_cover_instruction", "blocking", r"先遮住(?:下方)?答案[^。\n]{0,100}"),
    ("production_note", "blocking", r"(?:制作说明|生成器(?:式)?模板|生成器说明|生成器提示|排版说明|制作流程|生成流程|工作流程说明)"),
    ("placeholder_text", "blocking", r"(?:占位(?:文字|文本|内容|图片|图|页|符)|示例文本|待填(?:写|充)|Lorem\s+ipsum)"),
    ("placeholder_marker", "blocking", r"(?im)^\s*(?:TODO|TBD|PLACEHOLDER)\b[^\n]{0,100}"),
    # This is repeated generic series furniture, not an approved cover title.
    # It is reported for human review without conflating it with story content.
    ("generic_template_banner", "review", r"(?m)^\s*STORIES TO READ AND REMEMBER\s*$"),
)
RULES = [(kind, severity, re.compile(pattern)) for kind, severity, pattern in RULE_SPECS]
WORKFLOW_HEADER = re.compile(r"^(?:(?:0?[1-4])\s*[/｜|·—–-]\s*)?(?:READ|CHECK|LEARN|RECALL)$", re.I)
WORKFLOW_CN_HEADER = re.compile(r"^(?:纯净阅读|中文核对|词汇记忆|回想巩固)$")
STRUCTURAL_PRODUCTION = re.compile(r"^(?:制作说明|生成器|排版(?:说明|占位)|占位(?:文字|文本|内容|图|页|符)?)(?:\s|[：:·｜|/]|$)")
PAGE_TYPES = ("目录", "英文原文", "中文译文", "核心词汇", "文中词汇与搭配", "回想与回顾", "文章主线", "注释")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def exact_snippet(text: str, start: int, end: int, radius: int = 70):
    low, high = max(0, start - radius), min(len(text), end + radius)
    return text[low:high], [low, high]


def scan_text(text: str):
    """Pure text rules, exposed separately for simple positive/negative checks."""
    findings = []
    for kind, severity, pattern in RULES:
        for match in pattern.finditer(text):
            snippet, snippet_range = exact_snippet(text, *match.span())
            findings.append({"type": kind, "severity": severity, "matched_text": match.group(0),
                             "text_snippet": snippet, "match_char_range": list(match.span()),
                             "snippet_char_range": snippet_range,
                             "extracted_line_1based": text.count("\n", 0, match.start()) + 1})
    return findings


def structural_findings(page):
    """Only treat workflow words as furniture in top/bottom page regions.

    A normal story sentence containing 'read' or a software story mentioning a
    generator is therefore not forbidden by the structural vocabulary rules.
    """
    findings = []
    height = float(page.rect.height)
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            original = "".join(span["text"] for span in line.get("spans", []))
            value = original.strip()
            box = list(line["bbox"])
            structural = box[1] < height * .23 or box[3] > height * .74
            if not structural:
                continue
            if WORKFLOW_HEADER.fullmatch(value) or WORKFLOW_CN_HEADER.fullmatch(value):
                kind = "workflow_section_furniture"
            elif STRUCTURAL_PRODUCTION.match(value):
                kind = "structural_production_or_placeholder_label"
            else:
                continue
            findings.append({"type": kind, "severity": "blocking", "matched_text": original,
                             "text_snippet": original, "bbox_points": box,
                             "structural_region": "header" if box[1] < height * .23 else "footer"})
    return findings


def ocg_state(doc):
    groups = doc.get_ocgs()
    configuration = doc.get_layer(-1) if groups else {}
    ui = list(doc.layer_ui_configs()) if groups else []
    matches = [(xref, value) for xref, value in groups.items() if value.get("name") == LAYER_NAME]
    on = set(configuration.get("on", []))
    off = set(configuration.get("off", []))
    hidden = len(matches) == 1 and matches[0][0] in off and matches[0][0] not in on and matches[0][1].get("on") is False
    return {
        "read_in_stored_default_state_without_layer_mutation": True,
        "configuration": configuration,
        "all_groups": [{"xref": xref, "name": value.get("name"), "default_on": value.get("on"),
                        "explicitly_default_on": xref in on, "explicitly_default_off": xref in off}
                       for xref, value in groups.items()],
        "layer_ui_configs": ui,
        "actual_visible_layer": {"expected_name": LAYER_NAME, "matching_group_count": len(matches),
                                 "default_hidden": bool(hidden),
                                 "default_closed_as_required": bool(hidden)},
    }


def scan_pdf(path: Path, preview_limit: int = 40):
    record = {"path": str(path.resolve()), "source_sha256": sha256(path), "findings": [],
              "text_extraction_only_no_OCR": True, "pdf_modified": False}
    candidates = {}
    def recommend(number, reason, priority):
        candidate = candidates.setdefault(number, {"page": number, "reasons": [], "priority": priority})
        if reason not in candidate["reasons"]:
            candidate["reasons"].append(reason)
        candidate["priority"] = max(candidate["priority"], priority)
    with fitz.open(path) as doc:
        record["pages"] = len(doc)
        record["default_OCG_state"] = ocg_state(doc)
        representative = {}
        page_hashes = []
        for index, page in enumerate(doc):
            number = index + 1
            text = page.get_text("text")
            page_hashes.append(hashlib.sha256(text.encode("utf-8")).hexdigest())
            findings = scan_text(text) + structural_findings(page)
            for finding in findings:
                finding["page"] = number
                record["findings"].append(finding)
                recommend(number, finding["type"], 100 if finding["severity"] == "blocking" else 70)
            if index < 3:
                recommend(number, "front_matter_or_first_pages", 50)
            if not text.strip():
                recommend(number, "no_extractable_text_requires_image_review", 90)
            for page_type in PAGE_TYPES:
                if page_type in text and page_type not in representative:
                    representative[page_type] = number
                    recommend(number, "representative_type:" + page_type, 45)
        if len(doc):
            recommend(len(doc), "last_page", 40)
        record["default_visible_text_sha256_by_page"] = page_hashes
        record["representative_page_types"] = representative
    record["source_sha256_after_read"] = sha256(path)
    record["source_unchanged"] = record["source_sha256"] == record["source_sha256_after_read"]
    record["findings_by_type"] = dict(Counter(f["type"] for f in record["findings"]))
    record["blocking_findings"] = sum(f["severity"] == "blocking" for f in record["findings"])
    record["review_findings"] = sum(f["severity"] == "review" for f in record["findings"])
    record["no_blocking_language_findings"] = record["blocking_findings"] == 0
    record["visible_language_passed"] = not record["findings"]
    record["attribution_state_passed"] = record["default_OCG_state"]["actual_visible_layer"]["default_hidden"]
    record["passed"] = record["source_unchanged"] and record["visible_language_passed"] and record["attribution_state_passed"]
    record["preview_candidates"] = sorted(candidates.values(), key=lambda p: (-p["priority"], p["page"]))[:preview_limit]
    record["preview_candidate_count_before_limit"] = len(candidates)
    return record


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".language-qa.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path, help="JSON report; never a PDF path.")
    parser.add_argument("--preview-list", type=Path, help="Optional separate JSON list of pages for visual review; no images are rendered.")
    parser.add_argument("--preview-limit", type=int, default=40, help="Maximum suggested visual-review pages per file; all pages are scanned.")
    args = parser.parse_args(argv)
    if args.preview_limit < 1:
        parser.error("--preview-limit must be positive")
    inputs = list(dict.fromkeys(p.resolve() for p in args.pdfs))
    for output in (args.out, args.preview_list):
        if output and (output.suffix.lower() != ".json" or output.resolve() in inputs):
            parser.error("Outputs must be separate .json files and cannot overwrite an input PDF.")
    if args.preview_list and args.preview_list.resolve() == args.out.resolve():
        parser.error("--preview-list and --out must be different JSON files")
    report = {"schema_version": 1, "purpose": "Formal-print visible-language and default-hidden attribution audit",
              "created_utc": datetime.now(timezone.utc).isoformat(),
              "scanner_sha256": sha256(Path(__file__)), "expected_attribution_layer": LAYER_NAME,
              "pdf_or_source_mutation": False, "default_OCG_state_not_changed": True,
              "text_extraction_only_no_OCR": True,
              "ordinary_story_words_not_forbidden": ["请", "制作", "程序", "生成"],
              "rules": [{"type": kind, "severity": severity, "regex": pattern} for kind, severity, pattern in RULE_SPECS],
              "files": [], "errors": []}
    for path in inputs:
        try:
            if path.suffix.lower() != ".pdf" or not path.is_file():
                raise ValueError("Input must be an existing PDF file")
            record = scan_pdf(path, args.preview_limit)
            report["files"].append(record)
        except Exception as error:
            report["errors"].append({"path": str(path), "type": type(error).__name__, "message": str(error)})
    report["file_count"] = len(report["files"])
    report["blocking_findings"] = sum(r["blocking_findings"] for r in report["files"])
    report["review_findings"] = sum(r["review_findings"] for r in report["files"])
    report["passed"] = not report["errors"] and len(report["files"]) == len(inputs) and all(r["passed"] for r in report["files"])
    write_json(args.out, report)
    if args.preview_list:
        write_json(args.preview_list, {"schema_version": 1, "images_rendered": False,
            "requires_actual_visual_review": True,
            "files": [{"path": r["path"], "source_sha256": r["source_sha256"],
                       "pages": r["preview_candidates"], "page_count": r["pages"]} for r in report["files"]]})
    print(json.dumps({"out": str(args.out), "files": report["file_count"],
                      "blocking_findings": report["blocking_findings"], "review_findings": report["review_findings"],
                      "errors": len(report["errors"]), "passed": report["passed"]}, ensure_ascii=False))
    return 2 if report["errors"] else 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
