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
请求账 = os.path.expanduser('~/.云端请求.json')   # K34：推了 GitHub 请求（推请求.py 记）、约了唤醒（send_later 后钩子记）
def _读账():
    try: return json.load(open(请求账))
    except Exception: return {}
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


# K16（G59，2026-10-26：上一个改门会话真的试过 git -c core.hooksPath=… 绕提交钩子，被平台审核拦下；不能靠外部兜底）：
# 绕开提交前规则执行核查的写法一律拦：--no-verify 及其缩写、-c/--config-env/include 改 hooksPath、GIT_* 环境变量、
# 改/删 .git/hooks、.git/config、githooks、~/.gitconfig、git 别名、不走钩子的底层提交（commit-tree、update-ref……）、解码后再执行
_放行GIT变量 = re.compile(r'GIT_(AUTHOR|COMMITTER)_(NAME|EMAIL|DATE)|GIT_TERMINAL_PROMPT|GIT_PAGER|GIT_LFS_SKIP_SMUDGE|GIT_TRACE\w*|GIT_SSL_CAINFO|GIT_HTTP_LOW_SPEED_\w+')
_护路径 = re.compile('(?:^|[\\s/"\'=:<>(])(?:\\.git(?:/(?:hooks|config|info)\\b|/?(?=[\\s"\';&|)]|$))|githooks\\b|\\.gitconfig\\b|制作记录/证据/)')
_只读命令 = {'ls', 'cat', 'head', 'tail', 'grep', 'rg', 'wc', 'diff', 'stat', 'file', 'sha256sum', 'md5sum', 'readlink', 'realpath', 'du', 'test', '['}
_只读git = {'log', 'diff', 'show', 'status', 'add', 'ls-files', 'blame', 'grep', 'cat-file', 'ls-tree', 'rev-parse', 'fetch', 'pull', 'push', 'commit', 'clone', 'stash', 'branch', 'remote'}


