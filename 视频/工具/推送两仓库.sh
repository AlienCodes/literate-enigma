#!/bin/bash
# 一条命令备份两个仓库（2026-10-15 方法升级，省 token）：提交 postgraduate-vocabulary → 只把这次改动的 视频/ 文件拷进 literate-enigma
# → 提交 → 推送两边 → 用 git 记录的文件指纹比对两边 视频/ 逐文件一致（不再逐个读大视频，几秒完成）。
# 用法：bash 视频/工具/推送两仓库.sh "提交说明"
set -e
HERE=$(cd "$(dirname "$0")" && pwd)   # 本程序所在的工具目录（下面会 cd 到主仓库）
exec 9>${PUSH_LOCK:-/tmp/推送两仓库.lock}; flock 9   # 几篇同时做时排队推送（推送自检用自己的锁，否则在推送里跑自检会自己等自己）
P=${PUSH_P:-/home/user/postgraduate-vocabulary}; L=${PUSH_L:-/home/user/literate-enigma}; B=${PUSH_B:-claude/adoring-hamilton-5qskmm}   # PUSH_* 只给 推送自检.py 在假仓库里测用
T=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01XbsiuYS9p9y2vNiB4h6ZZU'
cd $P
git symbolic-ref -q HEAD >/dev/null || git checkout -q -B main   # K130（36 推送连被拒 5 遍）：主仓库分离 HEAD 时 main 落后，先把 main 挪到 HEAD（定稿.sh K128 同一写法）
# git 提交钩子装上（新容器、别的会话同样生效）：提交前只查快测印章，对不上自动跑快测
git -C $P config core.hooksPath 视频/工具/githooks; git -C $L config core.hooksPath 视频/工具/githooks 2>/dev/null
[ ! -f $P/视频/工具/新管/印章.py ] || python3 $P/视频/工具/新管/印章.py --自动 || { echo "【停止】快测不通过（有检查坏了，属于质量问题）：先修好再推"; exit 1; }   # 印章对不上自动跑快测，过了接着推（用户 2026-10-29）
python3 $P/视频/工具/报坑.py --查 > /dev/null 2>&1 || echo "（提醒：报坑登记有撞号或总表新行没取号，python3 视频/工具/报坑.py --查 看；只提醒，不拦）"
git add -A 视频 CLAUDE.md 新版定稿   # 新版定稿：文章本身也会改（撞词去掉重点词等）；路径不存在 git 会报错，set -e 当场停（G3：不许悄悄没提交）
big=$(git diff --cached --name-only -z | xargs -0 -r du -b 2>/dev/null | awk '$1>95*1024*1024{print $2}')
[ -z "$big" ] || { echo "【停止】有文件超过 GitHub 单个文件 100MB 上限（G1）：$big——先拆成几段（附 SHA256 和还原脚本）"; git reset -q; exit 1; }
if ! git diff --cached --quiet; then git commit -qm "$1$T"; fi
git pull -q --no-rebase --no-edit origin main || python3 $P/视频/工具/新管/合并追加.py || exit 1   # 新管：追加型记录自动合并；2026-10-22：别的会话（每篇新开会话）可能先推了，先合并远端再算差异、再推
(cd $L; git checkout -q -- 视频 2>/dev/null; { git pull -q --no-rebase --no-edit origin $B || python3 $P/视频/工具/新管/合并追加.py; })   # 镜像分支先合并别的会话推的
# G58（2026-10-26 GitHub 化）：GitHub 工作流（github-actions[bot]）写回镜像的结果，先反向回写主仓库（含删除），不被主仓库的旧版本覆盖。
# 镜像上 bot 最后一次改这个文件、且比主仓库这份新才回写；只认白名单（印章、视频/云端/结果/、本次请求篇号 NN 的成片与记录，主会话 2026-10-26 定），
# bot 改了白名单外的文件 → 停（工作流越权写，不许悄悄混进主仓库）。
python3 - "$P" "$L" <<'PYW' || exit 1
import sys, os, re, subprocess, shutil, fnmatch
P, L = sys.argv[1:3]; BOT = 'github-actions[bot]'
g = lambda r, *a: subprocess.run(['git', '-c', 'core.quotepath=off', '-C', r, *a], capture_output=True, text=True).stdout
nn, 草 = set(), set()   # 请求篇号：镜像里 视频/云端/请求/*.txt（一个请求一个文件）中 出片/定稿/草稿 请求写的篇号
import glob
for rf in glob.glob(f'{L}/视频/云端/请求/*.txt') + [f'{L}/视频/云端/演练请求.txt']:
    try: w = next((l.split() for l in open(rf) if l.strip() and not l.lstrip().startswith('#')), [])
    except FileNotFoundError: continue
    if w and w[0] in ('出片', '定稿', '草稿'): nn |= {x for x in w[1:] if re.fullmatch(r'\d\d', x)}
    if w and w[0] == '草稿': 草 |= {x for x in w[1:] if re.fullmatch(r'\d\d', x)}   # 阶段 B：草稿 NN 在 GitHub 跑 草稿声音.sh，切点、确认写进脚本（定稿不许改脚本，G19）
