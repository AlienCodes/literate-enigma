#!/usr/bin/env python3
"""把旧工具目录接上“看门开关”。每处只加一个判断，读 <工具>/管道.json 的 {"看门": "停用"|"启用"}；
切换 = 改这一个配置（停用由主会话写 用户同意记录 后再改）。补丁可重复打（已打过的跳过），锚找不到就停。
用法：python3 新管/切换.py <工具目录> [--停用|--启用]"""
import sys, os, json
H = os.path.dirname(os.path.abspath(__file__))
G = "__import__('管道').看门停用()"
补丁 = [   # (文件, 原文, 新文)：原文必须正好出现一次。K102（读音核对 自检）不在这里：第七棒单独一趟先上 main（改门待演练/K102读音自检.diff）
    ('交付核查.py', "if stage in ('出片前', '出片后'):   # G60", f"if stage in ('出片前', '出片后') and not {G}:   # G60"),
    ('交付核查.py', "    c, o = run(['python3', f'{T}/规则执行核查.py']); step('规则执行核查（守则16：每条规矩都有门、接进流程、有自检，机器自检通过）', c == 0, '' if c == 0 else o.strip()[-600:])\n    c, o = run(['python3', f'{T}/用上核查.py', '--严'])",
     f"    if not {G}: c, o = run(['python3', f'{{T}}/规则执行核查.py']); step('规则执行核查（守则16：每条规矩都有门、接进流程、有自检，机器自检通过）', c == 0, '' if c == 0 else o.strip()[-600:])\n    if not {G}: c, o = run(['python3', f'{{T}}/用上核查.py', '--严'])"),
    ('交付核查.py', "elif stage == '出片后':\n    c, o = run(['python3', f'{T}/规则执行核查.py'])", f"elif stage == '出片后':\n    if not {G}: c, o = run(['python3', f'{{T}}/规则执行核查.py'])"),
    ('交付核查.py', "if ok and stage in ('出片前', '出片后'): _ZJ.记(no, stage)", f"if ok and stage in ('出片前', '出片后') and not {G}: _ZJ.记(no, stage)"),
    ('交付核查.py', "if not ok:   # K 丝滑记录", f"if not ok and not {G}:   # K 丝滑记录"),
    ('草稿声音.sh', "python3 $T/证据.py --记 $no 草稿声音", "[ \"$(python3 -c \"import sys;sys.path.insert(0,'$T');print(__import__('管道').看门停用())\")\" = True ] || python3 $T/证据.py --记 $no 草稿声音"),
    ('生成文本.py', "_m = subprocess.run(['python3', f'{T}/规则执行核查.py'], capture_output=True, text=True)", f"_m = subprocess.run(['true'] if (sys.path.insert(0, T) or {G}) else ['python3', f'{{T}}/规则执行核查.py'], capture_output=True, text=True)"),
    ('推送两仓库.sh', 'python3 $P/视频/工具/规则执行核查.py || { echo "【停止】规则执行核查不通过', 'if [ "$(python3 -c "import sys;sys.path.insert(0,\'$P/视频/工具\');print(__import__(\'管道\').看门停用())")" = True ]; then python3 $P/视频/工具/新管/印章.py || { echo "【停止】快测印章对不上：程序改过没过快测（python3 视频/工具/新管/快测.py）"; exit 1; }; else python3 $P/视频/工具/规则执行核查.py; fi || { echo "【停止】规则执行核查不通过'),
    ('推送两仓库.sh', "  python3 $P/视频/工具/报坑.py --查 --严 ||", "  python3 -c \"import sys;sys.path.insert(0,'$P/视频/工具');sys.exit(0 if __import__('管道').看门停用() else 1)\" || python3 $P/视频/工具/报坑.py --查 --严 ||"),
    ('草稿声音.sh', 'no=$1; T=/home/user/postgraduate-vocabulary/视频/工具', 'no=$1; T=${XG_TOOLS:-/home/user/postgraduate-vocabulary/视频/工具}'),
    ('快速重建核查.sh', 'no=$1; T=/home/user/postgraduate-vocabulary/视频/工具', 'no=$1; T=${XG_TOOLS:-/home/user/postgraduate-vocabulary/视频/工具}'),
    ('render.py', "    NOTE_RIGHT.clear(); _RIGHT_USE.clear()   # G37", "    _n = len(d.get('sentences', []))   # G35 常规规则（用户 2026-10-25 看 26：“以后以后一定要合理的安排，不要压缩成这个样子”，27 又说一次；用户同意记录 篇 26）：25 起结尾简述一律整屏，不再要每篇特批；写了特批的照特批\n    if _n and str(d.get('no', '0')).isdigit() and int(d['no']) >= 25 and f'S{_n}' not in d.get('说明放宽特批', {}) and '（简述：' in (d['sentences'][-1]['chunks'][-1].get('note') or ''):\n        NOTE_WIDE[' '.join(p[0] for c in d['sentences'][-1]['chunks'] for p in c['align'])] = '整屏'\n    NOTE_RIGHT.clear(); _RIGHT_USE.clear()   # G37"),
    ('推送两仓库.sh', "git pull -q --no-rebase --no-edit origin main   # 2026-10-22", "git pull -q --no-rebase --no-edit origin main || python3 $P/视频/工具/新管/合并追加.py || exit 1   # 新管：追加型记录自动合并；2026-10-22"),
    ('推送两仓库.sh', "git pull -q --no-rebase --no-edit origin $B)   # 镜像分支", "{ git pull -q --no-rebase --no-edit origin $B || python3 $P/视频/工具/新管/合并追加.py; })   # 镜像分支"),
    ('方法进化表.py', "def 汇总(rec=REC, 目录=None):",
     "def 出过片(no, rec=None):   # K97（主会话 2026-10-28）：只算已经出过片（有出片后 收工记录）的篇；排队中的、只有交接的篇不算\n    f = f'{rec or REC}/{no}.md'\n    return (not os.path.exists(f)) or '\\n- 收工 ' in open(f).read()\n\n\ndef 汇总(rec=REC, 目录=None):"),
    ('方法进化表.py', "    for no, v in 篇.items():\n        ss = v['会话']", "    for no, v in 篇.items():\n        if not 出过片(no, rec): continue   # K97：排队中、没出过片的篇不进比较\n        ss = v['会话']"),
    ('方法进化表.py', "    if no not in 行: return [f'【G65 方法进化】{no} 没有一条 token 记录", "    if no not in 行 and not 出过片(no): return [], ''   # K97：还在排队、没出过片的篇（开下一篇时查上一篇）不拦\n    if no not in 行: return [f'【G65 方法进化】{no} 没有一条 token 记录"),
    ('推送自检.py', "    if open(f'{L}/CLAUDE.md').read() != '新守则\\n': fails.append('没抓到：CLAUDE.md 没以 postgraduate-vocabulary 为准（G11）')\n", '    if open(f\'{L}/CLAUDE.md\').read() != \'新守则\\n\': fails.append(\'没抓到：CLAUDE.md 没以 postgraduate-vocabulary 为准（G11）\')\n    # 新管：看门停用时推送前查快测印章，印章对不上必停（管道.json 是“启用”时也在这里演练这条分支，门变异才抓得到）\n    写(f\'{P}/视频/工具/管道.py\', open(f\'{T}/管道.py\').read()); 写(f\'{P}/视频/工具/管道.json\', \'{"看门": "停用"}\'); 写(f\'{P}/视频/工具/新管/印章.py\', \'import sys; sys.exit(1)\\n\'); 写(f\'{P}/视频/印章测.md\', \'x\\n\')\n    r = run(); o = r.stdout + r.stderr\n    if r.returncode == 0 or \'快测印章对不上\' not in o: fails.append(f\'没抓到：看门停用时快测印章对不上，推送没停（新管）{o.strip()[-80:]}\')\n    for f_ in (\'视频/工具/管道.py\', \'视频/工具/管道.json\', \'视频/工具/新管/印章.py\', \'视频/印章测.md\'): os.remove(f\'{P}/{f_}\')\n    git(\'reset\', \'-q\', cwd=P)\n'),
]
# 提交前钩子的改法（切换推送时由主会话批准后做，本程序不碰钩子文件，K16）：看门停用时只查快测印章（新管/印章.py），不再跑 会话开工 --提交前、规则执行核查
管道 = '''import json, os
def 看门停用():
    """新管开关：<工具>/管道.json 写 {"看门": "停用"} 时，8 套看门机制（证据、闲置、用上核查、门变异、放行口子、规则执行核查、演练、丝滑）不再当门"""
    try: return json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '管道.json'))).get('看门') == '停用'
    except Exception: return False
'''

