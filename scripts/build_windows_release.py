"""打包 Windows 发布版：dist/VoiceTwin-Windows-v<版本>.zip（解压后是一个 VoiceTwin 文件夹）。

    pip install markdown-it-py mdit-py-plugins
    python scripts/build_windows_release.py [--version 0.1.0] [--notes dist/release_notes.md]

压缩包内容：程序代码、Windows 安装脚本、README、docs/，以及由《快速上手.md》转换来的
《使用教程（先看我）.html》——双击即可在浏览器里看图文版快速上手（截图已内嵌）。
另外把快速上手的 PDF 复制到 dist/ 作为单独的 Release 附件（详细的长手册已经不再发布）：
    docs/快速上手.pdf              → VoiceTwin-QuickStart-v<版本>.pdf（几页纸，先看这个）
"""

from __future__ import annotations

import argparse
import base64
import html
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUICK = ROOT / "快速上手.md"
QUICK_PDF = ROOT / "docs" / "快速上手.pdf"                   # 由 scripts/build_manual_pdf.py --quickstart 生成
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


def data_uri(path: Path) -> str:
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif"}.get(path.suffix.lower(),
                                                                                                 "application/octet-stream")
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def markdown_to_html(md_text: str, title: str, online_path: str = "快速上手.md", embed_images: bool = False,
                     extra_css: str = "") -> str:
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
    if embed_images:  # 截图直接内嵌，单个 HTML / PDF 文件就能完整显示
        body = re.sub(r'<img src="(?!https?://|data:)([^"]+)"', lambda m: f'<img src="{data_uri(ROOT / m.group(1))}"', body)
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
  img {{ max-width:100%; box-sizing:border-box; border:1px solid var(--border); border-radius:8px; }}
{extra_css}
</style>
</head>
<body><main>
<p class="online">在线版（内容可能更新）：<a href="{REPO_URL}/blob/master/{online_path}">{REPO_URL}</a></p>
{body}
</main></body>
</html>
"""


#: 每个版本在 Release 页面上写的「这一版新增」（没有写的版本就不显示这一段）
WHATS_NEW = {
    "18.5": [
        "**「📝 一键全部文字校正」**（在「① 准备素材」校对表上面）：以你的**母本标准库**为准，点一下就把识别引擎写错的字"
        "**一次全部改好**——标准库 = 你修缮过的讲课母本（你所有的说话习惯）+ 所有的英语语法术语 + 「错的写法 → 正确写法」对照表"
        "（借词 → 介词、艾子 → as、关系带词 → 关系代词、定语从剧 → 定语从句……），程序里已经带着，不用上传",
        "· 「修改建议」那一列**有把握**的建议也一起采用；**没把握的不会乱改**（比如两个识别引擎听得不一样的中文、"
        "本身就是一个词的同音字），还是红色、建议还在：听一听录音，对就点那一行的蓝色的「采用」",
        "· 你自己改过的字不会被改回去；点过「这句没错」的句子不动",
        "· **每批素材只能用一次**：用完按钮变灰（刷新网页、重开程序也是灰的）；以后加了新的素材、识别完，按钮会再亮起来，"
        "只改新加的句子，以前的句子一点不动。用之前你自己改过的字，它不会动",
        "· 改错了可以撤销：点那一行红色的「已采用」（或者自己改回去、撤销这一行的修改）；"
        "一行里你自己又改过别的地方时，只改建议的那几个字，程序拿不准改哪里时不会乱改，会告诉你原因，请你双击「文字」自己改",
        "修好：「保存修改」以后马上点「✅ 确认训练素材」，偶尔会报错（两个地方同时写一个文件）",
        "· 颜色还是原来的规矩：改过的字「文字」列绿色、「可能有错」列蓝色，没改的可能有错的字红色；改过的行是 🔴 没保存，"
        "看一眼没问题点「保存修改」，训练前点「✅ 确认训练素材」",
        "· 只改「刚好是一个完整的词」的地方（「凭借词汇」里的「借词」不改），你母本里常用的说法（比如「原型」）不改",
        "**你的母本逐句修缮过**：1008 句里还有 138 处当时没看到的识别错误（借词 17 处、定语从剧 / 从具……），"
        "装好这一版点一次「一键全部文字校正」就会全部改好（存成没保存的修改，你看一眼再保存）；另外 6 处英文例句听不出原话，没有改",
        "可以上传新的讲稿或改好的文字（txt 或 transcripts.csv）一起当母本用（可选）",
        "**「⬇️ 下载改好的文字（txt）」**：把「文字」列改好的文字一次全部存成 txt（一行一句，紫色删除的不要），下次可以当母本上传",
        "网页标题永远是「声音分身 VoiceTwin v18」（这次的安装包叫 v18.5）",
    ],
    "18.4": [
        "**修好：训练完以后「自动挑选最像你的模型」「重新挑选最佳模型」和「生成讲课音频」卡在「启动合成引擎」，"
        "等 10 分钟后报「GPT-SoVITS 没能启动」**。其实合成引擎一分钟内就开好了，是声音分身问它「好了没有」的方式不对，"
        "一直以为它没好。现在一开好就能认出来",
        "**训练好的模型不用重新训练**：装好这一版以后，到「② 训练模型」点「重新挑选最佳模型」就行",
        "**出问题时自动生成「问题报告」**：页面下面的「详细过程」里直接写出停在哪一步、原因、怎么办和自动找到的线索，"
        "同时在 logs 文件夹里存一份「问题报告_日期_时间.txt」；需要帮忙时把这个文件发给帮你的人就行",
        "合成引擎如果真的打不开，1~2 分钟内就会说明原因，不会再白等 10 分钟",
        "**必须先点「✅ 确认训练素材」才能训练**：没确认、确认以后又改过、或者还有没保存的修改，点「开始训练」都不会开始，会告诉你先去做哪一步",
        "**核查过：训练只用你保存过的、改好的文字；紫色（删除）的那一行音频和文字都不用**（也不当参考音频、不当挑模型的试听句子）；"
        "训练以后又改了文字，训练页和生成时会提醒你重新训练",
        "关掉黑色窗口时，GPT-SoVITS 的后台程序一起关掉，不会留在后台占着显卡",
        "修好真实引擎的两个音质问题：偶尔出现的「咔哒」声；句子开头第一个字被淡掉",
        "网页标题永远是「声音分身 VoiceTwin v18」（这次的安装包叫 v18.4）",
    ],
    "18.3": [
        "**校对表加了「查找 / 替换」（像 Word 一样全局改错字）**：表格上面有一个专门的查找框，"
        "输入一个词（例如「艾子」）点「🔍 查找」或者按回车，表格里只列出有这个词的句子，找到的字是**黄色**，现在这一处是**橙色**",
        "· 「⬆ 上一处 / ⬇ 下一处」一处一处看；「替换这一处」只换橙色的那一个，换完自动跳到下一处",
        "· 「全部替换」一次把所有的都换掉（会先问一次，说清楚一共几处）；换错了点「↩️ 撤销刚才的替换」",
        "· 换上的字是**绿色**、这一行亮**红灯**（没保存），和自己改字一样，点「保存修改」才生效；删除（紫色）的句子不查也不换",
        "· 英文默认只找整个单词（找 as 不会找到 has 里面的 as），要找单词里面的就把勾去掉；点「✖ 关闭查找」表格显示全部句子",
        "· 查找时找到过的句子一直列在表格里：换完、改完、删除以后也不会突然不见",
        "表格最左边的行号是这一句在全部句子里的位置（只看可能有错的、查找的时候也不变）",
        "网页标题永远是「声音分身 VoiceTwin v18」（这次的安装包叫 v18.3）",
    ],
    "18.2": [
        "**删除的句子整行变成紫色**（不再消失）：紫色 = 不再算训练素材；在「⋯ 选项」里点「撤销删除」，紫色消失、又算训练素材",
        "**新按钮「✅ 确认训练素材」**（在「保存修改」下面）：点了以后，用来训练的句子行号变成**橙色**，删除的、不能用的不显示行号",
        "表格上方显示**用来训练的句子数**：删几条就减几条，例如「1000 − 2（你删除的）= 998 条」，撤销删除就加回来",
        "**修好：删除时报错「还没有可用的素材」**：片段的文字还没识别出来时（上次「开始准备素材」的识别中途停了），"
        "删除会报错、表格不刷新。现在删除照样成功，表格里会写「还没有识别出文字」，上方说明**再点一次「开始准备素材」**就会接着把文字识别完",
        "网页标题永远是「声音分身 VoiceTwin v18」（这次的安装包叫 v18.2）",
    ],
    "18.1": [
        "**校对表（① 准备素材下面）按老师的要求重新做了**：",
        "· 改错字：**双击「文字」**会打开一个会自动换行的大框，整句话都看得见（以前一点就挤成一行、超出格子）；"
        "改过、新打上去的字在「文字」里是**绿色**，在「可能有错」那一列是**蓝色**",
        "· 「修改建议」是一个**蓝色小按钮**：点一下就按建议自动改好，按钮**变红 = 生效了**（再点一下可以撤销）；"
        "只有「可能有错」那一列有内容的行才有。建议更准了：像「艾子」这种把老师说的英文（as）听成汉字的，现在会建议改回 as"
        "（以前查过错字的，再点一次「🔍 自动查找可能的错字」就能用上）",
        "· 最右边一列「**⋯ 选项**」：**保存这一行**、**删除这一行**（会再问一次；删除的行变灰色，菜单里变成**撤销删除**）、"
        "修改文字、听一听、撤销这一行的修改、这句没错；按钮左边的小灯 **🔴 = 改了还没保存、🟢 = 已经保存**",
        "· 去掉了「丢弃原因」「保留」两列：不用来训练的行整行变灰；没保存的修改刷新网页也不会丢",
        "顶部的模型型号框改成圆角长方形；网页标题仍然是「声音分身 VoiceTwin v18」（这次的安装包叫 v18.1，因为同一个号码不能发布两次）",
    ],
    "18": [
        "**版本号改成 v18**（老师喜欢的号码）：网页标题显示「声音分身 VoiceTwin v18」。v18 比 v0.1.9 新，"
        "功能和 v0.1.9 完全一样，只是换了号码；以后的版本是 v19、v20……",
        "包含 v0.1.8、v0.1.9 的全部改进：标题右边显示从模型文件里检测出来的模型型号；修好桌面图标建不出来（????）；"
        "安装时不再出现红色 ERROR / 黄色 WARNING；「以管理员身份运行」时安装窗口的中文不再变成「?」",
    ],
    "0.1.9": [
        "**修好：安装窗口里中文全部变成「?」**：右键「以管理员身份运行」时，Windows 会打开老式黑色窗口；"
        "在「非 Unicode 程序的语言」不是中文的电脑上，这种窗口的字体没有中文字。现在安装程序会自动换到 Windows Terminal 里运行，"
        "没有 Windows Terminal 时把窗口字体换成有中文字的「新宋体」；声音分身的黑色窗口也一样",
        "（安装本身一直是正常的，只是中文显示不出来；已经装好的不用重装）",
    ],
    "0.1.8": [
        "**网页顶部显示你正在用的模型型号**：标题右边写着例如「模型：GPT-SoVITS v2ProPlus」。它是从你的声音模型文件里读出来的"
        "（和 GPT-SoVITS 自己判断版本的方法一样），不是照抄设置；还没训练时读底模；读不出来就如实写「读不出来」。"
        "以后换成 v4、v5（官方公开后）也能认出来",
        "**修好桌面图标建不出来的问题**：有些电脑（Windows 的「非 Unicode 程序的语言」不是中文）会把中文图标名变成 ????、保存失败；"
        "现在先用英文名建好，再改成中文名放到桌面",
        "安装时不再出现 librosa 的红色 ERROR 和「不在 PATH 里」的黄色 WARNING（两条都不影响使用；已用和整合包完全相同的版本测试过）；"
        "「环境检查」前面不再出现一堆英文警告",
    ],
    "0.1.7": [
        "**「像你本人（%）」换成精准声纹打分**：测试了 19 个公开的声纹模型，选出最准的 3 个一起打分"
        "（ReDimNet2-B6 + ERes2NetV2 + ERes2Net-base，都用中文训练过）；2 秒的中文短句里认错人的比例约 0.05%",
        "**百分比两头校准**：100% = 和你自己的真实录音一样像，0% = 陌生人的水平；⑤ 鉴别会告诉你你自己的录音一般在多少 %",
        "**只比较人声**：句子之间的绝对静音、「去杂音」版本、音量大小基本不影响分数（实测偏差只有 1~3 个百分点）",
        "**很短的句子**按同样长度的你自己的录音来算 100%；人声不到 2 秒的句子不直接判「不像」，提醒你用耳朵听",
        "安装时自动下载声纹模型（约 170 MB，下载后逐个核对）；没下载时自动用旧的打分方式，网页上点「⬇️ 下载缺少的模型」可以补上",
        "以前生成好的句子会自动按新标准重新打分，不用重新生成",
        "「环境检查」新增一行：确认用的是 GPT-SoVITS 目前公开的最新、最强版本 v2ProPlus（V5 还没公开）",
    ],
    "0.1.6": [
        "**每一步都有进度条**：百分比、第几步、已用时间、预计几点完成；绿色 = 正常，黄色 = 好几分钟没动静，红色 = 出问题（写明原因和怎么办）",
        "**网页最上面一直显示显卡状态**：绿色 = 正常；红色时告诉你怎么修",
        "**所有表格都有编号和总数**；新增 **🎙️ 我的声音库**，点一下就选中声音",
        "**训练参数全自动**：按你的显卡和素材选出最好的设置，显存不够自动重试",
        "**新的「完美」质量**：每句最多试 20 次；同时做「未去杂音 / 去杂音」两个版本，自动推荐更像你原声的那个，由你选",
        "**每句都有「像你本人（%）」**：用你自己的真实录音做标尺，低于 85% 的自动淘汰",
        "**绝对静音**：生成的音频只有你的声音，没有背景音、没有底噪，句子之间完全静音",
        "**语速拉杆**：往左更快、往右更慢，音色不变",
        "**自动查找错字**：可能识别错的字标成红色，并给出修改建议",
        "**⑤ 鉴别**：机器打分排名 + 观众盲听测试",
        "出错时用中文说明原因和怎么办；修复生成失败后再点「生成」可能提示「看不懂「[]」」的问题",
    ],
}


def release_notes(version: str, zip_name: str) -> str:
    news = WHATS_NEW.get(version)
    news_md = ("\n### ✨ 这一版新增\n\n" + "\n".join(f"- {line}" for line in news) + "\n") if news else ""
    return f"""## 声音分身 VoiceTwin v{version}（Windows）

