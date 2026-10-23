#!/usr/bin/env python3
"""Claude 钩子闸门（规则执行机器，CLAUDE.md 第16条）：拦的是我自己的动作，不靠记忆。
  python3 闸门.py 子代理   PreToolUse(Agent|Workflow|Task)：守则2①/T29 不派子代理、工作流；
                           确有必要时，任务说明里写“【T29许可：理由】”才放行，并记进 制作记录/子代理记录.md
  python3 闸门.py 发文件   PreToolUse(SendUserFile)：守则7/A25 声音、视频、Word、PDF、网页一次只发一个，
                           并且必须是过了核查的那个文件（交付核查 出片后 / 生成文本 记下的文件指纹）
  python3 闸门.py 命令     PreToolUse(Bash)：不许用 --no-verify / -n 跳过提交前的规则执行核查，不许改 core.hooksPath
  python3 闸门.py 收工     Stop：postgraduate-vocabulary 里还有没推送的改动就不让收工（守则3）
  python3 闸门.py 发文件后 PostToolUse(SendUserFile)：发了 Word 就提醒用户打印勾选“打印背景色”（W6）
  命令闸门同时管部署（C1/C2/流16）：不部署、不公开发布、不推 master/gh-pages、不强推，除非命令里写明用户原话
输入：钩子的 JSON（stdin）；输出：拦下时打印决定 JSON。"""
import sys, os, json, re, hashlib, subprocess, datetime
V = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PV = '/home/user/postgraduate-vocabulary'
回执目录 = os.path.expanduser('~/.核查回执')
媒体 = ('.mp4', '.mp3', '.wav', '.m4a', '.docx', '.pdf', '.html')


