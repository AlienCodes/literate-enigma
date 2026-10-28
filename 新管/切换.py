#!/usr/bin/env python3
"""把旧工具目录接上“看门开关”。每处只加一个判断，读 <工具>/管道.json 的 {"看门": "停用"|"启用"}；
切换 = 改这一个配置（停用由主会话写 用户同意记录 后再改）。补丁可重复打（已打过的跳过），锚找不到就停。
用法：python3 新管/切换.py <工具目录> [--停用|--启用]"""
import sys, os, json
H = os.path.dirname(os.path.abspath(__file__))
G = "__import__('管道').看门停用()"
补丁 = [   # (文件, 原文, 新文)：原文必须正好出现一次
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
    ('推送两仓库.sh', "git push -q origin main || { git pull -q --no-rebase --no-edit origin main && git push -q origin main; }", "git push -q origin main || { { git pull -q --no-rebase --no-edit origin main || python3 $P/视频/工具/新管/合并追加.py; } && git push -q origin main; }"),
    ('推送两仓库.sh', "git push -q -u origin $B || { git pull -q --no-rebase --no-edit origin $B && git push -q -u origin $B; }", "git push -q -u origin $B || { { git pull -q --no-rebase --no-edit origin $B || python3 $P/视频/工具/新管/合并追加.py; } && git push -q -u origin $B; }"),
    ('方法进化表.py', "def 汇总(rec=REC, 目录=None):",
     "def 出过片(no, rec=None):   # K97（主会话 2026-10-28）：只算已经出过片（有出片后 收工记录）的篇；排队中的、只有交接的篇不算\n    f = f'{rec or REC}/{no}.md'\n    return (not os.path.exists(f)) or '\\n- 收工 ' in open(f).read()\n\n\ndef 汇总(rec=REC, 目录=None):"),
    ('方法进化表.py', "    for no, v in 篇.items():\n        ss = v['会话']", "    for no, v in 篇.items():\n        if not 出过片(no, rec): continue   # K97：排队中、没出过片的篇不进比较\n        ss = v['会话']"),
    ('方法进化表.py', "    if no not in 行: return [f'【G65 方法进化】{no} 没有一条 token 记录", "    if no not in 行 and not 出过片(no): return [], ''   # K97：还在排队、没出过片的篇（开下一篇时查上一篇）不拦\n    if no not in 行: return [f'【G65 方法进化】{no} 没有一条 token 记录"),
    ('读音核对.py', '    # ② 关掉读音改正\n    used = [w for w in PRON_WORDS if re.search(r\'(?<![A-Za-z])\' + re.escape(w) + r\'(?![A-Za-z])\', text, flags=re.I)\n            and re.sub(r\'\\s\', \'\', PRON_WORDS[w]) != re.sub(r\'\\s|[,;:.!?]\', \'\', KT.tokenizer.phonemize(w, \'en-us\'))   # McArthur 只差一个空格，听不出，不拿来测\n            and not (w[0].islower() and str(_FIXJ.get(w, {}).get(\'判定\', \'\')).startswith(\'可接受\'))]   # 普通词的“可接受但改”（10 glazier：原读法词典也收）关掉改正本来就不算读错，不拿来测\n    if used:\n        keep = dict(PRON_WORDS); PRON_WORDS.clear()\n        got = {line for _, line, bad in check(no) if bad}; PRON_WORDS.update(keep)\n        res.append((f\'关掉读音改正（{"、".join(used)}）\', all(any(re.search(r\'\\] \' + re.escape(w) + r"([\'’]s)? ", l_) for l_ in got - base) for w in used)))   # 文中只有所有格的（10 Uffizi\'s）也算\n', '    # ② 关掉读音改正（K102 2026-10-28：逐个词单独关掉，只有在本篇句子里关掉会变读音的才当样本；一个都没有就造假样本，不许跳过；另查改正确实生效）\n    used = [w for w in PRON_WORDS if re.search(r\'(?<![A-Za-z])\' + re.escape(w) + r\'(?![A-Za-z])\', text, flags=re.I)\n            and re.sub(r\'\\s\', \'\', PRON_WORDS[w]) != re.sub(r\'\\s|[,;:.!?]\', \'\', KT.tokenizer.phonemize(w, \'en-us\'))   # McArthur 只差一个空格，听不出，不拿来测\n            and not (w[0].islower() and str(_FIXJ.get(w, {}).get(\'判定\', \'\')).startswith(\'可接受\'))]   # 普通词的“可接受但改”（10 glazier）关掉改正本来就不算读错\n    _nz = lambda x: re.sub(r\'[\\s,;:.!?"“”]\', \'\', x)   # 重音符号要留着（Tambora 只差重音）\n    dead = [w for w in used if _nz(phonemes_of(w)) == _nz(KT.tokenizer.phonemize(w, \'en-us\'))]   # 门在：表里有改正，单读却还是 espeak 原读法 = 改正没生效\n    if dead: res.append((f\'读音改正生效（{"、".join(dead)} 有改正却照 espeak 原样读）\', False))\n    valid = []\n    for w in used:   # 样本照真门判（主会话 2026-10-28）：单独关掉这个词的改正，check() 在本篇对这个词报 BAD，就是样本\n        keep_w = PRON_WORDS.pop(w); got = {line for _, line, bad in check(no) if bad}; PRON_WORDS[w] = keep_w\n        hit = any(re.search(r\'\\] \' + re.escape(w) + r"([\'’]s)? ", l_) for l_ in got - base)   # 文中只有所有格的（10 Uffizi\'s）也算\n        print(f\'  K102 ② {w}：单独关掉改正 → \' + (\'报 BAD（当样本）\' if hit else \'不报（关掉后仍读对，不当样本）\'))\n        if hit: valid.append(w)\n    if valid:\n        res.append((f\'关掉读音改正（{"、".join(valid)}）\', True))\n    elif tgt:   # 本篇没有在句子里起作用的改正：照 ① 造一条假改正（单读对、整句被“模型”读坏，改正关掉必须报出）\n        w, ph = tgt; bad_ph = _moved(ph)\n        def fake2(t, _w=w, _ph=ph, _bad=bad_ph):\n            r = orig(t)\n            return r if _w in PRON_WORDS else (r.replace(_ph, _bad) if re.search(r\'(?<![A-Za-z])\' + re.escape(_w) + r\'(?![A-Za-z])\', t) else r)\n        PRON_WORDS[w] = ph; phonemes_of = fake2; ok0 = not ({line for _, line, bad in check(no) if bad} - base)\n        PRON_WORDS.pop(w); got = {line for _, line, bad in check(no) if bad}; phonemes_of = orig\n        res.append((f\'假改正 {w}（本篇改正在句子里都不起作用，造样本）\', ok0 and any(f\'] {w} \' in l_ for l_ in got - base)))\n'),
    ('读音核对.py', "    hk = next((k_ for k_ in HETCONF if k_.startswith(no + ' ')), None)", "    hk = next((k_ for k_ in HETCONF if k_.startswith(no + ' ') and het_key(k_.split(' ', 2)[2])), None)   # K102：只挑 HET 表里的词（别的词去掉记录不会报）"),
]
# 提交前钩子的改法（切换推送时由主会话批准后做，本程序不碰钩子文件，K16）：看门停用时只查快测印章（新管/印章.py），不再跑 会话开工 --提交前、规则执行核查
管道 = '''import json, os
def 看门停用():
    """新管开关：<工具>/管道.json 写 {"看门": "停用"} 时，8 套看门机制（证据、闲置、用上核查、门变异、放行口子、规则执行核查、演练、丝滑）不再当门"""
    try: return json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '管道.json'))).get('看门') == '停用'
    except Exception: return False
'''

def main():
    t = sys.argv[1]; bad = []
    open(f'{t}/管道.py', 'w').write(管道)
    for f, a, b in 补丁:
        p = f'{t}/{f}'; s = open(p).read()
        if b in s: continue
        if s.count(a) != 1: bad.append(f'{f}：锚出现 {s.count(a)} 次：{a[:50]}'); continue
        open(p, 'w').write(s.replace(a, b))
    if '--停用' in sys.argv or '--启用' in sys.argv:
        json.dump({'看门': '停用' if '--停用' in sys.argv else '启用'}, open(f'{t}/管道.json', 'w'), ensure_ascii=False)
    print('\n'.join(bad) or f'补丁 {len(补丁)} 处已打；开关 {t}/管道.json')
    sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