白 = ['视频/工具/执行效应演练通过.json', '视频/工具/执行效应声音演练通过.json', '视频/工具/全篇重查通过.json', '视频/云端/结果/*']
for n in nn: 白 += [f'视频/视频/{n}.mp4', f'视频/视频/草稿1080p/{n}_*', f'最终版4K视频/{n} *', '最终版4K视频/README.md', f'新版定稿/{n}-*',
                    f'视频/制作记录/{n}.md', f'视频/制作记录/{n}_*', f'视频/制作记录/逐句确认/{n}.json', f'视频/制作记录/证据/{n}*',
                    f'视频/脚本/已发版本/{n}.json', f'视频/音频核对/*_{n}.txt', f'视频/音频核对/*_{n}_*.txt']
for n in 草: 白 += [f'视频/脚本/{n}.json']
ok = lambda f: any(fnmatch.fnmatchcase(f, w) for w in 白)
for f in g(L, 'ls-files', '--', '视频/云端/请求/', '视频/云端/待演练/', '视频/云端/结果/').splitlines():   # K45：待演练补丁、本地结果同样只增不删（2026-10-27 镜像同步抹掉了只在镜像的交接补丁）；K24：会话直接放在镜像里的请求只增不删：拷回主仓库（之后两边一致，主仓库推过去不算“新加”、不会重跑）
    if f and not os.path.exists(f'{P}/{f}'): os.makedirs(os.path.dirname(f'{P}/{f}'), exist_ok=True); shutil.copy2(f'{L}/{f}', f'{P}/{f}'); g(P, 'add', '--', f); print(f'回写请求（K24）：{f}')
_浅 = set(open(f'{L}/.git/shallow').read().split()) if os.path.exists(f'{L}/.git/shallow') else set()   # K47：浅克隆的边界提交没有父提交，git log 把它当成“新加了全部文件”，误报白名单外
fs, _cur = set(), ''
for x in g(L, 'log', '-300', '--author=' + re.escape(BOT), '--name-only', '--format=@%H').splitlines():
    if x.startswith('@'): _cur = x[1:]
    elif x and _cur not in _浅: fs.add(x)
bad, n_ = [], 0
for f in sorted(fs):
    la = g(L, 'log', '-1', '--format=%an %ct', '--', f).rsplit(' ', 1); pt = int(g(P, 'log', '-1', '--format=%ct', '--', f).strip() or 0)
    if len(la) < 2 or la[0] != BOT or int(la[1]) <= pt: continue
    inL, inP = os.path.exists(f'{L}/{f}'), os.path.exists(f'{P}/{f}')
    if inL and inP and open(f'{L}/{f}', 'rb').read() == open(f'{P}/{f}', 'rb').read(): continue
    if not inL and not inP: continue
    if not ok(f): bad.append(f); continue
    if inL: os.makedirs(os.path.dirname(f'{P}/{f}'), exist_ok=True); shutil.copy2(f'{L}/{f}', f'{P}/{f}'); g(P, 'add', '--', f); print(f'回写（G58）：{f}')
    else: g(P, 'rm', '-q', '--', f); print(f'回写删除（G58）：{f}')
    n_ += 1