登记 = {   # (类, 键): 用途
    ('开关', 'XG_TOOLS'): '新管：检查程序目录（默认 视频/工具；验收在副本上跑时指过去）；不放宽任何检查',
    ('开关', 'XG_P'): '新管：主仓库根目录（默认 /home/user/postgraduate-vocabulary）；不放宽任何检查',
    ('开关', 'XG_WORK'): '新管 快测：出片工作目录；不放宽任何检查',
    ('开关', 'XG_NO'): '新管 快测：回归篇号（默认 27）；不放宽任何检查',
    ('起查', '修.py:25'): 'G35 结尾简述整屏常规 25 起（用户 2026-10-25 原话，用户同意记录 篇 26）',
}

新管用途 = {
    '做.py': '新管：一条命令从数据到 1080p 草稿（做.sh 的主体）', '做.sh': '新管：草稿入口（管道.json 看门停用后的正式入口）',
    '定稿.sh': '新管：4K 定稿入口（疑点清零、成片指纹、归档、推送）', '修.py': '新管：机械错误的标准修法（破折号、L19 折行、G35 简述整屏）',
    '快测.py': '新管：改规则/程序后的门（坏样本必抓、27 回归、印章）', '印章.py': '新管：快测印章（程序哈希），提交、推送、出片前查',
    '生成规则表.py': '新管：从规则执行表等生成规则表.json', '生成写稿须知.py': '新管：从规则表生成写稿须知.md',
    '画面哈希.py': '新管：快测 27 回归的每屏像素哈希', '合并追加.py': '新管：推送 pull 撞追加型记录时三方自动合并（K100）',
    '推送.sh': '新管：推送两仓库外壳，G2/被拒自动重推', '切换.py': '新管：切换补丁和 管道.json 开关',
    '切换变异测.py': '新管：切换补丁的本地门变异', '并发测.py': '新管：三会话并发推送验收', '从零测.sh': '新管：全新浅克隆从零验收',
    '对比4K.py': '新管：定稿 4K 与存档逐样本逐帧对比', '原话存档.py': '新管：CLAUDE.md 一页化前的用户原话存档与核对',
}

