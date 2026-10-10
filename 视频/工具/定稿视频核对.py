#!/usr/bin/env python3
"""定稿视频核对（G9 铁律）：存下来的视频必须是我们最后做好、通过全部核查的定稿，绝不能是旧版本。
用户 2026-10-10 原话：“我们一定一定一定要确定最终存的视频是我们最终做好的这些视频……千万不要弄那些老的视频……
这个作为我们一个非常非常重的铁律。”
在视频工作目录（含 make_video.py、render.py、title_anim.py、fonts/，上一级有 tts/）下运行：
  python3 <工具目录>/定稿视频核对.py            查 最终版4K视频/ 里的全部篇目
  python3 <工具目录>/定稿视频核对.py 08 07      只查这几篇（文件夹清点、自检照样全做）
  --不查镜像：归档定稿视频.py 归档完立刻调用时用（镜像仓库还没同步）；
  --只查清点和镜像：同步、推送镜像仓库之后用，几秒钟：清点 + 各处拷贝逐字节相同 + 4K（不重画画面、不重出声音）
逐篇查（任何一处不对都报出、返回 1：说明存的不是最终版，必须重新出片、过交付核查、重新归档）：
 ① 清点：《踩坑核查》G7（每篇一个文件、视频/视频/ 只有 NN.mp4、两处逐字节相同、旧草稿和试听视频已删）；
    最终版4K视频/ 的文件名与定稿脚本的标题一致；README 目录与文件一一对应；
 ② 4K：3840×2160；
 ③ 画面：从视频里解出每一个不同的画面（mpdecimate），与用现行定稿脚本（仓库 视频/脚本/NN.json）重新画的每一屏逐像素比对
    （缩到 1920×1080、去掉最下面的进度条，按 16×16 小块比）：脚本里的每一屏视频里都要有，视频里的每一个画面脚本里都要有；
    改过一个字、换过一处颜色、少了一屏或多了一屏都会报出；
 ④ 声音：用现行定稿脚本、现行读音改正，用出片程序只出声音（AUDIO_ONLY，与正式出片同一套程序），与视频里的声音逐样本比对，必须一致；
 ⑤ 镜像：literate-enigma 里的两处拷贝与这里逐字节相同。
自检（每次都跑）：故意改一个中文字的那一屏必须报出；声音调低 0.5 dB、换成别篇的声音必须报出；多放一个旧版本文件、文件名用旧标题必须报出。"""
import sys, os, re, json, glob, hashlib, subprocess, shutil, copy
os.environ['VIDEO_S'] = '2'                                    # 定稿 4K 的画法（render.py 在 import 时读）
import numpy as np, imageio_ffmpeg
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); ROOT = os.path.dirname(V)
WORK = os.getcwd(); sys.path.insert(0, WORK); sys.path.insert(1, T)
MIRROR = os.environ.get('MIRROR', '/home/user/literate-enigma')
FF = imageio_ffmpeg.get_ffmpeg_exe()
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
safe = lambda s: re.sub(r'[\\/:*?"<>|]', '', s).strip()        # 与 归档定稿视频.py 相同
W1, H1 = 1920, 1080; BAR = 12                                  # 比对用 1920×1080；进度条在最下面 8 像素，去掉 12 像素
THR = 8.0                                                      # 16×16 小块平均差的最大值超过它 = 不是同一个画面。标定（08）：同一屏 ≤ 3.0；
                                                               # 没高亮的暗字里逗号换顿号 22.8、换一个字 38 以上

if not all(os.path.exists(f'{WORK}/{x}') for x in ('make_video.py', 'render.py', 'title_anim.py', 'fonts')):
    sys.exit('【停止】请在视频工作目录（含 make_video.py、render.py、title_anim.py、fonts/）下运行')
import render as R, title_anim as TA
_src = open(f'{WORK}/make_video.py').read()
exec(_src[_src.index('T=dict(BG_TOP'):_src.index('P_CHUNK=')], {'R': R})   # 与出片同一套配色（make_video 在 import 时设给 render）


