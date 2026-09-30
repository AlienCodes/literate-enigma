"""打包 Windows 发布版：dist/VoiceTwin-Windows-v<版本>.zip（解压后是一个 VoiceTwin 文件夹）。

    pip install markdown-it-py mdit-py-plugins
    python scripts/build_windows_release.py [--version 0.1.0] [--notes dist/release_notes.md]

压缩包内容：程序代码、Windows 安装脚本、README、docs/，以及由教程转换来的
《使用教程（先看我）.html》——双击即可在浏览器里看带目录的图文教程。
另外把 docs/声音分身VoiceTwin使用手册.pdf 复制为 dist/VoiceTwin-Manual-v<版本>.pdf，作为单独的 Release 附件。
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs" / "Windows详细使用教程.md"
MANUAL_PDF = ROOT / "docs" / "声音分身VoiceTwin使用手册.pdf"   # 由 scripts/build_manual_pdf.py 生成
INCLUDE = ["voicetwin", "docs", "install_windows.bat", "install_windows.ps1", "pyproject.toml", "README.md"]
TOP = "VoiceTwin"
REPO_URL = "https://github.com/AlienCodes/literate-enigma"


def project_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    if not m:
        raise SystemExit("pyproject.toml 里没有 version")
    return m.group(1)


def github_slug(value: str, separator: str = "-") -> str:
    """与 GitHub 标题锚点一致：小写、去掉标点符号、空格变连字符（保留中文）。"""
    value = value.strip().lower()
    value = re.sub(r"[^\w\- ]", "", value)
    return value.replace(" ", separator)


def markdown_to_html(md_text: str, title: str) -> str:
    try:
        # CommonMark 解析（与 GitHub 显示一致：列表里嵌套的列表/代码块用 3 个空格缩进）
        from markdown_it import MarkdownIt
        from mdit_py_plugins.anchors import anchors_plugin

        md = MarkdownIt("commonmark", {"html": False}).enable("table")
        md.use(anchors_plugin, min_level=1, max_level=3, slug_func=github_slug)
        body = md.render(md_text)
    except ImportError:
        body = f"<pre>{html.escape(md_text)}</pre>"
    # 教程里指向仓库内其它文件的相对链接，换成 GitHub 上的地址
    body = re.sub(r'href="(?!https?://|#)([^"]+)"', lambda m: f'href="{REPO_URL}/blob/master/{m.group(1)}"', body)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
  :root {{ --fg:#1f2328; --muted:#59636e; --bg:#ffffff; --code:#f6f8fa; --border:#d1d9e0; --accent:#0969da; --note:#fff8c5; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --fg:#e6edf3; --muted:#9198a1; --bg:#0d1117; --code:#161b22; --border:#3d444d; --accent:#4493f8; --note:#2d2a12; }}
  }}
  body {{ margin:0; background:var(--bg); color:var(--fg);
         font:16px/1.75 "Microsoft YaHei","PingFang SC","Noto Sans CJK SC",system-ui,sans-serif; }}
  main {{ max-width:880px; margin:0 auto; padding:24px 16px 80px; }}
  h1 {{ font-size:1.9em; border-bottom:1px solid var(--border); padding-bottom:.3em; }}
  h2 {{ margin-top:2.2em; border-bottom:1px solid var(--border); padding-bottom:.25em; }}
  h3 {{ margin-top:1.6em; }}
  a {{ color:var(--accent); }}
  code {{ background:var(--code); padding:.15em .4em; border-radius:6px; font-family:Consolas,"Cascadia Mono",monospace; font-size:.92em; }}
  pre {{ background:var(--code); padding:14px 16px; border-radius:8px; overflow-x:auto; }}
  pre code {{ padding:0; background:none; }}
  blockquote {{ margin:1em 0; padding:.6em 1em; background:var(--note); border-left:4px solid #d4a72c; border-radius:6px; }}
  blockquote p {{ margin:.3em 0; }}
  table {{ border-collapse:collapse; width:100%; margin:1em 0; display:block; overflow-x:auto; }}
  th, td {{ border:1px solid var(--border); padding:6px 12px; text-align:left; }}
  th {{ background:var(--code); }}
  li {{ margin:.25em 0; }}
  .online {{ color:var(--muted); font-size:.9em; }}
</style>
</head>
<body><main>
<p class="online">在线版（内容可能更新）：<a href="{REPO_URL}/blob/master/docs/Windows详细使用教程.md">{REPO_URL}</a></p>
{body}
</main></body>
</html>
"""