if bad: sys.exit('【停止】GitHub 工作流改了白名单外的文件（G58，篇号 ' + (' '.join(sorted(nn)) or '无') + '）：' + '；'.join(bad[:5]))
PYW
git diff --cached --quiet || git commit -qm "回写：GitHub 工作流结果（G58）$T"
python3 "$HERE/新管/合回镜像.py" "$P" "$L" || exit 1   # 只能推镜像的会话推到镜像上的改动先按文件合回 main，不许盖掉（主会话 2026-10-29：31 的配音缓存、31.md 被冲了两次）
git diff --cached --quiet || git commit -qm "合回：别的会话只推到镜像的改动$T"
D='视频 最终版4K视频 新版定稿'
TP=$(mktemp); TL=$(mktemp)   # 2026-10-26：清单原写死 /tmp/_p.txt、/tmp/_l.txt，演练里几场推送自检同时跑互相覆盖，复制错文件（G58 演练在 GitHub 上偶发失灵查出）   # G20：三个都镜像（只镜像 视频/ 时，定稿流水线 ⑥ 中断后用本脚本补推，镜像里的 4K 和文章一直是旧的）
# 2026-10-23：按两边 git 指纹逐文件比对来拷（只拷“这次改动”会漏掉两个会话合并出来的文件）
git -c core.quotepath=off ls-tree -r HEAD $D | awk -F'\t' '{split($1,a," "); print a[3]"\t"$2}' | sort -k2 > $TP
(cd $L; git -c core.quotepath=off ls-tree -r HEAD $D | awk -F'\t' '{split($1,a," "); print a[3]"\t"$2}' | sort -k2) > $TL
python3 - "$P" "$L" "$TP" "$TL" <<'PY2'
import sys,shutil,os
P,L,TP,TL=sys.argv[1:5]
p=dict(l.rstrip('\n').split('\t')[::-1] for l in open(TP)); q=dict(l.rstrip('\n').split('\t')[::-1] for l in open(TL))
for f,h in p.items():
    if q.get(f)!=h: os.makedirs(os.path.dirname(f'{L}/{f}'),exist_ok=True); shutil.copy(f'{P}/{f}',f'{L}/{f}')   # K48：不用 copy2，保留修改时刻、大小又一样时 git 按缓存当没改，镜像漏提交
for f in q:
    if f not in p and os.path.exists(f'{L}/{f}'): os.remove(f'{L}/{f}')
PY2
git push -q origin main || { git pull -q --no-rebase --no-edit origin main && git push -q origin main; }   # 别的会话刚推了：合并一次再推
cp $P/CLAUDE.md $L/CLAUDE.md   # CLAUDE.md 以 postgraduate-vocabulary 为准（G11：定稿流水线用它覆盖工作分支，只改工作分支那份会被冲掉）
cd $L; git symbolic-ref -q HEAD >/dev/null || git checkout -q -B $B   # 新容器 L 可能是游离 HEAD：分支挪到 HEAD 再推（2026-10-23 T34 九篇因此停）
git add -A
if ! git diff --cached --quiet; then git commit -qm "镜像：$1"$'\n\n'"主仓库提交：$(git -C $P rev-parse HEAD)$T"; fi   # 主仓库提交：合回镜像 靠这一行认同步提交（只看“镜像：”开头不够，别的会话也可能这样写）
git push -q -u origin $B || { git pull -q --no-rebase --no-edit origin $B && git push -q -u origin $B; }
diff <(git -C $P ls-tree -r HEAD $D | awk '{print $3,$4}') <(git -C $L ls-tree -r HEAD $D | awk '{print $3,$4}') >/dev/null \
  && cmp -s $P/CLAUDE.md $L/CLAUDE.md && [ -z "$(git -C $P status --short)" ] && [ -z "$(git -C $L status --short)" ] \
  && git -C $P fetch -q origin main && git -C $L fetch -q origin $B \
  && git -C $P merge-base --is-ancestor HEAD origin/main && git -C $L merge-base --is-ancestor HEAD origin/$B \
  && echo "两仓库已推送，视频/ 逐文件一致，云端已含这次提交（G2；别的会话紧接着推了也算对）" && { [ -n "$PUSH_P" ] || python3 $P/视频/工具/报坑.py --放锁 --静默 2>/dev/null || true; } || { echo "【停止】两仓库 视频/ 不一致、有没提交的改动，或云端与本地不一致（G2）"; exit 1; }
