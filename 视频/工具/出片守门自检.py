#!/usr/bin/env python3
"""出片守门自检（规则执行机器，CLAUDE.md 第16条）：出片程序 make_video.py 里每一道“停止”守门，都在真实脚本的副本上
故意改坏一处、只出声音，出片程序必须停下并报出对应的编号；原样的一份必须完整出完（不误拦）。
出片程序从工作目录 scripts/ 下所有脚本读设置（按句子原文对应），所以每一项都在并排的隔离工作区 ../守门自检/ 里跑：
模型、字体、缓存等一律链接回原工作目录，scripts/ 里只放这一份改坏的脚本，work_NN 也是隔离的，不碰正式篇目。
在视频工作目录下运行：python3 <工具目录>/出片守门自检.py
全部通过 → 把 make_video.py、render.py 和本程序的指纹写进 工具/出片守门自检通过.json（规则执行机器核对：出片程序一改，
指纹对不上，提交、推送一律停，直到重跑本自检通过）。"""
import re, os, sys, json, copy, subprocess, hashlib, shutil, time
T = os.path.dirname(os.path.abspath(__file__)); STAMP = f'{T}/出片守门自检通过.json'
指纹 = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def 改(d, path, val):
    x = d
    for k in path[:-1]: x = x.setdefault(k, {})
    x[path[-1]] = val(x.get(path[-1])) if callable(val) else val