# ① 清点 ------------------------------------------------------------------------------------------------
def names_check(final_names, titles, readme_nos):
    """final_names：最终版4K视频/ 里的视频文件名；titles：{篇号: (英文标题, 中文标题)}（定稿脚本）；readme_nos：README 目录里的篇号"""
    bad = []; nos = []
    for b in final_names:
        m = re.match(r'(\d\d) - .+ - .+\.mp4$', b)
        if not m: continue                                     # 命名不对由 G7 报
        no = m.group(1); nos.append(no)
        if no not in titles: bad.append(f'[G9] 最终版4K视频/{b}：仓库里没有第{no}篇的定稿脚本'); continue
        want = f"{no} - {safe(titles[no][0])} - {safe(titles[no][1])}.mp4"
        if b != want: bad.append(f'[G9] 最终版4K视频/{b}：文件名与定稿脚本的标题不一致（旧标题的旧版本？），应为 {want}')
    if sorted(readme_nos) != sorted(nos): bad.append(f'[G9] 最终版4K视频/README.md 目录 {sorted(readme_nos)} 与文件 {sorted(nos)} 对不上')
    return bad


def inventory():
    K = __import__('踩坑核查')
    bad = list(K.video_folders(ROOT))
    final = sorted(os.path.basename(p) for p in glob.glob(f'{ROOT}/最终版4K视频/*.mp4'))
    titles = {os.path.basename(p)[:2]: (json.load(open(p))['title_en'], json.load(open(p))['title_zh'])
              for p in glob.glob(f'{V}/脚本/[0-9][0-9].json')}
    rd = f'{ROOT}/最终版4K视频/README.md'
    readme = re.findall(r'^\| (\d\d) \|', open(rd).read(), re.M) if os.path.exists(rd) else []
    return bad + names_check(final, titles, readme), final


# ③ 画面 ------------------------------------------------------------------------------------------------
def to_gray(png):
    from PIL import Image
    return np.asarray(Image.open(png).convert('L').resize((W1, H1), Image.BOX), dtype=np.uint8)


def render_screens(d, outdir, only=None):
    """用定稿脚本 d 画出视频里的每一屏（与 make_video.build 同一套画法；进度条画成 0，比对时去掉）。
    返回 [(名字, 灰度图)]：片头动画每一帧（'片头 k'，最后一帧是完整片头）+ 每句每块高亮（'S句-块'）。only=句号集合时只画这几句"""
    os.makedirs(outdir, exist_ok=True); no = d['no']
    colors = {}; i = 0                                         # 与 make_video.build 相同
    for s in d['sentences']:
        for c in s['chunks']:
            for w in re.findall(r'\*\*([^*]+)\*\*', c['en']):
                if w.lower() not in colors: colors[w.lower()] = R.PAL[i % len(R.PAL)]; i += 1
    R.unify_colors(colors, d['sentences'])
    header = f"{no} · {d['title_en']}　{d['title_zh']}"
    R.ES_FIXED = None
    sizes = [R.max_es([[tuple(p) for p in c['align']] for c in s['chunks']], colors, [c.get('note') for c in s['chunks']]) for s in d['sentences']]
    out = []
    if only is None:
        fx = d.get('title_fx', {})
        for k, (fn, _) in enumerate(TA.render_frames(d['title_en'], d['title_zh'], fx.get('hl', []), fx.get('ghost', []), outdir)):
            out.append((f'片头 {k}', to_gray(fn)))
    for si, s in enumerate(d['sentences']):
        if only is not None and si + 1 not in only: continue
        for ci in range(len(s['chunks'])):
            fn = f'{outdir}/S{si + 1:02d}_{ci + 1:02d}.png'
            R.ES_FIXED = min(sizes[si], 100 * R.S)
            R.frame_interlinear([[tuple(p) for p in c['align']] for c in s['chunks']], colors, header, 0, fn, active=ci,
                                notes=[c.get('note') for c in s['chunks']])
            out.append((f'S{si + 1}-{ci + 1}', to_gray(fn)))
    return out


