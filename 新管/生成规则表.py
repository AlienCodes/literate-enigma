#!/usr/bin/env python3
"""从现有 规则执行表.json + CLAUDE.md + 《制作硬性标准与踩坑总结》机器生成 新管/规则表.json。
不手抄：每条规矩的门、自检照旧表解析（规则执行核查.解析），按门所在程序归到阶段。
用法：python3 新管/生成规则表.py [--写入]   不带 --写入只打印统计和“没搬”清单。"""
import sys, os, re, json, hashlib
H = os.path.dirname(os.path.abspath(__file__))
_内 = os.path.exists(f'{os.path.dirname(H)}/交付核查.py')   # 切换后在 视频/工具/新管/ 里
R = os.path.dirname(os.path.dirname(os.path.dirname(H))) if _内 else os.path.dirname(H)   # 仓库根（有 CLAUDE.md）
T = os.environ.get('XG_TOOLS') or (os.path.dirname(H) if _内 else f'{R}/视频/工具'); sys.path.insert(0, T)
import 规则执行核查 as RZ

# 门所在程序 → 阶段。看门类由 指纹/快测 替代（原因写在 替代原因）
阶段表 = {
    '文本': ['踩坑核查.py', '译文核查.py', 'check_all.py', '说明分行.py', '意思个数.py', '初稿生成/核对.py', '拆分组.py',
             '生成文本.py', 'sync_article.py', '颜色核对.py', '工作稿核对.py', '补对照记录.py', '破折号.py', '重点词被去掉.py', '对正量.py'],
    '声音': ['读音核对.py', '停顿位置精确核对.py', '结尾句接点.py', '区间作废.py', '疑点清单.py', '确认按位置迁移.py', '草稿声音.sh',
             '逐词对齐.py', '标点停顿核对.py', '句首句尾与停顿位置核对.py', '词尾辅音核对.py', '无标点停顿核对.py', '音频体检.py',
             '自动切点.py', '句内响度.py', '快速重建核查.sh', '配音缓存核对.py'],
    '出片内': ['make_video.py', 'render.py', 'title2.py', 'title_anim.py', '出片守门自检.py', '排版自检.py'],
    '出片后': ['机器复听.py', '纯人声核对.py', '响度一致性核对.py', '高亮同步核对.py', '独立复核/synth.py', '独立复核/labels.py',
               '出片指纹.py', '抽屏.py', 'audio_qc.py', '句间停顿核对.py', '高亮对齐.py'],
    '定稿': ['定稿流水线.sh', '归档定稿视频.py', '定稿视频核对.py', '推送两仓库.sh', '全篇核查.py', '缓存进仓库核对.py', '重查记录.py',
             '镜像同步.py', '开工记录.py', '推送自检.py', '流程自检.py', '环境/准备机器.sh'],
    '看门': ['规则执行核查.py', '用上核查.py', '门变异.py', '证据.py', '丝滑.py', '执行效应演练.py', '执行效应声音演练.py', '演练镜像.py',
             '彩排.sh', '放行口子核查.py', '会话开工.py', '开工必读.py', '开工提醒.sh', '方法进化表.py', '推请求.py', 
             '主会话核对.sh', '音频首要法则.py', '收工记录.py', 'githooks/pre-commit'],
    '行为闸门': ['钩子/闸门.py', '报坑.py', '钩子/钩子自检.py'],   # 拦我自己动作的钩子（不许 --no-verify、发文件一次一个、不派子代理）、原子取号：保留，轻
}
程序阶段 = {p: s for s, ps in 阶段表.items() for p in ps}
替代原因 = {
    '规则执行核查.py': '规矩↔门的对账改由规则表本身承担：每条一行，快测逐条跑坏样本',
    '用上核查.py': '只剩一根管子，程序是否用上由 做.sh/定稿.sh 的调用链决定；成片指纹含程序哈希',
    '门变异.py': '改为每周后台体检，不拦人（快测的坏样本已证明门在）',
    '证据.py': '成片指纹（数据+规则表版本+程序哈希）替代证据链；只有走管子才出得了带指纹的片',
    '丝滑.py': '不丝滑由 做.sh 的一页报告直接看出（停在哪一步、为什么）',
    '执行效应演练.py': '快测：每条规则的坏样本必抓、好样本必放 + 27 回归',
    '执行效应声音演练.py': '快测：声音检查程序各自的 --自检（造坏声音必须抓到）+ 27 回归逐字节',
    '演练镜像.py': '同执行效应演练，由快测替代', '彩排.sh': '快测本地 ≤5 分钟替代 GitHub 全新容器彩排；全量体检每周后台',
    '放行口子核查.py': '例外只认 用户同意记录 原话：定稿.sh 疑点清零时直接查，不另设口子表',
    '会话开工.py': '开工只读 写稿须知.md（从规则表生成）', '开工必读.py': '由 写稿须知.md 替代（从规则表生成）',
    '开工提醒.sh': '由 写稿须知.md 和 做.sh 报告替代', '方法进化表.py': 'token 记录保留为 做.sh 报告的一行，不拦人',
    '推请求.py': 'GitHub 全量链降为每周体检', '流程自检.py': '管子只有两条命令，快测直接跑它们的门',
    '推送自检.py': '推送仍由 推送两仓库.sh 做，其自检并入快测', '主会话核对.sh': '主会话看 做.sh 报告',
    '音频首要法则.py': '音频规则全部在规则表里（阶段 声音/出片后），写稿须知 只列 AI 要判的', '收工记录.py': '并入 做.sh 报告',
    '钩子/钩子自检.py': '钩子只剩行为闸门，自检并入快测', 'githooks/pre-commit': '提交前只跑快测（规则表完整 + 坏样本）',
}

