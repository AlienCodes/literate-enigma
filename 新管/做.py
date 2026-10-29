#!/usr/bin/env python3
"""做：一条命令从数据到 1080p 草稿（在出片工作目录下运行；做.sh 是它的外壳）。
  ⓪ 快测印章（程序改了没过快测就停）
  ① 文本：机械修（破折号、L19 折行）→ 踩坑核查。✘ 错 → 停；？ 待确认 → 疑点表
  ② 声音：草稿声音.sh（结尾句接点、自动切点、词尾除阻、句内响度这些标准修法都在里面，缓存命中只重做改过的句子）
  ③ 出片前核查（交付核查，看门已停用：只剩真检查）。✘ → 停（读音待核实、停顿、词尾……指出哪句哪词）
  ④ 出 1080p → ⑤ 出片后核查。只有“响度骤降要用户听”算疑点；别的 ✘ → 停
  ⑥ 拷 视频/视频/草稿1080p/NN_1080p.mp4、脚本、已发版本；疑点表写 制作记录/NN_疑点.md → 推两仓库 → ⑦ 一页报告
结果只有三种：通过 / 修了（列出改了什么）/ 疑点（片子照出，疑点表跟着发）；停 = 机器修不了又不是疑点。
用法：python3 做.py NN [--不推]"""
import sys, os, re, json, subprocess, time, shutil
H = os.path.dirname(os.path.abspath(__file__))
T = os.environ.get('XG_TOOLS') or (os.path.dirname(H) if os.path.exists(f'{os.path.dirname(H)}/交付核查.py') else f'{os.path.dirname(H)}/视频/工具')
P = os.environ.get('XG_P', '/home/user/postgraduate-vocabulary'); V = f'{P}/视频'
no = sys.argv[1].zfill(2); 推 = '--不推' not in sys.argv; t0 = time.time()
LOG = os.path.abspath(f'做_{no}'); os.makedirs(LOG, exist_ok=True)
报告, 修了, 疑点 = [], [], []
env = {**{k: v for k, v in os.environ.items() if k != 'OLD_IV_VOID'}, 'XG_TOOLS': T}

def 跑(name, cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, env={**env, **kw.pop('extra', {})}, **kw)
    o = r.stdout + r.stderr; open(f'{LOG}/{name}.log', 'w').write(o); return r.returncode, o

def 停(步, 行):
    print('\n'.join(报告 + [f'【停】{步}（{time.time() - t0:.0f} 秒；全文在 {LOG}/）：'] + [f'  {l}' for l in 行[:30]]
                    + ([f'  已自动修：'] + [f'    {x}' for x in 修了] if 修了 else [])))
    sys.exit(1)

# ⓪
if not (os.path.exists('make_video.py') and os.path.exists(f'scripts/{no}.json')): 停('⓪ 工作目录', [f'请在出片工作目录运行（要有 make_video.py、scripts/{no}.json）'])
c, o = 跑('工作目录程序', ['python3', f'{T}/出片指纹.py', '--核对工作目录', '.'])
if c:   # 机械：工作目录的出片程序比仓库旧（G27），照现有做法拷过来
    c, o = 跑('拷出片程序', ['python3', f'{T}/出片指纹.py', '--拷', '.'])
    if c: 停('⓪ 拷出片程序', o.strip().splitlines()[-3:])
    修了.append('工作目录的出片程序比仓库旧，已按 出片指纹.py --拷 拷过来（G27）')
c, o = 跑('印章', ['python3', f'{H}/印章.py'], extra={'XG_TOOLS': T})
if c: 停('⓪ 快测印章', o.strip().splitlines())
if os.path.exists(f'{T}/初稿生成/gen{no}.py') and os.path.getmtime(f'{T}/初稿生成/gen{no}.py') > os.path.getmtime(f'scripts/{no}.json'):
    c, o = 跑('生成', ['python3', f'{T}/初稿生成/gen{no}.py'])
    if c: 停('⓪ genNN 生成脚本', o.strip().splitlines()[-8:])
# ①
c, o = 跑('修', ['python3', f'{H}/修.py', no], extra={'XG_TOOLS': T})
修了 += [l for l in o.splitlines() if l.strip() and not l.startswith('错：')]
if any(l.startswith('错：') for l in o.splitlines()): 停('① 机械修', [l[2:] for l in o.splitlines() if l.startswith('错：')])
c, o = 跑('文本', ['python3', f'{T}/踩坑核查.py', no, '出片'])
错 = [l.strip()[2:] for l in o.splitlines() if l.strip().startswith('✘')]
if '【核查程序失灵' in o: 停('① 踩坑核查自检失灵', o.strip().splitlines()[-3:])
if 错: 停('① 文本（改 genNN 数据或脚本后重跑 做.sh）', 错)
疑点 += [('文本', l.strip()[2:]) for l in o.splitlines() if l.strip().startswith('？')]
import glob as _gl, tempfile as _tf   # K98（28 定稿到 ④ 文章同步才查出速查表缺 11 个新重点词）：文章同步在 ① 先试跑一遍（临时副本，不改文章）
_md = _gl.glob(f'{P}/新版定稿/{no}-*.md')
if _md:
    with _tf.TemporaryDirectory() as _td:
        shutil.copy(_md[0], f'{_td}/a.md'); c, o = 跑('文章同步试跑', ['python3', f'{T}/sync_article.py', os.path.abspath(f'scripts/{no}.json'), f'{_td}/a.md'], cwd=P)
    if c or '【停止】' in o: 停('① 文章同步试跑（速查表缺词性词义等，K98）', [l for l in o.splitlines() if '停止' in l or 'Error' in l][:5] or o.strip().splitlines()[-3:])