def video_screens(mp4):
    """视频里每一个不同的画面（mpdecimate 去掉与上一帧相同的帧），缩到 1920×1080 灰度；返回 [(秒, 灰度图)]"""
    p = subprocess.run([FF, '-v', 'info', '-i', mp4, '-vf', f'mpdecimate,showinfo,scale={W1}:{H1}:flags=area,format=gray',
                        '-fps_mode', 'vfr', '-an', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True)
    n = len(p.stdout) // (W1 * H1); fr = np.frombuffer(p.stdout[:n * W1 * H1], np.uint8).reshape(n, H1, W1)
    ts = [float(x) for x in re.findall(r'pts_time:\s*([\d.]+)', p.stderr.decode('utf-8', 'replace'))]
    return list(zip(ts + [float('nan')] * (n - len(ts)), fr))


def _thumb(a): return a[:1060].reshape(53, 20, 96, 20).mean(axis=(1, 3))      # 缩略图（只用来挑候选）


def score(a, b):
    """两幅图的差别：去掉进度条后按 16×16 小块求平均绝对差，取最大的一块（改一个字、换一种颜色都会让某一块很大）"""
    dd = np.abs(a[:H1 - BAR].astype(np.int16) - b[:H1 - BAR].astype(np.int16)).astype(np.float32)
    h, w = dd.shape; h -= h % 16; w -= w % 16
    return float(dd[:h, :w].reshape(h // 16, 16, w // 16, 16).mean(axis=(1, 3)).max())


def best(img, pool, k=4):
    """img 在 pool 里最像的一幅：先用缩略图挑 k 个候选，再逐块比。返回 (差别, 下标)"""
    if not pool: return float('inf'), -1
    t = _thumb(img); ds = [float(np.abs(t - pt).mean()) for pt in pool['thumb']]
    cand = sorted(range(len(ds)), key=ds.__getitem__)[:k]
    return min((score(img, pool['img'][j]), j) for j in cand)


def mkpool(imgs): return {'img': imgs, 'thumb': [_thumb(x) for x in imgs]}


def screens_check(no, d, vids, outdir):
    """脚本→视频：每一屏（片头最后一帧 + 每句每块）视频里都要有；视频→脚本：视频里每一个画面都要是脚本画出来的某一屏（含片头动画帧）"""
    bad = []; rs = render_screens(d, outdir)
    vpool = mkpool([f for _, f in vids]); rpool = mkpool([g for _, g in rs])
    must = [x for x in rs if not x[0].startswith('片头')] + [[x for x in rs if x[0].startswith('片头')][-1]]
    worst = 0.0
    for name, g in must:
        s_, j = best(g, vpool); worst = max(worst, s_)
        if s_ > THR: bad.append(f'[G9] 第{no}篇 {name}：视频里找不到与现行定稿脚本一致的这一屏（最接近的画面差 {s_:.1f}，在 {vids[j][0]:.2f} 秒）')
    worst2 = 0.0
    for t, f in vids:
        s_, j = best(f, rpool); worst2 = max(worst2, s_)
        if s_ > THR: bad.append(f'[G9] 第{no}篇 视频 {t:.2f} 秒的画面：现行定稿脚本里没有这一屏（最接近 {rs[j][0]}，差 {s_:.1f}）')
    return bad, len(must), len(vids), worst, worst2, rs


# ④ 声音 ------------------------------------------------------------------------------------------------
def pcm(mp4):
    p = subprocess.run([FF, '-v', 'error', '-i', mp4, '-map', '0:a:0', '-f', 'f32le', '-ac', '1', '-ar', '48000', '-'], capture_output=True)
    return np.frombuffer(p.stdout, np.float32)


def audio_only(js, tag):
    """用出片程序只出声音（与正式出片同一套程序、同一套后期），在工作目录旁边的临时目录里做，不动 work_NN/ 里的东西"""
    tmp = os.path.join(os.path.dirname(WORK), f'定稿视频核对_{tag}')
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    os.symlink(f'{WORK}/fonts', f'{tmp}/fonts')
    os.symlink(f'{V}/脚本', f'{tmp}/scripts')   # 出片程序从当前目录的 scripts/*.json 读每句的人工设置（停顿插入点、非人声区间、词尾除阻、结尾句），
                                               # 没有它出的声音就不一样（2026-10-10 第一次试跑 01、02 误报差 2.8 dB 就是这个原因）；这里用仓库里的定稿脚本
    r = subprocess.run(['python3', f'{WORK}/make_video.py', js, 'a.mp4'], cwd=tmp, env=dict(os.environ, AUDIO_ONLY='1'), capture_output=True, text=True)
    if r.returncode or not os.path.exists(f'{tmp}/a.mp4'): sys.exit(f'【停止】只出声音失败：{js}\n{r.stdout[-800:]}{r.stderr[-800:]}')
    a = pcm(f'{tmp}/a.mp4'); shutil.rmtree(tmp, ignore_errors=True); return a


def audio_diff(a, b):
    """两段声音的差别（dB，相对 a 的响度）；长度差（秒）。完全相同时为 -inf"""
    n = min(len(a), len(b)); e = float(np.sqrt(np.mean((a[:n] - b[:n]) ** 2))); r = float(np.sqrt(np.mean(a[:n] ** 2))) + 1e-12
    return (20 * np.log10(e / r) if e > 0 else -np.inf), abs(len(a) - len(b)) / 48000


def audio_check(no, va, ref):
    db, dl = audio_diff(va, ref)
    bad = []
    if db > -60: bad.append(f'[G9] 第{no}篇 视频里的声音与现行定稿脚本出的声音不一致（差 {db:.1f} dB）：视频是旧配音或没按现行脚本出片')
    if dl > 0.1: bad.append(f'[G9] 第{no}篇 视频声音长度与现行定稿脚本出的声音差 {dl:.2f} 秒')
    return bad, db, dl


# ⑤ 镜像 ------------------------------------------------------------------------------------------------
def mirror_check(no, name, h):
    if not os.path.isdir(MIRROR): return []
    bad = []
    for p in (f'{MIRROR}/视频/视频/{no}.mp4', f'{MIRROR}/最终版4K视频/{name}'):
        if not os.path.exists(p): bad.append(f'[G9] 镜像仓库里没有 {os.path.relpath(p, MIRROR)}')
        elif sha(p) != h: bad.append(f'[G9] 镜像仓库里的 {os.path.relpath(p, MIRROR)} 与定稿不是同一个版本')
    return bad


def size_of(p):
    r = subprocess.run([FF, '-i', p], capture_output=True, text=True).stderr
    m = re.search(r'Video: .*?, (\d+)x(\d+)', r); return m.groups() if m else ('?', '?')


# 自检 --------------------------------------------------------------------------------------------------
def selftest(no, d, vids, va, ref, outdir):
    fails = []
    # 画面：第1句中文里第一个汉字换成“囗”、第一个中文逗号换成顿号（暗字里最细微的改动），这一句的每一屏都必须找不到
    vpool = mkpool([f for _, f in vids])
    for label, pat, new in (('改一个字', r'[一-鿿]', '囗'), ('逗号换顿号', '，', '、')):
        d2 = copy.deepcopy(d); hit = None
        for c in d2['sentences'][0]['chunks']:
            m = re.search(pat, c['zh'])
            if not m: continue
            ch = m.group(0); k_ = next((i for i, (_, z) in enumerate(c['align']) if ch in z), None)
            if k_ is None: continue
            c['zh'] = c['zh'].replace(ch, new, 1); c['align'][k_] = [c['align'][k_][0], c['align'][k_][1].replace(ch, new, 1)]; hit = ch; break
        if hit is None: fails.append(f'自检样本找不到：第{no}篇 S1 {label}'); continue
        for name, g in render_screens(d2, outdir + '_自检', only={1}):
            s_, _ = best(g, vpool)
            if s_ <= THR: fails.append(f'没抓到：第{no}篇 {name} {label}（{hit}→{new}）仍判为同一屏（差 {s_:.1f}）')
        shutil.rmtree(outdir + '_自检', ignore_errors=True)
    # 声音：调低 0.5 dB、错开 5 毫秒都必须报出
    if not audio_check(no, va * 10 ** (-0.5 / 20), ref)[0]: fails.append('没抓到：声音调低 0.5 dB')
    if not audio_check(no, np.concatenate([np.zeros(240, np.float32), va]), ref)[0]: fails.append('没抓到：声音错开 5 毫秒')
    # 清点：多一个旧版本、旧标题的文件名都必须报出；原样不报
    titles = {no: (d['title_en'], d['title_zh'])}; good = f"{no} - {safe(d['title_en'])} - {safe(d['title_zh'])}.mp4"
    if names_check([good], titles, [no]): fails.append('清点误报：原样文件名被报出')
    if not names_check([good, f'{no} - Old Title - 旧标题.mp4'], titles, [no]): fails.append('没抓到：最终版4K视频/ 里多一个旧标题的旧版本')
    if not names_check([good], titles, []): fails.append('没抓到：README 目录少了一篇')
    return fails


def main():
    flags = {a for a in sys.argv[1:] if a.startswith('--')}; want = [a.zfill(2) for a in sys.argv[1:] if not a.startswith('--')]
    quick = '--只查清点和镜像' in flags; no_mirror = '--不查镜像' in flags
    bad, final = inventory()
    print('① 清点（G7 + 文件名与定稿标题一致 + README 目录）：' + ('通过' if not bad else '✘'))
    for x in bad: print('   ✘', x)
    nos = [b[:2] for b in final]
    for no in want:
        if no not in nos: bad.append(f'[G9] 第{no}篇不在 最终版4K视频/ 里'); print('   ✘', bad[-1])
    todo = [b for b in final if not want or b[:2] in want]
    st_done = False
    for b in todo:
        no = b[:2]; fp = f'{ROOT}/最终版4K视频/{b}'; js = f'{V}/脚本/{no}.json'
        if not os.path.exists(js): continue
        d = json.load(open(js)); h = sha(fp); B = []
        sz = size_of(fp)
        if sz != ('3840', '2160'): B.append(f'[G9] 第{no}篇不是 4K（{sz[0]}×{sz[1]}）')
        if quick:
            vb = f'{V}/视频/{no}.mp4'
            if not os.path.exists(vb) or sha(vb) != h: B.append(f'[G9] 第{no}篇 视频/视频/{no}.mp4 与 最终版4K视频/ 里的不是同一个版本')
            B += mirror_check(no, b, h)
            print(f'第{no}篇 {b}  sha256 {h[:16]}  {sz[0]}×{sz[1]}  各处拷贝 → ' + ('✔ 一致' if not B else '✘'))
            for x in B: print('   ✘', x)
            bad += B; continue
        vids = video_screens(fp); outdir = os.path.join(os.path.dirname(WORK), f'定稿视频核对_画面_{no}')
        sb, n1, n2, w1, w2, rs = screens_check(no, d, vids, outdir); B += sb
        va = pcm(fp); ref = audio_only(js, no); ab, db, dl = audio_check(no, va, ref); B += ab
        if not no_mirror: B += mirror_check(no, b, h)
        print(f'第{no}篇 {b}\n   sha256 {h[:16]}  {sz[0]}×{sz[1]}  画面：脚本 {n1} 屏全在视频里（最大差 {w1:.1f}），视频 {n2} 个画面全是脚本里的（最大差 {w2:.1f}）'
              f'  声音：与现行脚本出的声音差 {db:.1f} dB、长度差 {dl:.3f} 秒  → ' + ('✔ 是最终版' if not B else '✘'))
        for x in B: print('   ✘', x)
        bad += B
        if not st_done:
            f_ = selftest(no, d, vids, va, ref, outdir); st_done = True
            print(f'自检（第{no}篇）：改一个字、逗号换顿号的那几屏，声音调低 0.5 dB、声音错开 5 毫秒、多一个旧版本、README 少一篇：' + ('全部报出' if not f_ else '✘ ' + '；'.join(f_)))
            if f_: bad += ['【核查程序失灵】' + x for x in f_]
        shutil.rmtree(outdir, ignore_errors=True)
    if quick: print('（只查了清点和各处拷贝；画面、声音没有重新比对）')
    print('定稿视频核对（G9）：' + ('全部通过——存的都是最终版' if not bad else f'✘ {len(bad)} 处不对，存的不是最终版，不得交付'))
    sys.exit(1 if bad else 0)


if __name__ == '__main__': main()