用你以前的讲课视频训练出"你的声音"，以后粘贴讲稿就能生成你的声音读的讲课音频和字幕（中文 + 英文）。
{news_md}
### 🔄 已经装过旧版本？升级只要 3 步（声音和训练好的模型都不会丢）

1. 下载下面的 `{zip_name}`，右键 → 全部解压缩 → 位置填 `D:\\`，提示有同名文件时选**替换**
2. 双击 `D:\\VoiceTwin\\install_windows.bat`，输入 **1** 回车，再输入 `D:\\GPT-SoVITS` 回车，等它装完
3. 双击桌面「声音分身 VoiceTwin」，黑色窗口里写着「声音分身 VoiceTwin v{version} 正在启动」就对了（网页标题永远显示 v18）

### 📥 下载（在下面的 Assets 里）

| 文件 | 是什么 |
|---|---|
| **`{quick_asset_name(version)}`** | **快速上手（几页纸，先看这个）** |
| **`{zip_name}`** | 程序本体 |

不需要下载 Source code。

### 🚀 最快用起来

**安装（一次）**
1. 下载 [GPT-SoVITS 整合包](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#KTvnO)（最新 v2pro 版），解压并改名为 `D:\\GPT-SoVITS`
2. 把 `{zip_name}` 解压到 `D:\\`，双击 `D:\\VoiceTwin\\install_windows.bat`，输入 **1** 回车，再输入 `D:\\GPT-SoVITS` 回车，等它装完

**训练（一次）**
3. 把讲课视频复制到 `D:\\讲课素材`，双击桌面「声音分身 VoiceTwin」
4. 声音名称填 `我的声音` → **① 准备素材**：文件夹填 `D:\\讲课素材` → 开始准备素材 → 等 ✅
5. **② 训练模型** → 开始训练 → 等 ✅

**以后每次**
6. **③ 生成讲课音频** → 粘贴讲稿 → 生成 → 试听、下载音频和字幕

图文版：[快速上手]({REPO_URL}/blob/master/快速上手.md)（解压后双击 `使用教程（先看我）.html` 也能看）。

> 电脑要求：Windows 10/11，NVIDIA 显卡 6GB 显存以上，硬盘空闲 30GB。只克隆你自己的声音；公开发布 AI 合成音频时请按平台规定标注。
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
    guide_html = markdown_to_html(QUICK.read_text(encoding="utf-8"), "声音分身 VoiceTwin 快速上手", embed_images=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for f in files:
            zf.write(f, f"{TOP}/{f.relative_to(ROOT).as_posix()}")
        zf.writestr(f"{TOP}/使用教程（先看我）.html", guide_html)
    # PDF 同时作为单独的 Release 附件（文件名用英文，GitHub 会去掉附件名里的中文）
    for src, name in ((QUICK_PDF, quick_asset_name(version)),):
        if src.exists():
            shutil.copyfile(src, out_dir / name)
    return zip_path


def quick_asset_name(version: str) -> str:
    return f"VoiceTwin-QuickStart-v{version}.pdf"




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
