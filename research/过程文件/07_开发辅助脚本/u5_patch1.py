p = '<仓库>/.claude/worktrees/wf_08725f86-d54-4/voicetwin/errors.py'
s = open(p, encoding='utf-8').read()
old_new = [
    ('''r"\\b40[0134] Client Error|Repository Not Found|EntryNotFoundError|RevisionNotFoundError|GatedRepoError",''',
     '''r"\\b40[0134] Client Error|Repository Not Found|\\bEntryNotFoundError|RevisionNotFoundError|GatedRepoError",'''),
    ('''def _fill_engine(ctx: _Ctx) -> Dict[str, str]:
    if "GPT-SoVITS" in ctx.text or "api_v2" in ctx.text:
        return {"engine": "GPT-SoVITS"}
    m = re.search(r"(Qwen3-TTS|IndexTTS)", ctx.text, re.I)
    return {"engine": m.group(1) if m else "合成引擎"}''',
     '''def _fill_engine(ctx: _Ctx) -> Dict[str, str]:
    # 英文名后面留一个空格再接中文；没认出是哪个引擎时说「合成引擎」
    if "GPT-SoVITS" in ctx.text or "api_v2" in ctx.text:
        return {"engine": "GPT-SoVITS "}
    m = re.search(r"(Qwen3-TTS|IndexTTS)", ctx.text, re.I)
    return {"engine": m.group(1) + " " if m else "合成引擎"}'''),
    ('''          "{engine} 没能启动",''', '''          "{engine}没能启动",'''),
    ('''          "{engine} 没能生成声音",''', '''          "{engine}没能生成声音",'''),
    ('''def _fill_media(ctx: _Ctx) -> Dict[str, str]:''', '''_UNQUOTED_MISSING = re.compile(
    r"((?:[A-Za-z]:)?[^\\s:'\\"]+\\.[A-Za-z0-9]{1,6}): (?:No such file or directory|Invalid data found)")


def _fill_path(ctx: _Ctx) -> Dict[str, str]:
    """找不到的文件：先看异常里的 filename / 引号里的路径，再看 ffmpeg 的「路径: No such file or directory」。"""
    values = _fill_file(ctx)
    if values["file"]:
        return values
    for m in (_UNQUOTED_MISSING.search(ctx.line), _FFMPEG_INPUT.search(ctx.text)):
        if m:
            name = _basename(m.group(1))
            if _useful_name(name):
                return {"file": name, "file_q": f"「{name}」", "file_s": f"：{name}"}
    return values


def _fill_media(ctx: _Ctx) -> Dict[str, str]:'''),
    ('''          "检查路径有没有写对，文件是不是被移动、改名或删除了。路径可以在文件夹窗口顶部的地址栏复制，再粘贴过来。",
          fill=_fill_file),''', '''          "检查路径有没有写对，文件是不是被移动、改名或删除了。路径可以在文件夹窗口顶部的地址栏复制，再粘贴过来。",
          fill=_fill_path),'''),
]
for o, n in old_new:
    assert o in s, o
    s = s.replace(o, n)
open(p, 'w', encoding='utf-8').write(s)
print("ok")