CASES = [   # (编号, 篇, 改法说明, 改法, 环境变量, 停止信息里必须有的字)
    ('原样', '20', '不改（不得误拦）', lambda d: None, {}, None),
    ('T36放行', '20', '24 起两数字紧挨的年份范围短横 1963–64 不算破折号（51 S18）：完整出完', lambda d: (改(d, ['no'], '24'), [c_.__setitem__('zh', c_['zh'].replace('——', '，')) for s_ in d['sentences'] for c_ in s_['chunks']], d['sentences'][0]['chunks'][0].__setitem__('zh', d['sentences'][0]['chunks'][0]['zh'] + '1963–64')), {}, None),   # 20 篇自己 S14-2 中文有“——”（24 前不管），先换掉
    ('T36', '20', '24 起中文里出现破折号', lambda d: (改(d, ['no'], '24'), d['sentences'][0]['chunks'][0].__setitem__('zh', d['sentences'][0]['chunks'][0]['zh'] + '——')), {}, '（T36）'),
    ('A45', '20', '区间声音指纹对不上（读音/语速改过，旧区间没作废）', lambda d: 改(d, ['区间声音指纹'], {k: '000000000000' for k in d.get('非人声区间', {})}), {}, '（A45）'),
    ('A45放行', '20', '指纹对不上但带 OLD_IV_VOID=1（草稿声音.sh）：跳过旧区间、完整出完', lambda d: 改(d, ['区间声音指纹'], {k: '000000000000' for k in d.get('非人声区间', {})}), {'OLD_IV_VOID': '1'}, None),
    ('A45开关', '20', 'OLD_IV_VOID=1 却出正式视频（不是只出声音）', lambda d: None, {'OLD_IV_VOID': '1', 'AUDIO_ONLY': ''}, '（A45 开关）'),
    ('A30', '20', '停顿插入点写成第 99 个标点', lambda d: 改(d, ['停顿插入点', 'S1'], {'99': 1.0}), {}, '个标点超出'),
    ('音21', '20', '句子增益写 2 dB', lambda d: 改(d, ['句子增益dB'], {'S1': 2.0}), {}, '句子增益dB 只许'),
    ('G36', '20', '分段增益写 8 dB（超过 ±6）', lambda d: 改(d, ['分段增益dB'], {'S1': {'1': 8.0}}), {}, '分段增益dB 写法不对'),
    ('G57', '20', '合成标点把字母也改了', lambda d: 改(d, ['合成标点'], {'S1': [['the', 'teh']]}), {}, '合成标点只许把逗号换成分号'),
    ('G57不在句', '20', '合成标点写的词组不在这一句里（G79 门变异）', lambda d: 改(d, ['合成标点'], {'S1': [['zzq,', 'zzq;']]}), {}, '不在这一句里'),
    ('列举逗号', '20', '列举逗号写成第 99 个标点（G79 门变异）', lambda d: 改(d, ['列举逗号'], {'S1': [99]}), {}, '列举逗号写的位置超出'),
    ('增益加除阻', '20', 'S11 有停顿处除阻又写分段增益：K157 起照常出完（独立复核先乘增益再换供体）', lambda d: 改(d, ['分段增益dB'], {'S11': {'1': 1.0}}), {}, None),
    ('A3', '20', '环境变量换音色', lambda d: None, {'VOICE': 'voice_mf.npy'}, '（A3/A7）'),
    ('A7', '20', '环境变量换降噪', lambda d: None, {'AFFILE': 'AF.txt'}, '（A3/A7）'),
    ('A27', '02', '结尾句语速改回会丢 /z/ 的 0.80', lambda d: 改(d, ['结尾句', 'S16', '整句语速'], 0.80), {}, '（A27）'),
    ('A33', '10', '前段音调去掉“范围”', lambda d: 改(d, ['结尾句', 'S17', '前段音调'], lambda v: {k: x for k, x in (v or {'拉长': 1.0}).items() if k != '范围'}), {}, '前段音调没有写 范围'),
    ('A40', '20', 'S3 除阻加强增益写 7 dB（超过 6 dB）', lambda d: 改(d, ['除阻加强', 'S3', '1'], lambda v: [v[0], v[1], 7.0]), {}, '除阻加强的位置或增益不对'),
    ('A39', '20', 'S11 连读处补除阻挪进下一个词 0.3 秒', lambda d: 改(d, ['停顿处除阻', 'S11', '2'], lambda v: [v[0] + 0.3, v[1] + 0.3, v[2]]), {}, '连读处补除阻的位置不对'),
    ('A10', '20', 'S5 第1个标点的停顿删除区间写在句首（删到词的声音）', lambda d: 改(d, ['停顿删除区间', 'S5'], {'1': [0.10, 0.20]}), {}, '停顿删除区间不在该标点处'),
    ('A12', '04', '连读处 S7 的人工插入点挪进下一个词 0.35 秒（重放 01 The unskilled, the）', lambda d: 改(d, ['停顿插入点', 'S7', '1'], lambda v: v + 0.35), {}, 'A15'),
    ('A15', '04', 'S7 人工插入点挪进词里 0.35 秒', lambda d: 改(d, ['停顿插入点', 'S7', '1'], lambda v: v + 0.35), {}, 'A15'),
    ('A28', '04', 'S17 人工插入点挪进词里 0.35 秒', lambda d: 改(d, ['停顿插入点', 'S17', '1'], lambda v: v + 0.35), {}, 'A15'),
    ('A42', '19', 'S2 交界插入点写法错', lambda d: 改(d, ['停顿插入点', 'S2', '2'], lambda v: [v[0], '交界错']), {}, '（A42）'),
    ('A25', '07', '去掉 S16 放慢版在 /i/→/s/ 交界的人工插入点', lambda d: d['停顿插入点'].pop('S16'), {}, '（A25）'),
    ('A20非人声区间', '20', 'S5 非人声区间挪进词里（G79 门变异）', lambda d: 改(d, ['非人声区间', 'S5'], [[1.0, 1.2, '']]), {}, '非人声区间不对'),
    ('A21除阻位置', '20', 'S14 词尾除阻挪进词里（G79 门变异）', lambda d: 改(d, ['词尾除阻', 'S14', '1'], lambda v: [1.0, v[1]]), {}, '词尾除阻的位置不对'),
    ('A21除阻被删', '20', 'S14 停顿删除区间截在移植的除阻里面（G79 门变异）', lambda d: 改(d, ['停顿删除区间', 'S14'], lambda v: {'1': [d['词尾除阻']['S14']['1'][0], d['词尾除阻']['S14']['1'][0] + 0.005]}), {}, '移植的除阻伸进了下一个词前面'),
    ('L14开口', '20', '高亮开口门槛写成 -10（比最响处还响，找不到开口；G79 门变异）', lambda d: 改(d, ['高亮开口门槛'], -10), {}, '找不到开口'),
    # 11-07（56）：G51 改号缺调平缓存、G72 严格缓存文字改了 两条“门变异”自检砍掉：结果取决于本机配音缓存，56 机器上误报卡住出片（守则① ③）；G51/G72 本身由 缓存进仓库核对、配音缓存核对 的自检管
    ('A3音色文件', '20', 'voice_mb.npy 被改了一个字节（G79 门变异）', lambda d: None, {'STRICT_CACHE': '1'}, '音色文件 voice_mb.npy 被改过', {'voice_mb.npy': lambda s, o: open(o, 'wb').write(open(s, 'rb').read()[:-1] + b'\x01')}),
    ('A7降噪文件', '20', 'AF.txt 降噪改成 nf=-30（G79 门变异）', lambda d: None, {'STRICT_CACHE': '1'}, '降噪设置 AF.txt 被改过', {'AF.txt': lambda s, o: open(o, 'w').write(re.sub(r'afftdn=nf=-40', 'afftdn=nf=-30', open(s).read()))}),
    ('G72单线程标记', '20', '配音缓存的 .单线程 标记指纹全写错（G79 门变异）', lambda d: None, {'STRICT_CACHE': '1'}, '标记指纹不符', {'cache_tts': lambda s, o: (os.makedirs(o), [os.symlink(f'{s}/{x}', f'{o}/{x}') for x in os.listdir(s) if not x.endswith('.单线程')], [open(f'{o}/{x}.单线程', 'w').write('0' * 16) for x in os.listdir(s) if x.endswith('.pkl')])}),
    ('A32', '10', '结尾句接点挪出最后一个标点的停顿', lambda d: 改(d, ['结尾句', 'S17', '接点'], lambda v: [v[0] + 2400, v[1] + 2400]), {}, '结尾句的接点'),
]


def _换(obj, **kv):
    """临时改对象属性（模块全局、实例方法），返回还原函数"""
    old = {k: (k in vars(obj), getattr(obj, k, None)) for k in kv}
    for k, v in kv.items(): setattr(obj, k, v)
    def back():
        for k, (had, v) in old.items():
            if had: setattr(obj, k, v)
            else: delattr(obj, k)
    return back
