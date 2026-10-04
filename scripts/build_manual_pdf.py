"""生成《声音分身 VoiceTwin 使用手册》PDF。

把 docs/manual/src/*.html 按文件名顺序拼成一个完整网页，自动生成目录（带页码和跳转链接），
再用 Chromium 打印成 A4 PDF（带书签、页眉页脚），输出到 docs/声音分身VoiceTwin使用手册.pdf。

加 --quickstart 时改为把根目录的《快速上手.md》打印成一页纸的 docs/快速上手.pdf。

用法（维护者在 Linux 上运行）：
    pip install playwright pypdf fonttools markdown-it-py mdit-py-plugins
    python scripts/build_manual_pdf.py [--chromium /opt/pw-browsers/chromium] [--html-only] [--quickstart]

需要系统里有 Noto Sans CJK SC 字体（Regular / Medium / Bold）和 Noto Color Emoji。
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "manual" / "src"
BUILD = ROOT / "docs" / "manual" / "build"
OUT = ROOT / "docs" / "声音分身VoiceTwin使用手册.pdf"
TITLE = "声音分身 VoiceTwin 使用手册"
QUICK_MD = ROOT / "快速上手.md"
QUICK_OUT = ROOT / "docs" / "快速上手.pdf"
QUICK_TITLE = "声音分身 VoiceTwin 快速上手"
# 快速上手的打印样式（在 build_windows_release.markdown_to_html 的网页样式基础上调整）
QUICK_PRINT_CSS = """
  @page { size: A4; margin: 14mm 15mm 15mm;
    @bottom-center { content: "声音分身 VoiceTwin 快速上手 · 第 " counter(page) " 页 / 共 " counter(pages) " 页";
                     font-family: "Noto Sans CJK SC", sans-serif; font-size: 8.5pt; color: #8a94a6; } }
  body { font-family: "Noto Sans CJK SC", sans-serif; font-size: 11pt; line-height: 1.7; }
  main { max-width: none; padding: 0; }
  h1 { font-size: 21pt; color: #0f2a55; border-bottom: 3px solid #1f5fbf; margin-top: 0; }
  h2 { font-size: 15pt; color: #10284f; margin-top: 1.3em; break-after: avoid; }
  h2 + p, p:has(> strong:first-child) { break-after: avoid; }
  hr { display: none; }
  p:has(> img) { break-inside: avoid; margin: .5em 0 .9em; }
  img { box-shadow: 0 1px 5px rgba(20, 40, 80, .12); }
  blockquote, tr, li, ol, ul { break-inside: avoid; }
  table { display: table; font-size: 10pt; }
  code { font-family: "DejaVu Sans Mono", "Noto Sans CJK SC", monospace; }
"""

HEADING_RE = re.compile(r'<h([1-3])\b([^>]*)>(.*?)</h\1>', re.S)
ID_RE = re.compile(r'\bid="([^"]+)"')
FONT_WEIGHTS = {"Regular": 400, "Medium": 500, "Bold": 700}
# Chromium 生成 PDF 时，会把"一、生、用、长……"这些字的 ToUnicode 映射到同形的部首码位（U+2E80~U+2FDF），
# 导致 PDF 里搜索、复制中文出错。去掉字体 cmap 里这两个部首区块即可。
RADICAL_BLOCKS = (0x2E80, 0x2FDF)


# ----------------------------------------------------------------------------- HTML
def text_of(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def headings(body: str) -> List[Dict[str, str]]:
    """文档里所有 h1~h3（按顺序），用于目录和对照 PDF 书签。"""
    out = []
    for m in HEADING_RE.finditer(body):
        level, attrs, inner = int(m.group(1)), m.group(2), m.group(3)
        hid = ID_RE.search(attrs)
        no = re.search(r'<span class="no">(.*?)</span>', inner, re.S)
        title = re.sub(r'<span class="no">.*?</span>', "", inner, flags=re.S)
        out.append({"level": level, "id": hid.group(1) if hid else "", "no": text_of(no.group(1)) if no else "",
                    "title": text_of(title), "full": text_of(inner)})
    return out


def toc_html(entries: List[Dict[str, str]], pages: Dict[str, int]) -> str:
    rows = ['<section class="toc">', '<h1 id="toc">目录</h1>']
    section = ""
    for e in entries:
        if not e["id"] or e["level"] > 2:
            continue
        if e["level"] == 1:
            section = e["id"]
        elif section == "preface":      # "写在前面"的小节不进目录
            continue
        label = f'{e["no"]}　{e["title"]}' if e["no"] else e["title"]
        pg = pages.get(e["id"])
        rows.append(f'<div class="l{e["level"]}"><a href="#{e["id"]}"><span>{html.escape(label)}</span>'
                    f'<span class="dots"></span><span class="pg">{pg if pg else "—"}</span></a></div>')
    rows.append("</section>")
    return "\n".join(rows)


def assemble(pages: Dict[str, int], font_css: str) -> Tuple[str, List[Dict[str, str]]]:
    parts = sorted(SRC.glob("*.html"))
    if not parts:
        raise SystemExit(f"找不到手册源文件：{SRC}")
    doc = "\n".join(p.read_text(encoding="utf-8") for p in parts)
    if "<!--TOC-->" not in doc:
        raise SystemExit("手册源文件里缺少 <!--TOC--> 标记")
    body_entries = headings(doc)
    doc = doc.replace("<!--TOC-->", toc_html(body_entries, pages), 1)
    doc = doc.replace("</style>", font_css + "\n</style>", 1)
    # 表格第一行是表头时放进 <thead>：跨页时每页自动重复表头，也不会孤零零地留在页底
    doc = re.sub(r'(<table class="t[^"]*"[^>]*>\s*)(<tr>(?:\s*<th\b[^>]*>(?:(?!</th>|<td\b|</?tr\b).)*</th>)+\s*</tr>)',
                 r"\1<thead>\2</thead>", doc, flags=re.S)
    # 很长的行内命令允许换行，避免超出页面
    doc = re.sub(r"<code>((?:(?!</code>).)*)</code>",
                 lambda m: f'<code class="long">{m.group(1)}</code>' if len(text_of(m.group(1))) > 26 else m.group(0),
                 doc, flags=re.S)
    doc = re.sub(r'<span class="path">([^<]*)</span>',
                 lambda m: f'<span class="path long">{m.group(1)}</span>' if len(m.group(1)) > 30 else m.group(0), doc)
    return doc, headings(doc)


# ----------------------------------------------------------------------------- 字体
def find_font(style: str) -> Optional[Path]:
    fc = shutil.which("fc-match")
    if fc:
        try:
            out = subprocess.run([fc, "-f", "%{file}", f"Noto Sans CJK SC:style={style}"], capture_output=True, text=True,
                                 timeout=20).stdout.strip()
            if out and "CJK" in out and Path(out).exists():
                return Path(out)
        except Exception:
            pass
    for d in (Path.home() / ".fonts", Path("/usr/share/fonts"), Path("/usr/local/share/fonts")):
        hits = sorted(d.rglob(f"NotoSansCJK*{style}*.[ot]t[fc]")) if d.exists() else []
        if hits:
            return hits[0]
    return None


def patched_fonts() -> str:
    """把 Noto Sans CJK SC 去掉部首区块后放进 build/fonts，返回覆盖同名字体的 @font-face。"""
    try:
        from fontTools.ttLib import TTCollection, TTFont
    except ImportError:
        print("⚠️ 未安装 fonttools，PDF 里的部分汉字将无法正确搜索/复制（pip install fonttools）")
        return ""
    font_dir = BUILD / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)
    rules = []
    for style, weight in FONT_WEIGHTS.items():
        src = find_font(style)
        if not src:
            print(f"⚠️ 没有找到 Noto Sans CJK SC {style}，将使用系统字体")
            continue
        dst = font_dir / f"VT-NotoSansCJKsc-{style}.otf"
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            print(f"处理字体 {src.name}（只需一次，约 20 秒）……")
            if src.suffix.lower() == ".ttc":
                coll = TTCollection(str(src))
                font = next((f for f in coll.fonts if "SC" in f["name"].getDebugName(1)), coll.fonts[0])
            else:
                font = TTFont(str(src))
            lo, hi = RADICAL_BLOCKS
            for table in font["cmap"].tables:
                if table.isUnicode():
                    for cp in [c for c in table.cmap if lo <= c <= hi]:
                        del table.cmap[cp]
            font.save(str(dst))
        rules.append(f'  @font-face {{ font-family: "Noto Sans CJK SC"; font-weight: {weight}; '
                     f'src: url("fonts/{dst.name}"); }}')
    if rules:  # 没有单独的 Medium 时，600 也映射到 Bold
        rules.append(rules[-1].replace(f"font-weight: {FONT_WEIGHTS['Bold']}", "font-weight: 600"))
    return "\n".join(rules)


# ----------------------------------------------------------------------------- PDF
CONTENT_WIDTH_PX = round((210 - 16 * 2) / 25.4 * 96)   # A4 宽度减去左右页边距（与 00_head.html 的 @page 一致）
OVERFLOW_JS = """() => {
  const out = [];
  for (const el of document.querySelectorAll('code, .path, .ui, .btn, .tab, .key, pre, img, .console, table')) {
    const box = (el.parentElement && el.parentElement.closest('td, th')) || document.body;
    if (el.getBoundingClientRect().right > box.getBoundingClientRect().right + 1) out.push(el.textContent.trim().slice(0, 60));
  }
  return out;
}"""
def render(html_path: Path, pdf_path: Path, chromium: Optional[str]) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium) if chromium else p.chromium.launch()
        page = browser.new_page(viewport={"width": CONTENT_WIDTH_PX, "height": 1000})
        page.emulate_media(media="print")
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        for item in page.evaluate(OVERFLOW_JS):
            print(f"⚠️ 内容超出边界：{item}")
        page.pdf(path=str(pdf_path), prefer_css_page_size=True, print_background=True, outline=True, tagged=True)
        browser.close()


def outline_pages(pdf_path: Path, entries: List[Dict[str, str]]) -> Dict[str, int]:
    """读取 PDF 书签，按顺序对应到各个标题，得到每个标题所在的页码（从 1 开始，和页脚一致）。"""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    flat: List[Tuple[str, int]] = []

    def walk(items) -> None:
        for it in items:
            if isinstance(it, list):
                walk(it)
            else:
                flat.append((re.sub(r"\s+", "", it.title or ""), reader.get_destination_page_number(it) + 1))

    walk(reader.outline)
    pages: Dict[str, int] = {}
    i = 0
    for e in entries:
        want = re.sub(r"\s+", "", e["full"])
        j = i
        while j < len(flat) and flat[j][0] != want:
            j += 1
        if j < len(flat):
            if e["id"]:
                pages[e["id"]] = flat[j][1]
            i = j + 1
    return pages


def finalize(pdf_path: Path, out: Path, title: str = TITLE) -> None:
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter(clone_from=PdfReader(str(pdf_path)))
    writer.add_metadata({"/Title": title, "/Author": "VoiceTwin 声音分身", "/Subject": "声音分身 VoiceTwin 详细图文使用教程（Windows）",
                         "/Keywords": "VoiceTwin, 声音分身, 声音克隆, GPT-SoVITS, 讲课, 教程"})
    writer.page_mode = "/UseOutlines"   # 打开 PDF 时显示书签栏
    with open(out, "wb") as f:
        writer.write(f)


def build_quickstart(out: Path, font_css: str, chromium: Optional[str], html_only: bool) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_windows_release import markdown_to_html

    doc = markdown_to_html(QUICK_MD.read_text(encoding="utf-8"), QUICK_TITLE, embed_images=True,
                           extra_css=font_css + QUICK_PRINT_CSS)
    html_path = BUILD / "quickstart.html"
    html_path.write_text(doc, encoding="utf-8")
    if html_only:
        print(f"✅ {html_path}")
        return
    tmp = BUILD / "quickstart.pdf"
    render(html_path, tmp, chromium)
    out.parent.mkdir(parents=True, exist_ok=True)
    finalize(tmp, out, QUICK_TITLE)
    from pypdf import PdfReader

    print(f"✅ {out}（{len(PdfReader(str(out)).pages)} 页，{out.stat().st_size / 1024 / 1024:.1f} MB）")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chromium", help="Chromium 可执行文件（默认用 Playwright 自带的）")
    ap.add_argument("--html-only", action="store_true", help="只生成 HTML，不打印 PDF")
    ap.add_argument("--quickstart", action="store_true", help="生成一页纸的《快速上手》PDF（docs/快速上手.pdf）")
    ap.add_argument("-o", "--output", default="")
    args = ap.parse_args()

    BUILD.mkdir(parents=True, exist_ok=True)
    font_css = patched_fonts()
    if args.quickstart:
        build_quickstart(Path(args.output or QUICK_OUT), font_css, args.chromium, args.html_only)
        return
    args.output = args.output or str(OUT)
    html_path = BUILD / "manual.html"
    doc, entries = assemble({}, font_css)
    html_path.write_text(doc, encoding="utf-8")
    if args.html_only:
        print(f"✅ {html_path}")
        return

    # 第一遍：目录页码先留空，打印后从书签里读出每个标题的页码；第二遍填上页码再打印
    first = BUILD / "pass1.pdf"
    render(html_path, first, args.chromium)
    pages = outline_pages(first, entries)
    missing = [e["full"] for e in entries if e["id"] and e["level"] <= 2 and e["id"] not in pages]
    if missing:
        print("⚠️ 这些标题没有在书签里找到页码：" + "；".join(missing[:10]))
    doc, entries = assemble(pages, font_css)
    html_path.write_text(doc, encoding="utf-8")
    second = BUILD / "pass2.pdf"
    render(html_path, second, args.chromium)
    check = outline_pages(second, entries)
    moved = [k for k, v in pages.items() if check.get(k) != v]
    if moved:  # 目录行数不变，页码一般不会变；万一变了再来一遍
        doc, entries = assemble(check, font_css)
        html_path.write_text(doc, encoding="utf-8")
        render(html_path, second, args.chromium)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    finalize(second, out)
    from pypdf import PdfReader

    n = len(PdfReader(str(out)).pages)
    print(f"✅ {out}（{n} 页，{out.stat().st_size / 1024 / 1024:.1f} MB）")


if __name__ == "__main__":
    sys.exit(main())