报告.append(f'① 文本：通过' + (f'，疑点 {len(疑点)} 处' if 疑点 else '') + (f'，自动修 {len(修了)} 处' if 修了 else ''))
# ②
c, o = 跑('声音', ['bash', f'{T}/草稿声音.sh', no])
for l in o.splitlines():
    if '人看' in l: 疑点.append(('纯人声（人看）', l.strip()))
报告.append('② 声音：' + '；'.join(l.strip() for l in o.splitlines() if '问题数' in l)[:200])
# ③
c, o = 跑('出片前', ['python3', f'{T}/交付核查.py', no, '出片前'])
x = [l for l in o.split('\n✘ ')[1:]] if c else []
x = [b for b in x if not b.startswith('踩坑核查（') or 错]   # 踩坑核查那一步只因“？”不过：已进疑点表
if x: 停('③ 出片前核查', ['✘ ' + b.strip()[:400] for b in x])
报告.append('③ 出片前核查：通过')
# ④
c, o = 跑('出片', ['python3', 'make_video.py', f'scripts/{no}.json', f'{no}.mp4'])
if c: 停('④ 出 1080p', o.strip().splitlines()[-10:])
# ⑤
c, o = 跑('出片后', ['python3', f'{T}/交付核查.py', no, '出片后'])
bs = [b for b in o.split('\n✘ ')[1:]] if c else []
for b in bs:
    if b.startswith('自动音频检查') and '响度比全片低' in b and not re.search(r'削波|电流|停顿超长|程序出错', b):
        疑点 += [('响度骤降（剪成试听交用户听）', l.strip()) for l in b.splitlines() if '响度比全片低' in l]
    else: 停('⑤ 出片后核查', ['✘ ' + b.strip()[:400] for b in bs])
报告.append('⑤ 出片后核查：' + ('全部通过' if not bs else '只剩疑点'))
# ⑥
os.makedirs(f'{V}/视频/草稿1080p', exist_ok=True)
shutil.copy(f'{no}.mp4', f'{V}/视频/草稿1080p/{no}_1080p.mp4'); shutil.copy(f'scripts/{no}.json', f'{V}/脚本/{no}.json')
os.makedirs(f'{V}/脚本/已发版本', exist_ok=True); shutil.copy(f'scripts/{no}.json', f'{V}/脚本/已发版本/{no}.json')   # L13：下次比换行的基准
for f in [f'标点试听_{no}.mp3']:
    if os.path.exists(f): shutil.copy(f, f'{V}/音频核对/{f}')
rec = f'{V}/制作记录/{no}.md'; 撞 = ''
if os.path.exists(rec):
    m = re.search(r'## 撞车提醒\n(.*?)(?=\n## |\Z)', open(rec).read(), re.S); 撞 = m.group(1).strip() if m else ''
疑表 = [f'# 第{no}篇 疑点表（{time.strftime("%Y-%m-%d %H:%M")}，做.sh）', '', '定稿前必须清零：修掉，或 用户同意记录 里有用户原话。', '']
疑表 += [f'- [{k}] {v}' for k, v in 疑点] or ['- 无']
if 修了: 疑表 += ['', '## 机器自动修了（请过目）'] + [f'- {x}' for x in 修了]
if 撞: 疑表 += ['', '## 撞车提醒（G34：告诉用户，先留着）', 撞]
open(f'{V}/制作记录/{no}_疑点.md', 'w').write('\n'.join(疑表) + '\n')
import hashlib   # 成片指纹（替代证据链）：定稿.sh 核对“定稿的就是用户看过的这一版”（数据、声音一致）
_h = lambda f: hashlib.sha256(open(f, 'rb').read()).hexdigest()[:16]
json.dump({'数据': _h(f'scripts/{no}.json'), '声音': _h(f'work_{no}/a.wav'), '片': _h(f'{no}.mp4'), '规则表版本': json.load(open(f'{H}/规则表.json'))['版本'],
           '快测印章': _h(f'{H}/快测通过.json'), '时刻': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())},
          open(f'{V}/制作记录/{no}_做指纹.json', 'w'), ensure_ascii=False, indent=0)
if 推:
    c, o = 跑('推送', ['bash', f'{H}/推送.sh', f'第{no}篇 草稿1080p（做.sh）：疑点 {len(疑点)}、自动修 {len(修了)}'], cwd=P)
    if c: 停('⑥ 推送两仓库', o.strip().splitlines()[-6:])
报告.append(f'⑥ 已拷 视频/视频/草稿1080p/{no}_1080p.mp4' + ('，两仓库已推送' if 推 else '（--不推）'))
c, o = 跑('报坑', ['python3', f'{T}/报坑.py', '--查'])   # 硬问题（撞号、没取号）停；超期只提醒（用户 2026-10-29：“直接一刀切把它砍掉了”）
if c: 停('⑥ 报坑登记有硬问题（G54）', [l.strip() for l in o.splitlines() if '✘' in l])
超 = [l.strip() for l in o.splitlines() if '超期' in l]
if 超: 报告.append(f'提醒：报坑登记 {len(超)} 条超期没入表（只提醒不拦）')
# ⑦
print('\n'.join([f'第{no}篇 做完（{time.time() - t0:.0f} 秒）：' + ('通过' if not 疑点 and not 修了 else f'修了 {len(修了)} 处、疑点 {len(疑点)} 处')] + 报告
                + [f'疑点表：视频/制作记录/{no}_疑点.md（跟着片子发给用户）'] + [f'  · [{k}] {v[:120]}' for k, v in 疑点[:20]]
                + [f'  修：{x[:120]}' for x in 修了[:20]] + (['撞车提醒：见疑点表'] if 撞 else [])))