def 绕钩子(c, segs):
    """返回拦下的理由；不拦返回 None。c 是去掉 heredoc 正文后的命令，segs 是拆开的命令段。"""
    if re.search(r'--no-v(?:e(?:r(?:i(?:f(?:y)?)?)?)?)?(?![\w-])', c):
        return '不许用 --no-verify（或它的缩写）跳过 git 钩子'
    low = c.lower()
    读 = re.sub(r'\bgit\s+(?:-c\s+\S+\s+)?config\s+(?:--get\s+)?core\.hookspath\s*(?=$|[;&|)\n])', '', low)   # 只读 core.hooksPath 放行
    if 'hookspath' in 读: return '不许设置、取消或临时改 core.hooksPath（含 git -c core.hooksPath=…）'
    if re.search(r'\bgit\b', low) and re.search(r'--config-env|\binclude(?:if)?\.', low): return '不许用 --config-env、include/includeIf 改 git 配置（可以借此换掉钩子）'
    for m in re.finditer(r'\b(GIT_[A-Z0-9_]+)', c):
        if not _放行GIT变量.fullmatch(m.group(1)): return f'不许用 git 环境变量 {m.group(1)}（GIT_CONFIG_*、GIT_DIR 等能让提交绕开钩子）'
    if re.search(r'\b(base64|xxd|openssl)\b[^\n;&]*\|\s*(?:(?:ba|z)?sh|python3?|perl)\b', c): return '不许把解码出来的文字当命令执行（看不出里面有没有绕钩子）'
    for s in segs:
        if not s: continue
        w = re.sub(r'^(?:\(|\{|sudo\s+|env\s+(?:-\S+\s+)*|command\s+|exec\s+|nice\s+|time\s+|timeout\s+\S+\s+|\\)+', '', s)
        first = (w.split() or [''])[0].rsplit('/', 1)[-1]
        g = re.search(r'(?:^|[\s/\\])git\s+(?:-[Cc]\s+\S+\s+|--\S+\s+)*([\w-]+)', w)
        sub = g.group(1) if g else ''
        if sub in ('commit-tree', 'update-ref', 'fast-import', 'replace') or (sub == 'symbolic-ref' and not re.search(r'symbolic-ref\s+-q\s+HEAD\s*$', w)):
            return f'不许用 git {sub}（底层命令做提交、改分支不走提交前钩子）'
        if (sub == 'config' or re.search(r'\s-c\s*alias\.', w)) and re.search(r'\balias\.', w): return '不许定义 git 别名（别名可以藏 --no-verify、换钩子）'
        if sub == 'commit' and re.search(r'\s-[a-zA-Z]*n[a-zA-Z]*(?=\s|$)', w): return '不许用 -n 跳过 git 钩子'
        if re.match(r'alias\b', w) and re.search(r'\bgit\b', w): return '不许用 shell 别名包装 git'
        if _护路径.search(' ' + w):
            写 = re.search(r'>>?\s*\S*(?:\.git\b|githooks|\.gitconfig|证据/)', w)
            ok = not 写 and ((first in _只读命令 and not re.search(r'\btee\b|-delete|-exec', w)) or (first == 'git' and sub in _只读git))
            if not ok: return '不许改、删、移 .git/hooks、.git/config、githooks、~/.gitconfig、制作记录/证据（钩子和使用证据只能由正式程序改）'
    return None


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
        def _去heredoc(c):   # G15（2026-10-24 执行效应演练查出）：heredoc 正文里以 git/vercel 开头的行也被当成命令拦了，先去掉 heredoc 正文
            out, end = [], None
            for l in c.splitlines():
                if end is not None:
                    if l.strip() == end: end = None
                    continue
                out.append(l); m = re.search(r'<<-?\s*[\'"]?([A-Za-z_]\w*)[\'"]?', l)
                if m: end = m.group(1)
            return '\n'.join(out)
        segs = [s.strip() for l in _去heredoc(c).splitlines() for s in re.split(r'&&|\|\||;|\|', l)]
        why = 绕钩子(_去heredoc(c), segs)
        if why: return 拦('PreToolUse', f'【规则执行闸门】K16：{why}（CLAUDE.md 第16条：提交前的规则执行核查绝不许绕过）。')
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
        for s in segs:   # G10：pgrep/pkill 认不出中文路径（LANG 为空），用中文去找进程永远找不到——2026-10-23 出片排队又因此让两篇同时跑
            if re.match(r'(.*\s)?(pgrep|pkill)\b', s) and re.search(r'[^\x00-\x7f]', s):
                return 拦('PreToolUse', '【G10 闸门】pgrep/pkill 认不出中文路径，用中文找进程永远找不到。排队用 flock 锁（如 flock /tmp/出片队列.lock …），查进程用 ps 加英文字（如 make_video、ffmpeg）或读 /proc/PID/cmdline。')
        for s in segs:   # C1/C2/流16：没有用户明确同意，不部署、不公开发布
            if re.search(r'^(npx\s+)?(vercel|netlify|surge|firebase\s+deploy|wrangler\s+(deploy|publish)|heroku)\b|^npm\s+publish|^twine\s+upload|^gh-pages\b', s) and '【用户同意' not in c:
                return 拦('PreToolUse', '【部署闸门】C1/C2/流16：没有用户明确同意，不部署、不公开发布（默认只生成文件）。用户明确要求时，命令里写“# 【用户同意：原话】”再执行。')
        m = re.search(r'【用户同意：([^】]{4,})】', c)
        if m:
            try: open(f'{V}/制作记录/用户同意记录.md', 'a').write(f'- {datetime.datetime.utcnow():%Y-%m-%dT%H:%M}（UTC）{m.group(1)} ← {c[:80]}\n')
            except Exception: pass
        return None
    if kind == '改文件':   # K16/G60/G61：Edit、Write 也不许改钩子、git 配置、使用证据；出稿、改稿会话不许改门程序
        p = os.path.abspath(str(ti.get('file_path') or ti.get('notebook_path') or ''))
        if re.search(r'/\.git(/|$)|/\.gitconfig$', p):
            return 拦('PreToolUse', '【规则执行闸门】K16：不许直接改 .git/ 下的文件或 ~/.gitconfig（提交钩子、git 配置只能由 开工提醒.sh、推送两仓库.sh 设）。')
        if '/制作记录/证据/' in p:
            return 拦('PreToolUse', '【G60 证据闸门】使用证据只能由正式入口（开工记录、生成文本、草稿声音.sh、交付核查、定稿流水线）写，不许手写。')
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import 会话开工 as _HK
            r = _HK.读记录() or {}; rel = re.sub(r'^.*?/(?=(视频/工具/|\.github/|\.claude/))', '', p)
            if r.get('角色') in ('出稿', '改稿') and _HK.门程序(rel):
                return 拦('PreToolUse', f'【G61 会话角色闸门】本会话是“{r["角色"]}”会话，不许改门程序 {rel}（G25：程序不好写进 NN.md 方法复盘 + 报坑.py 登记，由改门会话改）。')
        except Exception: pass
        return None
    if kind == '已约唤醒':   # K34：send_later 之后记下（PostToolUse），收工闸门据此放行
        a = _读账(); a['唤醒'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        try: json.dump(a, open(请求账, 'w'), ensure_ascii=False)
        except OSError: pass
        return None
    if kind == '发文件后':   # W6：发了 Word，提醒用户打印要勾选“打印背景色”（钩子把提醒放进我的上下文，不靠我记）
        if any(str(f).lower().endswith('.docx') for f in (ti.get('files') or [])):
            return {'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': '【W6 提醒】刚发了 Word：回复里要提醒用户，打印时勾选“打印背景色”，否则浅色底色和彩色字印不出来。'}}
        return None
    if kind == '收工':
        if d.get('stop_hook_active'): return None
        a = _读账(); rq = a.get('请求', []); last = max((r.get('时刻', '') for r in rq), default='')
        if last and a.get('唤醒', '') < last:   # K34：GitHub 写回结果（API 提交）不触发 PR 事件、不会唤醒会话（2026-10-26 空等 2 小时 20 分、改门锁过期）
            return 拦('Stop', f'【K34 云端请求闸门】推了 GitHub 请求（{rq[-1].get("名字", "")}，{last}）还没约唤醒：GitHub 写回结果不会唤醒会话。'
                     '先用 send_later（claude-code-remote）约约 20 分钟后叫回自己，再收工。')
        if not os.path.isdir(仓库): return None
        r = subprocess.run(['git', '-c', 'core.quotepath=off', '-C', 仓库, 'status', '--porcelain', '--', '视频', 'CLAUDE.md', '新版定稿'],
                           capture_output=True, text=True).stdout
        ch = []
        for l in r.splitlines():
            p = l[3:].strip().strip('"')
            if not l.strip() or '子代理记录.md' in p or p.endswith('全篇重查通过.json'): continue   # 全篇重查边查边记的进度，跑完它自己推送
            if l.startswith(' M') and re.match(r'视频/制作记录/方法进化/[^/]+\.json$', p): continue   # K33：已推过的本会话 token 记录每轮重写（等锁、等 GitHub 时每轮都要推一次），跟下一次真推送一起走
            if l.startswith(' M') and '制作记录/' in p:   # 收工记录钩子每轮自动更新的“进行中”行不算没推送的改动
                df = subprocess.run(['git', '-C', 仓库, 'diff', '-U0', '--', p], capture_output=True, text=True).stdout
                chg = [x for x in df.splitlines() if x[:1] in '+-' and not x.startswith(('+++', '---'))]
                if chg and all('进行中' in x for x in chg): continue
            ch.append(l)
        if ch:
            return 拦('Stop', f'【守则3 收工闸门】还有 {len(ch)} 个改动没推送（如 {ch[0][3:][:60]}）：'
                     '先 bash 视频/工具/推送两仓库.sh "说明"（会先过规则执行核查），再收工。')
        # 方法进化闸门（守则12/T29，用户 2026-10-23：“我们的方法一定要不断的进化……这次做完，你就下一步想……还有没有能够去进化的地方”）：
        # 今天改过工具，《制作硬性标准与踩坑总结》的方法升级记录里就要有今天的一行（哪件手工活变成了程序、哪里还能更省）
        今天 = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        改 = subprocess.run(['git', '-C', 仓库, 'log', f'--since={今天}T00:00:00+00:00', '--format=%h', '--', '视频/工具'], capture_output=True, text=True).stdout.split()
        try: 记 = open(f'{仓库}/视频/制作硬性标准与踩坑总结.md').read().split('方法升级记录', 1)[1]
        except Exception: 记 = ''
        if 改 and f'- {今天}' not in 记:
            return 拦('Stop', f'【方法进化闸门】今天改了 {len(改)} 次工具，《制作硬性标准与踩坑总结》“方法升级记录”里还没有今天（{今天}）的一行：'
                     '写清哪件手工活变成了程序、哪个门改成了查用户看到的东西、下一步哪里还能更省，推送后再收工。')
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