def 指纹(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def 记回执(paths, 来源):
    """核查通过的文件记下指纹（交付核查 出片后、生成文本 调用）"""
    os.makedirs(回执目录, exist_ok=True)
    for p in paths:
        if os.path.exists(p): open(f'{回执目录}/{指纹(p)}', 'w').write(f'{来源} {os.path.abspath(p)}\n')


def 拦(事件, 理由):
    if 事件 == 'Stop': return {'decision': 'block', 'reason': 理由}
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny', 'permissionDecisionReason': 理由}}


def 判(kind, d, 仓库=PV):
    ti = d.get('tool_input') or {}
    if kind == '子代理':
        s = json.dumps(ti, ensure_ascii=False)
        m = re.search(r'【T29许可：([^】]{6,})】', s)
        if not m:
            return 拦('PreToolUse', '【T29 闸门】守则2①：不派子代理/工作流，除非程序做不了、我一个人也做不了。'
                     '确有必要，在任务说明里写“【T29许可：为什么程序和我一个人都做不了】”再派（会记进 制作记录/子代理记录.md）。')
        try:
            open(f'{V}/制作记录/子代理记录.md', 'a').write(
                f'- {datetime.datetime.utcnow():%Y-%m-%dT%H:%M}（UTC）{d.get("tool_name")}：{m.group(1)}\n')
        except Exception: pass
        return None
    if kind == '发文件':
        fs = ti.get('files') or []
        med = [f for f in fs if str(f).lower().endswith(媒体)]
        if len(med) > 1:
            return 拦('PreToolUse', f'【A25 闸门】守则7：声音、视频、文档一次只发一个（这次 {len(med)} 个：{"、".join(map(os.path.basename, med))}）。')
        for f in med:
            p = f if os.path.isabs(f) else os.path.join(d.get('cwd') or os.getcwd(), f)
            if not os.path.exists(p): continue
            if not os.path.exists(f'{回执目录}/{指纹(p)}'):
                return 拦('PreToolUse', f'【A25 闸门】守则7：{os.path.basename(p)} 没有核查通过的回执（声音、视频要过 交付核查 出片后，'
                         '文档要用 生成文本.py 生成），不许发。试听也只能用出片程序生成、过核查。')
        return None
    if kind == '命令':
        c = ti.get('command') or ''
        # 只看真正执行的 git 命令段（按行、; && || | 拆开，段首是 git），不看 heredoc、字符串里的字
        segs = [s.strip() for l in c.splitlines() for s in re.split(r'&&|\|\||;|\|', l)]
        for s in segs:
            s = re.sub(r'^(\(|cd\s+\S+\s*$|sudo\s+|env\s+\S+=\S+\s+)+', '', s)
            if not re.match(r'git\b', s): continue
            if '--no-verify' in s or re.search(r'\bcommit\b.*\s-[a-zA-Z]*n[a-zA-Z]*(\s|$)', s):
                return 拦('PreToolUse', '【规则执行闸门】不许用 --no-verify / -n 跳过 git 钩子（CLAUDE.md 第16条）。')
            if re.search(r'\bpush\b', s) and (re.search(r'(^|[\s:+])(master|gh-pages)(\s|$)', s) or re.search(r'\s(-f|--force)(\s|$)|--force-with-lease', s)) and '【用户同意' not in c:
                return 拦('PreToolUse', '【部署闸门】C1/C2/流16：不推 master、gh-pages，不强推（master 是另一个项目）；用户明确要求时，命令里写“# 【用户同意：原话】”再执行。')
            if re.search(r'core\.hooksPath\s+\S|--unset[^|;&]*core\.hooksPath|core\.hooksPath[^|;&]*--unset', s):   # 只拦设置、取消；读取不拦
                return 拦('PreToolUse', '【规则执行闸门】不许改 core.hooksPath（提交前的规则执行核查靠它，开工提醒.sh 和 推送两仓库.sh 自动设好）。')
        if re.search(r'Document\(', c) and '.docx' in c and not re.search(r'read_docx2|make_docx|segs\(', c):
            return 拦('PreToolUse', '【W2 闸门】读回用户改过的 Word 一律用 read_docx2.py（两行一组、单元格去重：Word 会把相邻小表格合并，直接读会大量重复）。')
        for s in segs:   # C1/C2/流16：没有用户明确同意，不部署、不公开发布
            if re.search(r'^(npx\s+)?(vercel|netlify|surge|firebase\s+deploy|wrangler\s+(deploy|publish)|heroku)\b|^npm\s+publish|^twine\s+upload|^gh-pages\b', s) and '【用户同意' not in c:
                return 拦('PreToolUse', '【部署闸门】C1/C2/流16：没有用户明确同意，不部署、不公开发布（默认只生成文件）。用户明确要求时，命令里写“# 【用户同意：原话】”再执行。')
        m = re.search(r'【用户同意：([^】]{4,})】', c)
        if m:
            try: open(f'{V}/制作记录/用户同意记录.md', 'a').write(f'- {datetime.datetime.utcnow():%Y-%m-%dT%H:%M}（UTC）{m.group(1)} ← {c[:80]}\n')
            except Exception: pass
        return None
    if kind == '发文件后':   # W6：发了 Word，提醒用户打印要勾选“打印背景色”（钩子把提醒放进我的上下文，不靠我记）
        if any(str(f).lower().endswith('.docx') for f in (ti.get('files') or [])):
            return {'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': '【W6 提醒】刚发了 Word：回复里要提醒用户，打印时勾选“打印背景色”，否则浅色底色和彩色字印不出来。'}}
        return None
    if kind == '收工':
        if d.get('stop_hook_active'): return None
        if not os.path.isdir(仓库): return None
        r = subprocess.run(['git', '-c', 'core.quotepath=off', '-C', 仓库, 'status', '--porcelain', '--', '视频', 'CLAUDE.md', '新版定稿'],
                           capture_output=True, text=True).stdout
        ch = []
        for l in r.splitlines():
            p = l[3:].strip().strip('"')
            if not l.strip() or '子代理记录.md' in p: continue
            if l.startswith(' M') and '制作记录/' in p:   # 收工记录钩子每轮自动更新的“进行中”行不算没推送的改动
                df = subprocess.run(['git', '-C', 仓库, 'diff', '-U0', '--', p], capture_output=True, text=True).stdout
                chg = [x for x in df.splitlines() if x[:1] in '+-' and not x.startswith(('+++', '---'))]
                if chg and all('进行中' in x for x in chg): continue
            ch.append(l)
        if ch:
            return 拦('Stop', f'【守则3 收工闸门】还有 {len(ch)} 个改动没推送（如 {ch[0][3:][:60]}）：'
                     '先 bash 视频/工具/推送两仓库.sh "说明"（会先过规则执行核查），再收工。')
        return None
    return None


if __name__ == '__main__':
    kind = sys.argv[1]
    try: d = json.load(sys.stdin)
    except Exception: d = {}
    try: out = 判(kind, d)
    except Exception as e:   # 闸门自己出错不锁死工具（机器每次当场跑钩子自检，坏了会在提交、推送时停）
        print(f'闸门程序出错：{e}', file=sys.stderr); out = None
    if out: print(json.dumps(out, ensure_ascii=False))
    sys.exit(0)