def 有同意(t):
    """停用 8 套看门只认用户原话：用户同意记录 里 用于 含“管道.json 看门 停用”、原话有字、来源不是演练"""
    try: R = json.load(open(f'{t}/用户同意记录.json'))['记录']
    except Exception: return False
    return any('管道.json 看门 停用' in r.get('用于', '') and len(r.get('原话', '').strip()) >= 6 and r.get('来源') != '演练' for r in R)

def main():
    t = sys.argv[1]; bad = []
    open(f'{t}/管道.py', 'w').write(管道)
    for f, a, b in 补丁:
        p = f'{t}/{f}'; s = open(p).read()
        if b in s: continue
        if s.count(a) != 1: bad.append(f'{f}：锚出现 {s.count(a)} 次：{a[:50]}'); continue
        open(p, 'w').write(s.replace(a, b))
    k = f'{t}/放行口子表.json'   # 新管程序里的路径开关、起查要登记（G24 放行口子核查；不放宽任何检查）
    if os.path.exists(k):
        tb = json.load(open(k)); 改 = False
        for 名, 用 in 登记.items():
            for 类, 键 in [名]:
                if tb.setdefault(类, {}).get(键) != 用: tb[类][键] = 用; 改 = True
        if 改: json.dump(tb, open(k, 'w'), ensure_ascii=False, indent=1)
    k = f'{t}/机制清单.json'   # 新管程序登记“辅助”（用上核查：没登记 = 孤儿）；用途写清，切换后由 做.sh/定稿.sh 正式调用
    if os.path.exists(k):
        m = json.load(open(k)); 辅 = m.setdefault('辅助', {}); 改 = False
        for 名, 用 in 新管用途.items():
            if 辅.get(f'新管/{名}') != 用: 辅[f'新管/{名}'] = 用; 改 = True
        if 改: json.dump(m, open(k, 'w'), ensure_ascii=False, indent=1)
    if '--停用' in sys.argv and not 有同意(t):
        print('【停止】用户同意记录.json 里还没有“管道.json 看门 停用”的用户原话（主会话记；篇“全部”、用于含“管道.json 看门 停用”、来源不是演练），不切换'); sys.exit(1)
    if '--停用' in sys.argv or '--启用' in sys.argv:
        json.dump({'看门': '停用' if '--停用' in sys.argv else '启用'}, open(f'{t}/管道.json', 'w'), ensure_ascii=False)
    print('\n'.join(bad) or f'补丁 {len(补丁)} 处已打；开关 {t}/管道.json')
    sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