def 分交付核查(锚):
    """交付核查.py 的门按锚在 出片前 / 出片后 哪一段"""
    s = open(f'{T}/交付核查.py').read(); i = s.find(锚[:24]); j = s.find("elif stage == '出片后'")
    return '声音' if 0 <= i < j else '出片后' if i >= 0 else '出片后'

看门词 = ('证据', '_ZJ', '用上核查', '_YS', '规则执行核查', '门变异', '丝滑', '放行口子', '演练', '彩排', '会话开工', '开工必读', '方法进化', '推请求', '收工记录', '闲置', '镜像回收')
def 词原因(锚):
    for w, f in (('证据', '证据.py'), ('_ZJ', '证据.py'), ('用上核查', '用上核查.py'), ('_YS', '用上核查.py'), ('闲置', '用上核查.py'), ('规则执行核查', '规则执行核查.py'),
                 ('门变异', '门变异.py'), ('丝滑', '丝滑.py'), ('放行口子', '放行口子核查.py'), ('演练', '执行效应演练.py'), ('彩排', '彩排.sh'),
                 ('会话开工', '会话开工.py'), ('开工必读', '开工必读.py'), ('方法进化', '方法进化表.py'), ('推请求', '推请求.py'), ('收工记录', '收工记录.py'), ('流程自检', '流程自检.py')):
        if w in 锚: return 替代原因[f]
    return '?'
def 阶段(prog, 锚):
    if any(w in 锚 for w in 看门词) and prog not in ('出片指纹.py',): return '看门'
    if prog == '交付核查.py': return 分交付核查(锚)
    return 程序阶段.get(prog)

def 级别(rid, 摘):
    return '疑' if re.search(r'待用户判|需试听|人看|只有人能判|人工', 摘) else '错'

修法 = {   # 现有的 --写入（机械修法）
    'T36': '破折号.py 换逗号/冒号（中文按意思），英文同步文章', '守则18': '同 T36', 'T18': '三项并列 and/or 前补逗号，align 同步', 'T35': '同 T18',
    'L19': '说明分行.py NN --写入', '守则14': '同 L19', 'G57': 'G57 合成标点（出片程序已有）', 'A21': '词尾辅音核对.py NN --写入',
    'A10': '词尾辅音核对.py NN --写入', 'A19': '自动切点.py NN --写入', 'A9': '自动切点.py NN --写入', 'G36': '句内响度.py NN --写入',
    'A27': '结尾句接点.py NN --写入', 'A45': '区间作废.py NN（改读音/语速后旧区间作废，重找）', 'L16': '说明分行.py NN --写入',
}