def _在(fn, *backs):
    try: return fn()
    finally:
        for b in backs: b()
def _假注音(MV, m):   # 注音程序在句子里注出了没登记过的写法（只认 m 里的词，其余一律 qqq）
    return _换(MV.KT.tokenizer, phonemize=lambda t_, l_='en-us': m.get(t_, 'qqq'))
def _读音(MV, words, extra, ctx, text, m):
    return _在(lambda: MV.phonemes_of(text), _换(MV, PRON_WORDS=words, PRON_EXTRA=extra, PRON_CTX=ctx, PRON_FIX={}), _假注音(MV, m))
def _块序(MV):
    import difflib, types as ty
    full = MV.phonemes_of(MV._synth_punct(MV.spoken('hello world'))); n = len(MV.phonemes_of(MV.spoken('hello')).strip()) + 1
    class SM:
        def __init__(s, *a, **k): pass
        def get_matching_blocks(s): return [ty.SimpleNamespace(a=0, b=3, size=1), ty.SimpleNamespace(a=n, b=0, size=1)]
    return _在(lambda: MV.chunk_token_starts(['hello', 'world'], [ty.SimpleNamespace(phoneme=full)]), _换(difflib, SequenceMatcher=SM))
def _句(MV, no, i):
    d = json.load(open(f'scripts/{no}.json')); ch = d['sentences'][i]['chunks']
    return ' '.join(re.sub(r'\*\*', '', MV.R.strip_gloss(c['en'])).strip() for c in ch)
def _标点数(MV):   # 带时长模型少报一个标点（模型行为变了）：标点数和分段数对不上必须停
    s = next(x for x in (_句(MV, '20', i) for i in range(17)) if re.search(r'[,;:](?=\s)', x) and x not in MV.ENDING)
    f0 = MV.KT.create_timed
    def ct(*a, **k):
        r = f0(*a, **k); return (r[0], r[1], [x for x in r[2] if x.phoneme not in ',;:'])
    ps, p0, gs = [], 0, []
    for mm in re.finditer(r'[,;:](?=\s)', s): ps.append((p0, mm.end())); p0 = mm.end() + 1; gs.append(MV.P_COMMA)
    ps.append((p0, len(s)))
    return _在(lambda: MV.sentence_audio(s, ps, gs), _换(MV.KT, create_timed=ct))
def _擦音(MV):
    import numpy as np
    n = [0]
    def sib(*a): n[0] += 1; return [(0, 0, 1.0)] * (2 if n[0] == 1 else 3)
    return _在(lambda: MV._ending_sib_guard('a b.', {}, np.zeros(10), []), _换(MV, _sib_strength=sib), _换(MV.k, create=lambda *a, **k: (np.zeros(100, np.float32), 24000)),
             _换(MV.KT, create_timed=lambda *a, **k: (np.zeros(100, np.float32), None, [])))
def _供体(MV, **kv):
    MV._DON.clear(); return _在(lambda: MV._donor('t'), _换(MV, **kv), lambda: MV._DON.clear())
def _颜色(MV):   # 门被拆的话 build 会接着出：只出声音、出到临时目录（不出整篇画面、不乱写文件）
    import tempfile; d = tempfile.mkdtemp(prefix='直测G49_'); os.environ['AUDIO_ONLY'] = '1'
    try: return _在(lambda: MV.build('scripts/20.json', f'{d}/g49.mp4'), _换(MV.R, 同屏色差=lambda d_, c_: ['S1 两个重点词颜色太像']))
    finally: os.environ.pop('AUDIO_ONLY', None); shutil.rmtree(d, ignore_errors=True)
def _普通句(MV):   # 20 里一句有逗号、不是结尾句、没写人工插入点/删除区间/除阻的句子，及它的分段
    for i in range(17):
        s = _句(MV, '20', i)
        if re.search(r'[,;:](?=\s)', s) and s not in MV.ENDING and not any(s in X for X in (MV.INSERT_AT, MV.DEL_AT, MV.GRAFT, MV.PGRAFT, MV.NONVOICE, MV.BOOST)): break
    ps, p0, gs = [], 0, []
    for mm in re.finditer(r'[,;:](?=\s)', s): ps.append((p0, mm.end())); p0 = mm.end() + 1; gs.append(MV.P_COMMA)
    ps.append((p0, len(s))); return s, ps, gs
def _自动删(MV, **kv):
    s, ps, gs = _普通句(MV); return _在(lambda: MV.sentence_audio(s, ps, gs), _换(MV, **kv))
def _结尾(MV, no='10'):
    d = json.load(open(f'scripts/{no}.json')); s = _句(MV, no, len(d['sentences']) - 1); return s, MV.ENDING[s]
def _音调伸出(MV):
    s, e = _结尾(MV); e2 = json.loads(json.dumps(e)); e2['前段音调']['范围'] = [e2['前段音调']['范围'][0], 99.0]
    return MV._ending_raw(s, e2)
