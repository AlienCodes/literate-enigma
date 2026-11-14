#!/usr/bin/env python3
"""逐词对齐（G47，T9 加强）：用户 2026-10-25 看 26 S14 “described something rolling downhill”：
“能能跟英文对齐的意思尽量对齐。就是说他有的这个哪怕没有标注的ok，就是能够跟上面的英文只要能对齐，尽量对齐，除非对齐不了……
描述某个东西滚下坡  就比如说某个东西就要跟这个something对齐。 rolling 就和滚对齐。 啊，尽量大家都要按照这个方式来对齐。”
门（26 起）：一个对齐组的英文里，除去重点词本身、专有名词（大写开头）、数字、虚词（冠词、介词、小品词、代词、助动词）后
还剩 2 个以上实词，就要拆开逐词对齐；对不了（习惯说法、语序整体换了、拆开中文不通顺，T7）写进 核对确认.合组：
{"S14 something rolling downhill": "对齐不了：<原因>"}（只认“对齐不了：”开头）。没拆也没写就停。
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
def 键(si, en): return f'S{si} ' + re.sub(r'\s+', ' ', re.sub(r'\{\{.*?\}\}', '', en).replace('**', '')).strip(' ,.;:')   # K143（40 S14 {{=}}and dispensed）：键去掉 {{=}} {{换行}} 标记
def 旧键(si, en): return f'S{si} ' + re.sub(r'\s+', ' ', en.replace('**', '')).strip(' ,.;:')
def 多实词组(d):
    return [(si, en, zh, 实词(en)) for si, s in enumerate(d['sentences'], 1) for c in s['chunks'] for en, zh in c['align'] if len(实词(en)) >= 2]
def 查(d, no):
    if not str(no).isdigit() or int(no) < 起: return []
    ok = d.get('核对确认', {}).get('合组', {}); out = []
    for si, en, zh, ws in 多实词组(d):
        k = 键(si, en); v = ok.get(k, '') or ok.get(旧键(si, en), '')
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
    d5 = {'sentences': [{'chunks': [{'align': [['{{=}}and dispensed **remedies** to villagers', '给村民发**药**(remedies)']]}]}]}   # K143 好/坏样本（40 S14）
    if not any('S1 and dispensed remedies to villagers' in x for x in 查(d5, '26')): f.append('没抓到：{{=}} 开头的多实词组没拆也没写（K143）')
    d5['核对确认'] = {'合组': {'S1 and dispensed remedies to villagers': '对齐不了：中文语序整体换了，拆开不通顺'}}
    if 查(d5, '26'): f.append('误报：{{=}} 组按去掉标记的键写了“对齐不了”还报（K143，40 S14）')
    d5['核对确认'] = {'合组': {'S1 {{=}}and dispensed remedies to villagers': '对齐不了：中文语序整体换了，拆开不通顺'}}
    if 查(d5, '26'): f.append('误报：带标记的旧键不认了（K143）')
    for en in ('came out', 'Apollo 13 crew', '**trade journal**', 'kept up', 'two days', 'Before the late 1970s', 'more often'):
        if len(实词(en)) >= 2: f.append(f'误报：{en} 不该算多实词（小品词、专名、数字、重点词本身不算）')
    return ['逐词对齐 自检：' + x for x in f] + 同序自检()

# K128（用户 2026-11-07 看 55 S6：“尽可能的就是上面的英文和如果说ok的话能那就跟下面的这个中文对应好，对吧？尽可能的不论是哪个单词”）：
# G47 只管“除重点词外还剩 2 个以上实词”的组；重点词（或术语）+ 别的实词挤一组、而中文语序和英文一样的（55 S5 As the steel rusts／随着钢筋生锈），
# 也能拆、也要拆。只提醒（疑点），不卡流程；对不了照样写 核对确认.合组 "对齐不了：原因"。55 起查。
同序起 = 55
def _锚(en, zh, 术语):
    """英文里的锚（重点词加粗段、术语）按出现顺序：[(起, 止, 标签)]；中文里对应的锚：[(起, 止, 标签)]"""
    ea = [(m.start(), m.end(), m.group(1).lower()) for m in re.finditer(r'\*\*([^*]+)\*\*', en)]
    za = [(m.start(), m.end(), m.group(2).lower()) for m in re.finditer(r'\*\*([^*]+)\*\*\(([^)]+)\)', zh)]
    for e_, z_ in (术语 or {}).items():
        m = re.search(r'(?<![A-Za-z])' + re.escape(e_) + r'(?![A-Za-z])', re.sub(r'\*\*', '', en))
        if m and '**' not in en and z_ in zh: ea.append((m.start(), m.end(), e_.lower())); i = zh.index(z_); za.append((i, i + len(z_), e_.lower()))
    去 = lambda L: sorted(x for x in L if not any(y != x and y[0] <= x[0] and x[1] <= y[1] for y in L))
    return 去(ea), 去(za)
def _词(t): return [w for w in re.findall(r"[A-Za-z][A-Za-z'’-]*|\d+", re.sub(r"['’]s\b", '', t)) if w.lower() not in 虚 and len(w) > 1 or w.isdigit()]   # 专名、数字也算（所有格 's 不算）
def _中实(t): return re.sub(r'（[^）]*）|\([^)]*\)|[\s，。；：、！？“”"‘’,.;:!?]', '', t)
def _对(e_, z_): return e_ == z_ or e_ in z_.split() or e_ in z_
def 同序组(d):
    out = []
    for si, s in enumerate(d['sentences'], 1):
        for c in s['chunks']:
            for en, zh in c['align']:
                ea, za = _锚(en, zh, d.get('术语', {}))
                if not ea or not za: continue
                if len(ea) >= 2:   # 几个重点词挤一组、中文先后和英文一样（55 S9 ascribed these lumps to）；被隔开的同一个短语（left her out）不算
                    if '**' in en and len(ea) == len(za) and len(set(x[2] for x in za)) >= 2 and all(_对(a[2], b[2]) for a, b in zip(ea, za)):
                        out.append((si, en, zh, '几个重点词中文先后和英文一样'))
                    continue
                if len(za) != 1: continue
                src = en if '**' in en else re.sub(r'\*\*', '', en)   # 术语锚的位置按去掉加粗的英文算
                be, af = _词(src[:ea[0][0]]), _词(src[ea[0][1]:])
                bz, az = _中实(zh[:za[0][0]]), _中实(zh[za[0][1]:])
                if (be and not af and bz and not az) or (af and not be and az and not bz):
                    out.append((si, en, zh, f'重点词前后的“{"、".join(be or af)}”和中文语序一样'))
    return out
def 同序(d, no):
    if not str(no).isdigit() or int(no) < 同序起: return []
    ok = d.get('核对确认', {}).get('合组', {}); out = []
    for si, en, zh, why in 同序组(d):
        k = 键(si, en); v = ok.get(k, '') or ok.get(旧键(si, en), '')
        if not re.match(r'^对齐不了[：:].{4,}', v):
            out.append(f'[K128] {k}「{zh}」{why}，能逐词拆开（用户 2026-11-07：“尽可能的不论是哪个单词”都对应好）；对不了写 核对确认.合组 "{k}": "对齐不了：原因"')
    return out
def 同序自检():
    f = []; 术 = {'Chatham House': '查塔姆研究所'}
    坏 = [['As the steel **rusts**,', '随着钢筋**生锈**(rusts)，'], ['**ascribed** these **lumps** **to**', '**把**(ascribed to)这些**块状物**(lumps)**归因于**(ascribed to)'],
          ['**seeps into** a crack,', '**渗入**(seeps into)裂缝时，'], ['the think-tank Chatham House', '智库查塔姆研究所（Chatham House）'], ['a **rethink** of construction.', '**重新思考**(rethink)建造之道。']]
    好 = [['As', '随着'], ['the steel', '钢筋'], ['**rusts**,', '**生锈**(rusts)，'], ['**ascribed**', '**把**(ascribed to)'], ['these **lumps**', '这些**块状物**(lumps)'], ['**to**', '**归因于**(ascribed to)'],
          ['**seeps into**', '**渗入**(seeps into)'], ['a crack,', '裂缝时，'], ['the think-tank', '智库'], ['Chatham House', '查塔姆研究所（Chatham House）'], ['a **rethink**', '**重新思考**(rethink)'], ['of construction.', '建造之道。'],
          ['a **lifespan** of around 50 years.', '约50年的**使用寿命**(lifespan)。'], ['**sloppy** mixing', '搅拌**马虎**(sloppy)'], ['About 43 metres **in diameter**,', '穹顶**直径**(in diameter)约43米，'],
          ['or **inferior** raw **ingredients**,', '或原料**成分**(ingredients)**低劣**(inferior)。'], ['an **astonishing** **feat** of **architecture**,', '**建筑**(architecture)史上**令人惊叹的**(astonishing)**壮举**(feat)，'],
          ['signs of **clumsy** workmanship', '手艺**拙劣的**(clumsy)痕迹，'], ['the **vast**', '下方**宏大的**(vast)'], ['and many **structures**', '而且许多**建筑**(structures)'], ['**reinforced with**', '**靠**(reinforced with)']]
    术2 = {'Galloping Gertie': '奔腾的格蒂', 'Gertie': '格蒂', 'Ministry of Health': '卫生部', 'Sierra Leone': '塞拉利昂', 'Yuan': '袁隆平'}
    for en, zh in [['Galloping Gertie.', '“奔腾的格蒂”。'], ['a 1954 Ministry of Health report', '卫生部1954年的一份报告'], ["Yuan's", '袁隆平迈出了'],
                   ['**left** her **out**;', '**把**(left out)她**排除在外了**(left out)；'], ["who shared the 2004 **World Food Prize** with Sierra Leone's Monty Jones,", '曾与塞拉利昂的蒙蒂·琼斯共获2004年**世界粮食奖**(World Food Prize)，']]:
        if 同序({'sentences': [{'chunks': [{'align': [[en, zh]]}]}], '术语': 术2}, '55'): f.append(f'误报：「{en}」（专名套专名、所有格、被隔开的同一短语、数字和专名在另一边，不该报，K128）')
    for en, zh in 坏:
        if not 同序({'sentences': [{'chunks': [{'align': [[en, zh]]}]}], '术语': 术}, '55'): f.append(f'没抓到：55 拆开前的「{en}」（K128）')
    for en, zh in 好:
        if 同序({'sentences': [{'chunks': [{'align': [[en, zh]]}]}], '术语': 术}, '55'): f.append(f'误报：「{en}」已拆开或中文语序倒过来，不该报（K128）')
    d = {'sentences': [{'chunks': [{'align': [坏[0]]}]}], '核对确认': {'合组': {'S1 As the steel rusts': '对齐不了：测试用原因写够长'}}}
    if 同序(d, '55'): f.append('误报：写了“对齐不了：原因”还报（K128）')
    if 同序({'sentences': [{'chunks': [{'align': [坏[0]]}]}]}, '54'): f.append('误报：55 以前不回头查（K128）')
    return ['逐词对齐 同序自检：' + x for x in f]
if __name__ == '__main__':
    if '--自检' in sys.argv:
        e = 自检(); print('\n'.join(e) or '逐词对齐 自检通过（多实词合组没拆必停、拆开或写“对齐不了：原因”放行、01–25 不回头查）'); sys.exit(1 if e else 0)
    if '--清单' in sys.argv: print(f'逐词对齐清单：01–25 共 {清单()} 组，写进 制作记录/逐词对齐清单.md'); sys.exit(0)
    print(__doc__)