特别 = {   # 门在看门程序里、但管的是真东西的：搬进快测，或写清由谁保证
    'A26': ('搬：快测', '快测跑 规则执行核查.挂钩检查（出片程序改了，核查程序挂钩还在）+ 成片指纹含程序哈希，程序一改旧片作废'),
    'A42': ('搬：快测', '同 A26：快测跑 挂钩检查'),
    '画17': ('替代', '出片顺序由 做.sh 固定写死（文本→合成→声音→出片→出片后），不再靠人拼步骤'),
    'A46': ('替代', '声音演练由快测替代：交付核查 出片后 各声音核查 --自检 + 27 回归逐字节'),
    'G61': ('替代', '证据链由成片指纹替代；出片只有 做.sh/定稿.sh 一条路'),
    'G65': ('替代', 'token/不丝滑/机制漏洞 进 做.sh 一页报告，不拦人'),
    'G74': ('替代', 'GitHub 全量链降为每周体检'),
    'G91': ('替代', '不丝滑由 做.sh 报告直接看出（停在哪一步、为什么）'),
    'G87': ('替代', '云端请求目录只给 GitHub 全量链用，全量链降为每周体检'),
}
def main():
    reg = json.load(open(f'{T}/规则执行表.json'))
    rules = RZ.规矩(open(RZ.STD).read(), open(f'{R}/CLAUDE.md').read()); rules.pop('__重复__', None)
    表, 没搬 = [], []
    for rid in sorted(set(rules) | set(reg), key=lambda k: (re.sub(r'\d.*', '', k), int(re.search(r'\d+', k).group()) if re.search(r'\d+', k) else 0, k)):
        gates, tests = RZ.解析(reg, rid)
        st = sorted({阶段(p, a) or '?' for p, a in gates})
        留 = [s for s in st if s not in ('看门', '?')]
        e = {'编号': rid, '摘要': rules.get(rid, '')[:80], '门': [list(g) for g in gates], '自检': [list(t) for t in tests],
             '演练': reg.get(rid, {}).get('演练', []), '阶段': 留 or st, '级别': 级别(rid, rules.get(rid, '') + json.dumps(reg.get(rid, {}), ensure_ascii=False)),
             '修法': 修法.get(rid, '')}
        if not gates:
            e['状态'] = '无门（' + ('只靠人判，写进写稿须知' if reg.get(rid, {}).get('部分靠人') or reg.get(rid, {}).get('为什么程序判不了') else '规则执行表没登记门') + '）'
            if '规则执行表没登记门' in e['状态']: 没搬.append(rid)
        elif 留: e['状态'] = '搬：' + '、'.join(留)
        elif '?' in st:
            e['状态'] = '没搬'; 没搬.append(rid); e['未知程序'] = sorted({p for p, a in gates if not 阶段(p, a)})
        else:
            e['状态'] = '替代'; e['替代原因'] = '；'.join(sorted({替代原因.get(p) or 词原因(a) for p, a in gates if 阶段(p, a) == '看门'}))
        if rid in 特别: e['状态'], e['说明'] = 特别[rid]
        if not tests and e['状态'].startswith('搬'): e['缺坏样本'] = True
        表.append(e)
    from collections import Counter
    c = Counter(e['状态'].split('：')[0].split('（')[0] for e in 表)
    print('规则', len(表), dict(c), '缺坏样本', sum(1 for e in 表 if e.get('缺坏样本')))
    for e in 表:
        if e['状态'] == '没搬' or e['状态'].startswith('无门（规则'): print('  没搬', e['编号'], e.get('未知程序', ''), e['摘要'][:40])
    if '--写入' in sys.argv:
        ver = hashlib.sha256(json.dumps(表, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
        json.dump({'版本': ver, '来源': '生成规则表.py 从 规则执行表.json、CLAUDE.md、制作硬性标准与踩坑总结.md 生成', '规则': 表},
                  open(sys.argv[sys.argv.index('--到') + 1] if '--到' in sys.argv else f'{H}/规则表.json', 'w'), ensure_ascii=False, indent=0)
        print('写入 规则表.json 版本', ver)

if __name__ == '__main__': main()