def _音调改响(MV):
    import numpy as np
    s, e = _结尾(MV); return _在(lambda: MV._ending_raw(s, e), _换(MV, _tone_shape=lambda rF, a_, b_, cfg: np.full(len(rF), 0.5, np.float32)))
def _接点挪(MV, 插入=False, no='10'):
    s, e = _结尾(MV, no); SR = MV.SR; gs = []; ps, p0 = [], 0
    for mm in re.finditer(r'[,;:](?=\s)', s): ps.append((p0, mm.end())); p0 = mm.end() + 1; gs.append(MV.P_COMMA)
    ps.append((p0, len(s)))
    class D(dict):
        def get(s_, k_, d_=None): v_ = dict.get(s_, k_, d_); return None if v_ is None else v_ + int(0.45 * SR)
    kv = {'_EJ': D(MV._EJ)}
    if 插入: kv.update(_停顿候选=lambda *a, **k: [], INSERT_AT={}, DEL_AT={})
    return _在(lambda: MV.sentence_audio(s, ps, gs), _换(MV, **kv))
def _画面L19(MV): return _画面运行(MV, [(MV.R, {'wide_notes': lambda *a, **k: ['假：说明比正文宽']})])
def _画面L20(MV):
    import 对正量 as DZ; return _画面运行(MV, [(DZ, {'gate': lambda *a, **k: ['假：S1 重点词中文偏了']})])
def _画面L3(MV): return _画面运行(MV, [(MV.R, {'orphan_lines': lambda *a, **k: [(1, '假')]})])
def _画面运行(MV, ps):
    import tempfile, title_anim as TA
    W = os.getcwd(); d = tempfile.mkdtemp(prefix='守门直测_', dir=os.path.dirname(W))
    for x in os.listdir(W):
        if x != 'scripts' and not x.startswith('work_') and not x.endswith(('.mp4', '.mp3', '.wav')): os.symlink(f'{W}/{x}', f'{d}/{x}')
    os.symlink(f'{W}/scripts', f'{d}/scripts')
    def 越过(*a, **k): raise RuntimeError('越过了画面守门')
    os.chdir(d)
    try: return _在(lambda: MV.build('scripts/25.json', f'{d}/x.mp4'), _换(TA, render_frames=越过), *[_换(o, **v) for o, v in ps])
    finally: os.chdir(W); shutil.rmtree(d, ignore_errors=True)
直测项 = [   # (编号, 改法说明, 改法(MV), 停止信息里必须有的字)
    ('A23改正连读', '读音改正（带连读错法）在句子里注出了没登记的写法，换不全', lambda MV: _读音(MV, {'zork': 'zˈuːk'}, {'zork': ['zˈʌk']}, {}, 'a zork', {'zork': 'zˈɑːk'}), '读音改正没有全部换到'),
    ('A23改正', '读音改正在句子里注出了没登记的写法，换不全', lambda MV: _读音(MV, {'zork': 'zˈuːk'}, {}, {}, 'a zork', {'zork': 'zˈɑːk'}), '读音改正没有全部换到'),
    ('A24语境个数', '按语境读音：词出现 2 次、语境只有 1 处', lambda MV: _读音(MV, {}, {}, {'zork it': {'词': 'zork', '读音': 'zˈuːk'}}, 'zork it and zork', {'zork': 'zˈɑːk'}), '按语境读音（A24）'),
    ('A24语境换到', '按语境读音：句子里注出的写法既不是错读也不是对读，换不到', lambda MV: _读音(MV, {}, {}, {'zork it': {'词': 'zork', '读音': 'zˈuːk'}}, 'zork it', {'zork': 'zˈɑːk'}), '按语境读音没有全部换到'),
    ('A20没声音', '一段全是静音', lambda MV: MV._edges(__import__('numpy').zeros(48000, 'float32')), '没有能听见的声音'),
    ('L14音素', '带时长模型的音素和朗读文字对不上', lambda MV: MV.chunk_token_starts(['hello'], [__import__('types').SimpleNamespace(phoneme='zzz')]), '带时长模型的音素与朗读文字对不上'),
    ('L14块序', '序列比对把第二块对到第一块前面', _块序, '不是递增的'),
    ('A21供体变了', '供体的合成和登记的指纹不同', lambda MV: _供体(MV, DONOR={**MV.DONOR, 't': (MV.DONOR['t'][0], '000000000000')}), '供体的合成变了'),
    ('A21供体除阻', '供体里量不出除阻', lambda MV: _供体(MV, _release=lambda *a, **k: None), '供体里找不到除阻'),
    ('A9标点数', '带时长模型少报一个标点', _标点数, '标点数对不上'),
    ('A27擦音个数', '结尾句和原速的擦音个数不同', _擦音, '擦音个数对不上'),
    ('A33音调伸出', '结尾句前段音调要改的范围伸到接点之后', _音调伸出, '伸到了接点之后'),
    ('A33音调接点', '前段音调改完接点那里有声音', _音调改响, '接点不在静音里了'),
    ('A10超出停顿', '自动删停顿：两头往里收算出的删除范围超出停顿', lambda MV: _自动删(MV, 余音删法=lambda s_: True, _余音两头=lambda e_, a_, b_, gap=2: (max(0, a_ - 80), b_ + 80)), '删除范围超出了停顿'),
    ('A10删到词', '自动删停顿：选中的“停顿”一直伸进后面的词里', lambda MV: _自动删(MV, _停顿候选=lambda e_, pe_, ns_, lo_, hi_, fl_: [(lo_, min(len(e_) - 1, ns_ + 400))]), '要删的部分里有词的声音'),
    ('A32接点删除', '20 结尾句接点挪到最后一个标点的停顿外（那里删了停顿）', lambda MV: _接点挪(MV, no='20'), '没有包住接点'),
    ('A32接点插入', '10 结尾句接点挪到词里（那里是连读插入）', lambda MV: _接点挪(MV, True), '结尾句的接点不在静音里（A32）'),
    ('L19说明行宽', '25 说明行比英文宽（宽度检查报出一处）', _画面L19, '说明行比上面的英文正文宽'),
    ('L20对正', '25 重点词中文没对正（对正量报出一处）', _画面L20, '重点词中文没对正'),
    ('L3孤词', '25 折行后末行只剩一个词（孤词检查报出一处）', _画面L3, '最后一行只剩一个词'),
    ('G49颜色', '同屏重点词色差检查报出太像', _颜色, '颜色太像'),
]


