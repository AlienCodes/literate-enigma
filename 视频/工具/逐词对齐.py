#!/usr/bin/env python3
"""逐词对齐（G47，T9 加强）：用户 2026-10-25 看 26 S14 “described something rolling downhill”：
“能能跟英文对齐的意思尽量对齐。就是说他有的这个哪怕没有标注的ok，就是能够跟上面的英文只要能对齐，尽量对齐，除非对齐不了……
描述某个东西滚下坡  就比如说某个东西就要跟这个something对齐。 rolling 就和滚对齐。 啊，尽量大家都要按照这个方式来对齐。”
门（26 起）：一个对齐组的英文里，除去重点词本身、专有名词（大写开头）、数字、虚词（冠词、介词、小品词、代词、助动词）后
还剩 2 个以上实词，就要拆开逐词对齐；对不了（习惯说法、语序整体换了、拆开中文不通顺，T7）写进 核对确认.合组：
{"S14 something rolling downhill": "对齐不了：<原因>"}（只认“对齐不了：”开头，登记 放行口子表）。没拆也没写就停。
01–25 不回头改：python3 逐词对齐.py --清单 把多实词组列进 制作记录/逐词对齐清单.md 交用户看。
用法：python3 逐词对齐.py --自检 | --清单"""
import json, re, os, sys, glob
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T)
起 = 26
虚 = set(("a an the of to in on at by for from with into onto upon as and or but nor so yet if than that which who whom whose what when where why how "
         "this these those it its they them their there here he him his she her we us our you your i me my "
         "himself herself itself themselves myself ourselves yourself is are was were be been being am has have had do does did "
         "will would shall should can could may might must not no up out off down over away back about around through "
         "more most very only just also even still such much many").split())   # 程度词不算实词
数 = set("one two three four five six seven eight nine ten eleven twelve twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion first second third half dozen".split())
def 实词(en):
    ws = re.findall(r"(?<![\w])[A-Za-z][A-Za-z'’-]*", re.sub(r'\*\*[^*]+\*\*', ' ', en))   # 1970s 的 s 不算词
    return [w for w in ws if w.lower() not in 虚 and w.lower() not in 数 and not w[0].isupper()]
def 键(si, en): return f'S{si} ' + re.sub(r'\s+', ' ', en.replace('**', '')).strip(' ,.;:')
def 多实词组(d):
    return [(si, en, zh, 实词(en)) for si, s in enumerate(d['sentences'], 1) for c in s['chunks'] for en, zh in c['align'] if len(实词(en)) >= 2]
def 查(d, no):
    if not str(no).isdigit() or int(no) < 起: return []
    ok = d.get('核对确认', {}).get('合组', {}); out = []
    for si, en, zh, ws in 多实词组(d):
        k = 键(si, en); v = ok.get(k, '')
        if not re.match(r'^对齐不了[：:].{4,}', v):
            out.append(f'[G47] {k}「{zh}」含 {len(ws)} 个实词（{"、".join(ws)}）没拆：能对齐的尽量逐词对齐（用户 2026-10-25：“rolling 就和滚对齐”）；'
                       f'对不了写 核对确认.合组 "{k}": "对齐不了：原因"')
    return out
def 清单():
    L = ['# 逐词对齐清单（程序生成：python3 视频/工具/逐词对齐.py --清单）', '',
         '用户 2026-10-25：“能跟英文对齐的意思尽量对齐……除非对齐不了”。26 起程序门要求多实词组拆开或写明对齐不了；01–25 不回头改，这里列出各篇里还剩 2 个以上实词的对齐组，交用户看。', '']
    tot = 0
    for p in sorted(glob.glob(f'{V}/脚本/[0-9][0-9].json')):
        n = os.path.basename(p)[:2]
        if int(n) >= 起: continue
        g = 多实词组(json.load(open(p)))
        if g: L += [f'## 第{n}篇（{len(g)} 组）', ''] + [f'- {键(si, en)}「{zh}」：{"、".join(ws)}' for si, en, zh, ws in g] + ['']; tot += len(g)
    open(f'{V}/制作记录/逐词对齐清单.md', 'w').write('\n'.join(L) + '\n'); return tot
def 自检():
    f = []
    d = {'sentences': [{'chunks': [{'align': [['described', '描述'], ['something rolling **downhill**', '某个东西滚**下坡**(downhill)']]}]}]}
    if not any('something rolling downhill' in x for x in 查(d, '26')): f.append('没抓到：26 S14 “something rolling downhill” 合在一组没拆（G47 重放）')
    if 查(d, '25'): f.append('误报：01–25 不回头查')
    d2 = json.loads(json.dumps(d)); d2['sentences'][0]['chunks'][0]['align'][1:] = [['something', '某个东西'], ['rolling', '滚'], ['**downhill**', '**下坡**(downhill)']]
    if 查(d2, '26'): f.append('误报：拆开逐词对齐的还报')
    d3 = json.loads(json.dumps(d)); d3['核对确认'] = {'合组': {'S1 something rolling downhill': '对齐不了：中文语序整体换了，拆开不通顺'}}
    if 查(d3, '26'): f.append('误报：写了“对齐不了：原因”还报')
    d4 = json.loads(json.dumps(d)); d4['核对确认'] = {'合组': {'S1 something rolling downhill': '先不拆，以后再说'}}
    if not 查(d4, '26'): f.append('没抓到：合组确认不是“对齐不了：”开头也放行')
    for en in ('came out', 'Apollo 13 crew', '**trade journal**', 'kept up', 'two days', 'Before the late 1970s', 'more often'):
        if len(实词(en)) >= 2: f.append(f'误报：{en} 不该算多实词（小品词、专名、数字、重点词本身不算）')
    return ['逐词对齐 自检：' + x for x in f]
if __name__ == '__main__':
    if '--自检' in sys.argv:
        e = 自检(); print('\n'.join(e) or '逐词对齐 自检通过（多实词合组没拆必停、拆开或写“对齐不了：原因”放行、01–25 不回头查）'); sys.exit(1 if e else 0)
    if '--清单' in sys.argv: print(f'逐词对齐清单：01–25 共 {清单()} 组，写进 制作记录/逐词对齐清单.md'); sys.exit(0)
    print(__doc__)