def release_notes(version: str, zip_name: str) -> str:
    return f"""## 声音分身 VoiceTwin v{version}（Windows）

用你自己的讲课视频和录音，复刻你的音色、语气和节奏（中文 + 英文），把讲稿生成"你的声音"的讲课音频和字幕。

### 下载

👉 下面 **Assets** 里的 **`{zip_name}`**（不需要下载 Source code）。

### 三步开始

1. 下载并解压 [GPT-SoVITS 官方整合包](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#KTvnO)（最新 v2pro 版）到 `D:\\GPT-SoVITS`；
2. 把 `{zip_name}` 解压到 `D:\\`，双击 `D:\\VoiceTwin\\install_windows.bat`，选 **1**，输入 `D:\\GPT-SoVITS`；
3. 双击桌面「声音分身 VoiceTwin」，按网页上的 ① 准备素材 → ② 训练 → ③ 生成讲课音频 操作。

**每一步的详细说明**：下载 Assets 里的 **《声音分身VoiceTwin使用手册》PDF**（`{manual_asset_name(version)}`，
约 80 页图文教程，压缩包的 `docs` 文件夹里也有一份）；或解压后双击 **`使用教程（先看我）.html`**，或在线查看
[Windows 详细使用教程]({REPO_URL}/blob/master/docs/Windows详细使用教程.md)。

### 电脑要求

Windows 10/11，NVIDIA 显卡 6GB 显存以上（推荐 8GB+），硬盘空闲 30GB 以上。

> 只克隆你自己的声音，或已取得本人授权的声音；公开发布 AI 合成音频时请遵守平台关于 AI 内容标识的规定。
"""


def build(version: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"VoiceTwin-Windows-v{version}.zip"
    files = []
    for item in INCLUDE:
        p = ROOT / item
        if p.is_dir():
            files += [f for f in sorted(p.rglob("*")) if f.is_file() and "__pycache__" not in f.parts
                      and f.suffix not in (".pyc", ".pyo")
                      and f.relative_to(ROOT).parts[:2] != ("docs", "manual")]   # 手册源文件不打包，只打包 PDF
        elif p.is_file():
            files.append(p)
        else:
            raise SystemExit(f"缺少文件：{item}")
    guide_html = markdown_to_html(GUIDE.read_text(encoding="utf-8"), "声音分身 VoiceTwin —— Windows 详细使用教程")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for f in files:
            zf.write(f, f"{TOP}/{f.relative_to(ROOT).as_posix()}")
        zf.writestr(f"{TOP}/使用教程（先看我）.html", guide_html)
    # PDF 使用手册同时作为单独的 Release 附件（文件名用英文，GitHub 会去掉附件名里的中文）
    if MANUAL_PDF.exists():
        shutil.copyfile(MANUAL_PDF, out_dir / manual_asset_name(version))
    return zip_path


def manual_asset_name(version: str) -> str:
    return f"VoiceTwin-Manual-v{version}.pdf"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="", help="版本号（默认读取 pyproject.toml）")
    ap.add_argument("--out", default=str(ROOT / "dist"))
    ap.add_argument("--notes", default="", help="同时写出 Release 说明到这个文件")
    args = ap.parse_args()
    version = (args.version or project_version()).lstrip("v")
    if version != project_version():
        raise SystemExit(f"版本号 {version} 与 pyproject.toml 中的 {project_version()} 不一致，请先修改 pyproject.toml")
    zip_path = build(version, Path(args.out))
    if args.notes:
        Path(args.notes).parent.mkdir(parents=True, exist_ok=True)
        Path(args.notes).write_text(release_notes(version, zip_path.name), encoding="utf-8")
    size_kb = zip_path.stat().st_size / 1024
    print(f"已生成 {zip_path}（{size_kb:.0f} KB）")


if __name__ == "__main__":
    sys.exit(main())