def main():
    if not os.path.exists('make_video.py') or not os.path.isdir('scripts'):
        sys.exit('【停止】请在视频工作目录（含 make_video.py、scripts/）下运行')
    for f in ('make_video.py', 'render.py'):
        if 指纹(f) != 指纹(f'{T}/{f}'): sys.exit(f'【停止】工作目录的 {f} 与仓库不一致，先拷过来再自检')
    import tempfile; pyc = tempfile.mkdtemp(prefix='守门自检pyc_'); sys.pycache_prefix = pyc; os.environ['PYTHONPYCACHEPREFIX'] = pyc   # K71：门变异并行 4 份私有工作目录链接同一个 __pycache__，同一秒写出、同样大小的两个变异体共用一份 .pyc，测的是别人的变异（v7 A23 两道“漏洞”）
    only = sys.argv[1:]; fails = []; t0 = time.time(); W = os.getcwd(); WS = os.path.abspath('../守门自检')
    shutil.rmtree(WS, ignore_errors=True); os.makedirs(f'{WS}/scripts')
    for x in os.listdir(W):
        if x == 'scripts' or x.startswith('work_') or x.endswith(('.mp4', '.mp3', '.wav', '.json')): continue
        os.symlink(f'{W}/{x}', f'{WS}/{x}')
    def 私tts(over):   # 改 ../tts 里的文件（音色、降噪、缓存标记）：另搭一个工作根，tts 逐项链接回去，只有被改的那几项是改过的副本（真 tts 不碰）
        R_ = f'{WS}_私'; shutil.rmtree(R_, ignore_errors=True); os.makedirs(f'{R_}/tts'); src = os.path.abspath(f'{W}/../tts')
        for x in os.listdir(src):
            if x in over: over[x](f'{src}/{x}', f'{R_}/tts/{x}')
            else: os.symlink(f'{src}/{x}', f'{R_}/tts/{x}')
        os.makedirs(f'{R_}/video')   # 真目录（链接成目录的话 ../tts 按真路径解析回真 tts）
        for x in os.listdir(WS): os.symlink(f'{WS}/{x}', f'{R_}/video/{x}')
        return f'{R_}/video'
    for case in CASES:
        rid, no, how, fn, env, want = case[:6]
        if only and rid not in only: continue
        d = copy.deepcopy(json.load(open(f'{W}/scripts/{no}.json')))
        try: fn(d)
        except Exception as e: fails.append(f'{rid} 自检样本找不到（{no} {how}）：{e}'); continue
        for p in os.listdir(f'{WS}/scripts'): os.remove(f'{WS}/scripts/{p}')
        json.dump(d, open(f'{WS}/scripts/{no}.json', 'w'), ensure_ascii=False)
        cwd_ = 私tts(dict(case[6])) if len(case) > 6 else WS
        r = subprocess.run(['python3', 'make_video.py', f'scripts/{no}.json', f'守门自检_{rid}.mp4'], capture_output=True, text=True, cwd=cwd_,
                           env={**os.environ, 'AUDIO_ONLY': '1', **env})
        o = r.stdout + r.stderr; stop = [l for l in o.splitlines() if '【停止】' in l]
        if want is None: ok = r.returncode == 0 and not stop
        else: ok = r.returncode != 0 and any(want in l for l in stop)
        print(f"{'✔' if ok else '✘'} {rid}：第{no}篇 {how} → " + (('完整出完' if r.returncode == 0 else '没出完：' + (stop or o.strip().splitlines()[-1:])[0][:120]) if want is None
              else (stop[0][:110] if stop else f'没停（退出码 {r.returncode}）')))
        if not ok: fails.append(f'没抓到：{rid}（{how}）' if want else f'误拦：{rid}')
        shutil.rmtree(f'{WS}_私', ignore_errors=True)
    shutil.rmtree(WS, ignore_errors=True)
    if not only or 'A24重音' in only:   # K145（39 S1 Y2K）：按语境读音只改重音（zˈɔːk → zˌɔːk）必须换到、不许停；旧程序同一处既算换了又算原本就对，停下
        sys.path.insert(0, W); import make_video as MV
        try: p_ = _读音(MV, {}, {}, {'zork it': {'词': 'zork', '读音': 'zˌɔːk'}}, 'zork it', {'zork it': 'zˈɔːk ɪt', 'zork': 'zˈɔːk'})
        except SystemExit as e: p_ = f'（停下）{e}'
        ok = p_.startswith('zˌɔːk') and 'zˈɔːk' not in p_
        print(f"{'✔' if ok else '✘'} A24重音：按语境读音只改重音 → {p_[:80]}")
        if not ok: fails.append('误拦：按语境读音只改重音（K145）')
    if not only or 'K155合成标点' in only:   # K155（45 S5 Johnny B. Goode）：合成标点许去掉人名首字母后的点；改字、去句末句号、加点、U.S. 的点、删逗号照停
        sys.path.insert(0, W); import make_video as MV
        cs_ = [('B. Goode', 'B Goode', True), ('Johnny B. Goode, and', 'Johnny B. Goode; and', True), ('birds, and', 'birds; and', True), ('the', 'teh', False), ('Goode.', 'Goode', False), ('B Goode', 'B. Goode', False), ('U.S. Army', 'U.S Army', False), ('Goode, and', 'Goode and', False), ("Kinderhook', after", "Kinderhook'. after", True), ('a, b', 'a. b. c', False), ('a b', 'a. b', False), ('a, cat', 'a. bat', False)]   # 51 S10：逗号↔句号原位互换放行；多加点、无标点处加点、改字照停
        bad_ = [f'{a}→{b}' for a, b, want in cs_ if MV._合成标点可收(a, b) != want]
        print(f"{'✔' if not bad_ else '✘'} K155合成标点：{len(cs_)} 个样本" + ('全对' if not bad_ else f'判错 {bad_}'))
        if bad_: fails.append(f'合成标点判错（K155）：{bad_}')
    if not only or 'K154擦音压低' in only:   # K154（44 S14 statistical 的 /s/ 发尖）：负增益只许罩住擦音（重心 ≥3 kHz、10–150 ms、-6～0 dB）；罩到元音、超过 -6 dB 都要停
        sys.path.insert(0, W); import make_video as MV, numpy as np_, scipy.signal as ss_
        SR_ = MV.SR; rg_ = np_.random.default_rng(11); tt_ = np_.arange(int(0.3 * SR_)) / SR_
        vow_ = (0.5 * np_.sin(2 * np_.pi * 180 * tt_) + 0.2 * np_.sin(2 * np_.pi * 540 * tt_)).astype(np_.float32)
        s_ = (ss_.sosfiltfilt(ss_.butter(6, 4000, 'highpass', fs=SR_, output='sos'), rg_.standard_normal(int(0.08 * SR_))) * 0.4).astype(np_.float32)
        w_ = np_.concatenate([vow_, s_, vow_]); a_, b_ = 0.3, 0.38; rm_ = lambda x: 20 * np_.log10(np_.sqrt(np_.mean(np_.asarray(x, np_.float64) ** 2)) + 1e-12)
        try: o_ = MV._boost(w_, {'1': [a_, b_, -3.0]}, '自检'); dd_ = rm_(o_[int(0.31 * SR_):int(0.37 * SR_)]) - rm_(w_[int(0.31 * SR_):int(0.37 * SR_)]); g1 = -3.3 < dd_ < -2.7
        except SystemExit as e: g1 = False; dd_ = str(e)[:60]
        def 停(items):
            try: MV._boost(w_, items, '自检'); return False
            except SystemExit as e: return 'K154' in str(e)
        b1 = 停({'1': [0.1, 0.2, -3.0]}); b2 = 停({'1': [a_, b_, -7.0]})
        # 51 S10 假擦音：≤60 ms、重心 ≥5 kHz、后面是静音的词尾段许压 -30 dB；不写“假擦音”或后面不是静音的照停
        f_ = (ss_.sosfiltfilt(ss_.butter(6, 6000, 'highpass', fs=SR_, output='sos'), rg_.standard_normal(int(0.05 * SR_))) * 0.4).astype(np_.float32)
        w2_ = np_.concatenate([vow_, f_, np_.zeros(int(0.03 * SR_), np_.float32), vow_])
        try: MV._boost(w2_, {'1': [0.3, 0.35, -30.0, '假擦音 自检']}, '自检'); g2 = True
        except SystemExit: g2 = False
        b3 = 停({'1': [0.3, 0.35, -30.0]}); w3_ = np_.concatenate([vow_, f_, vow_]); b4 = False
        try: MV._boost(w3_, {'1': [0.3, 0.35, -30.0, '假擦音']}, '自检')
        except SystemExit as e: b4 = 'K154' in str(e)
        ok = g1 and b1 and b2 and g2 and b3 and b4
        print(f"{'✔' if ok else '✘'} K154擦音压低：假擦音放行{'对' if g2 else '错'}、不写假擦音{'停' if b3 else '没停'}、后面不是静音{'停' if b4 else '没停'}；/s/ 压 3 dB → {dd_ if isinstance(dd_, str) else f'{dd_:+.2f} dB'}；罩到元音{'停' if b1 else '没停'}；-7 dB {'停' if b2 else '没停'}")
        if not ok: fails.append('没抓到或误拦：擦音压低（K154）')
    if not only or 'L14句首' in only:   # 51 S12：句首 非人声区间 盖住前 10 ms 起的比对窗口，_head_offset 要往后找有声音的窗口；对不上的照停
        sys.path.insert(0, W); import make_video as MV, numpy as np_
        r_ = np_.random.default_rng(1).standard_normal(MV.SR).astype(np_.float32) * 0.1; st_ = 1234; w_ = r_[st_:].copy(); w_[int(0.015 * MV.SR):int(0.055 * MV.SR)] = 0
        g_ = MV._head_offset(r_, w_) == st_
        try: MV._head_offset(r_, np_.random.default_rng(2).standard_normal(MV.SR).astype(np_.float32)); b_ = False
        except SystemExit: b_ = True
        print(f"{'✔' if g_ and b_ else '✘'} L14句首：句首静音后找得到裁剪位置{'对' if g_ else '错'}；对不上{'停' if b_ else '没停'}")
        if not (g_ and b_): fails.append('没抓到或误拦：句首裁剪位置（L14）')
    if not only or 'A21短供体' in only:   # 51 S10 Kinderhook：停顿处除阻第4项写“短供体”只留爆破送气（≤25 ms、1 kHz 以下占比 ≤-15 dB）；不写的照旧用整段供体
        sys.path.insert(0, W); import make_video as MV, numpy as np_
        d_ = MV._donor('k'); s_ = MV._short_donor(d_); X_ = np_.abs(np_.fft.rfft(s_)) ** 2; f_ = np_.fft.rfftfreq(len(s_), 1 / MV.SR)
        lo_ = 10 * np_.log10(X_[f_ < 1000].sum() / X_.sum()); w_ = np_.ones(MV.SR, np_.float32) * 0.1
        ok = len(s_) <= int(0.025 * MV.SR) and lo_ <= -15 and len(MV._pdonor(w_, 'k')) == len(d_) and len(MV._pdonor(w_, 'k', True)) == len(s_)
        print(f"{'✔' if ok else '✘'} A21短供体：{len(s_) / MV.SR * 1000:.0f} ms、1 kHz 以下 {lo_:.1f} dB；不写短供体的照旧整段")
        if not ok: fails.append('短供体不对（A21）')
    if not only or 'G43吸气' in only:   # 51 S10：非人声区间第4项写“吸气”、≥-30 dB 的每帧都是吸气频谱的许到 -24 dB；不写“吸气”、或那一下是元音照停
        sys.path.insert(0, W); import make_video as MV, numpy as np_, scipy.signal as ss_
        SR_ = MV.SR; t_ = np_.arange(int(0.3 * SR_)) / SR_; vw_ = (0.5 * np_.sin(2 * np_.pi * 180 * t_)).astype(np_.float32); z_ = np_.zeros(int(0.05 * SR_), np_.float32)
        rr_ = np_.sqrt(np_.mean(vw_[:int(0.005 * SR_)] ** 2)) * 1.0
        br_ = ss_.sosfiltfilt(ss_.butter(4, [2500, 4500], 'bandpass', fs=SR_, output='sos'), np_.random.default_rng(5).standard_normal(int(0.1 * SR_))); br_ = (br_ / np_.sqrt(np_.mean(br_ ** 2)) * rr_ * 10 ** (-26.5 / 20)).astype(np_.float32)
        tv_ = (np_.sin(2 * np_.pi * 180 * np_.arange(int(0.1 * SR_)) / SR_) * rr_ * 10 ** (-26.5 / 20) * np_.sqrt(2)).astype(np_.float32)
        def 停_(mid, lab):
            w_ = np_.concatenate([vw_, z_, mid, z_, vw_]); a_ = (len(vw_) + len(z_) // 2) / SR_; b_ = (len(vw_) + len(z_) + len(mid) + len(z_) // 2) / SR_
            try: MV._nonvoice(w_, [[a_, b_, '', lab] if lab else [a_, b_]], '自检'); return False
            except SystemExit: return True
        g_ = not 停_(br_, '吸气 自检'); b1_ = 停_(br_, None); b2_ = 停_(tv_, '吸气')
        print(f"{'✔' if g_ and b1_ and b2_ else '✘'} G43吸气：-26.5 dB 吸气写“吸气”放行{'对' if g_ else '错'}、不写{'停' if b1_ else '没停'}、元音写“吸气”{'停' if b2_ else '没停'}")
        if not (g_ and b1_ and b2_): fails.append('没抓到或误拦：非人声区间“吸气”（G43）')
    if not only or 'A23大小写' in only:   # K148（43 NeXT）：读音改正的词中间有大写（ZorK），普通小写 zork 不许被当成它去换（原来不分大小写，换不到就停）；大小写对得上的照换
        sys.path.insert(0, W); import make_video as MV
        try: p_ = _读音(MV, {'ZorK': 'zˈuːk'}, {}, {}, 'the zork day', {'the zork day': 'ðə zˈɔːk dˈeɪ', 'ZorK': 'zˈiː ˈoʊ'})
        except SystemExit as e: p_ = f'（停下）{e}'
        try: q_ = _读音(MV, {'ZorK': 'zˈuːk'}, {}, {}, 'a ZorK', {'a ZorK': 'ɐ zˈiː ˈoʊ', 'ZorK': 'zˈiː ˈoʊ'})
        except SystemExit as e: q_ = f'（停下）{e}'
        ok = 'zˈɔːk' in p_ and 'zˈuːk' in q_
        print(f"{'✔' if ok else '✘'} A23大小写：小写 zork 不动 → {p_[:30]}；ZorK 照换 → {q_[:30]}")
        if not ok: fails.append('误拦：读音改正把大小写不同的普通词当成专名（K148）')
    if not only or 'A24盖全局' in only:   # K147（19 S9 Dutch commerce）：词在读音改正表里（全局改成 zˈuːk），语境读音要能按原读法 zˈɑːk 换回来，不许停；别的句子仍按全局
        sys.path.insert(0, W); import make_video as MV
        try: p_ = _读音(MV, {'zork': 'zˈuːk'}, {}, {'zork it': {'词': 'zork', '读音': 'zˈɑːk'}}, 'zork it', {'zork it': 'zˈɑːk ɪt', 'zork': 'zˈɑːk'})
        except SystemExit as e: p_ = f'（停下）{e}'
        try: q_ = _读音(MV, {'zork': 'zˈuːk'}, {}, {'zork it': {'词': 'zork', '读音': 'zˈɑːk'}}, 'a zork', {'a zork': 'ɐ zˈɑːk', 'zork': 'zˈɑːk'})
        except SystemExit as e: q_ = f'（停下）{e}'
        ok = p_.startswith('zˈɑːk') and 'zˈuːk' in q_
        print(f"{'✔' if ok else '✘'} A24盖全局：语境读音盖过读音改正 → {p_[:40]}；别处照全局 → {q_[:40]}")
        if not ok: fails.append('误拦：语境读音盖不过读音改正（K147）')
    if not only or 'A36' in only:   # A36：复合词按它自己那一条读音改正换；所有格的 s 不被吞（注音函数直接测）
        sys.path.insert(0, W); import make_video as MV
        hb, bs = MV.PRON_WORDS.get('Haber-Bosch'), MV.PRON_WORDS.get('BASF')
        p1, p2 = MV.phonemes_of('the Haber-Bosch process'), MV.phonemes_of('BASF’s plant')
        g = MV.PRON_WORDS.pop('Haber-Bosch')
        try: p3 = MV.phonemes_of('the Haber-Bosch process')   # 拿掉复合词这一条：要么停（A23 守门：Haber 没换到），要么读音变了
        except SystemExit: p3 = '（停下）'
        MV.PRON_WORDS['Haber-Bosch'] = g
        ok = bool(hb and bs) and hb in p1 and hb not in p3 and any(bs + x in p2 for x in 'sz')
        print(f"{'✔' if ok else '✘'} A36：Haber-Bosch 按登记读音{'换到' if hb and hb in p1 else '没换到'}、拿掉改正后{'停下' if p3 == '（停下）' else ('变回' if hb and hb not in p3 else '没变')}；BASF’s 结尾 s {'保住' if bs and any(bs + x in p2 for x in 'sz') else '被吞'}")
        if not ok: fails.append('没抓到：复合词读音、所有格 s（A36）')
    直 = [x for x in 直测项 if not only or x[0] in only]
    if 直:   # 出片程序内部的守门（读音改正、按语境读音、供体、音素对齐、标点数、擦音个数、颜色……）：脚本造不出来，在进程里把内部状态改坏，守门必须停（G79 门变异）
        sys.path.insert(0, W); import make_video as MV
        os.environ['STRICT_CACHE'] = '1'   # 直测只用已有配音缓存，绝不现合成、不往仓库缓存里写
        try:
            for rid, how, fn, want in 直:
                try: fn(MV); got = '没停'
                except SystemExit as e: got = str(e)
                except Exception as e: got = f'出错 {e!r}'
                ok = want in got
                print(f"{'✔' if ok else '✘'} {rid}：{how} → {got[:110]}")
                if not ok: fails.append(f'没抓到：{rid}（{how}）')
        finally: os.environ.pop('STRICT_CACHE', None)
    if not fails and not only:
        json.dump({'make_video.py': 指纹(f'{T}/make_video.py'), 'render.py': 指纹(f'{T}/render.py'), '出片守门自检.py': 指纹(__file__),
                   '时间': time.strftime('%Y-%m-%dT%H:%M'), '项数': len(CASES)}, open(STAMP, 'w'), ensure_ascii=False, indent=1)
    print(f'出片守门自检：' + ('通过（每一道守门造的错都停下并报对编号，原样完整出完）' if not fails else '失灵！' + '；'.join(fails)) + f'（{time.time() - t0:.0f} 秒）')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
