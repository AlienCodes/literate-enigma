"""片头动画（小样）：在 title2.py 静态片头的基础上，把画面拆成图层，按时间依次出现。
- 英文标题逐行淡入并轻微上移；
- 中文标题黄色色块轻弹出现；
- 「朋克英语」四张纸片按 朋→克→英→语 依次"啪"地贴上（放大落下、轻微回弹、旋转归位）；
- 纸胶带落下，最后 PUNK ENGLISH 标签条从左滑入。
动画结束后的画面与 title2.frame_title2 的静态片头一致（只差合成取整误差）。
"""
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import render as R
import title2 as T

S = T.S; W, H = T.W, T.H; U = T.U
FPS = 30


def _rgba(color, alpha):
    lay = Image.new('RGBA', (W, H), color + (0,)); lay.putalpha(alpha); return lay


def _title_layers(en, zh, hl, ghost, variant=1):
    """返回 背景、每行英文图层、中文色块图层、标志各部件图层（均为整幅 RGBA）。坐标算法与 title2.frame_title2 相同。"""
    bg = T.base(variant).convert('RGBA')
    words = [(w, ('h' if w.strip(',.') in hl else 'g' if w.strip(',.') in ghost else 'n')) for w in en.split()]
    for es in range(168 * S, 60, -4):
        ef = R.EN(es, 900)
        lines = T.wrap(words, ef, 1680 * S)
        if len(lines) <= 3:
            break
    zf = R.ZH(int(es * 0.57), 900)
    logo_canvas, parts, bb = _logo_parts()
    logo_h = bb[3] - bb[1]; logo_w = bb[2] - bb[0]
    lhE = int(es * 1.08); ph = int(es * 0.57 * 1.55)
    GAP_BADGE, GAP_LOGO = 48 * S, 46 * S
    total = len(lines) * lhE + GAP_BADGE + ph + GAP_LOGO + logo_h
    top_ink = ef.getbbox(lines[0][0][0])[1]
    y = (H - (total - top_ink)) / 2 - top_ink
    line_layers = []
    for ln in lines:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        lw = ef.getlength(' '.join(w for w, _ in ln)); x = (W - lw) / 2
        for w, k in ln:
            ww = ef.getlength(w)
            m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text((x, y), w, font=ef, fill=255)
            if k == 'h':
                gl = m.filter(ImageFilter.GaussianBlur(18 * S)).point(lambda v: int(v * 0.7))
                lay = Image.alpha_composite(lay, _rgba(T.AC2, gl))
                g = Image.new('RGB', (W, H)); g.paste(T.grad(int(ww) + 2, int(es * 1.3), T.AC1, T.AC2), (int(x), int(y)))
                gg = g.convert('RGBA'); gg.putalpha(m); lay = Image.alpha_composite(lay, gg)
            elif k == 'g':
                gm = Image.new('L', (int(ww) + 2, int(es * 1.3))); gd = ImageDraw.Draw(gm)
                for i in range(gm.width):
                    gd.line([(i, 0), (i, gm.height)], fill=int(255 - 230 * (i / gm.width) ** 1.3))
                fm = Image.new('L', (W, H), 0); fm.paste(gm, (int(x), int(y)))
                lay = Image.alpha_composite(lay, _rgba((248, 250, 246), ImageChops.multiply(m, fm)))
                dots = Image.new('L', (W, H), 0); dd = ImageDraw.Draw(dots); rnd = random.Random(3)
                for _ in range(260 * S):
                    px = x + ww * 0.45 + rnd.random() * ww * 0.75; py = y + es * 0.15 + rnd.random() * es * 0.95
                    rr = (rnd.random() * 4 + 1) * S
                    dd.ellipse([px - rr, py - rr, px + rr, py + rr], fill=int(60 + 120 * rnd.random()))
                lay = Image.alpha_composite(lay, _rgba((200, 255, 230), ImageChops.multiply(dots, m.filter(ImageFilter.MaxFilter(15 * S + (S + 1) % 2)))))
            else:
                lay = Image.alpha_composite(lay, _rgba((248, 250, 246), m))
            x += ww + ef.getlength(' ')
        line_layers.append(lay); y += lhE
    y += GAP_BADGE
    badge = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(badge)
    zw = zf.getlength(zh); pad = 48 * S
    d.rounded_rectangle([(W - zw) / 2 - pad, y, (W + zw) / 2 + pad, y + ph], radius=18 * S, fill=T.AC1)
    tb = d.textbbox((0, 0), zh, font=zf)
    d.text(((W - (tb[2] - tb[0])) / 2 - tb[0], y + (ph - (tb[3] - tb[1])) / 2 - tb[1]), zh, font=zf, fill=(20, 40, 32))
    badge_c = (W / 2, y + ph / 2)
    y += ph + GAP_LOGO
    ox, oy = int((W - logo_w) / 2) - bb[0], int(y) - bb[1]
    logo_parts = [dict(p, x=p['x'] + ox, y=p['y'] + oy, cx=p['cx'] + ox, cy=p['cy'] + oy) for p in parts]
    return bg, line_layers, (badge, badge_c), logo_parts


def _logo_parts():
    """与 title2.ransom_logo 相同的部件与位置，但把每个部件（纸片+阴影、胶带、标签条）单独返回。"""
    CW, CH = int(560 * U), int(260 * U)
    P = T.PIECES; total = sum(p['w'] for p in P) - sum(p.get('ov', T.OVERLAP) for p in P[:-1])
    x = CW / 2 - total * U / 2; centers = []
    for sp in P:
        centers.append((x + sp['w'] * U / 2, CH / 2 + sp['dy'] * U)); x += (sp['w'] - sp.get('ov', T.OVERLAP)) * U
    pieces = {i: T.paper_piece(P[i], random.Random(100 + i), 500 + i * 7) for i in range(len(P))}
    parts = []; canvas = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))

    def add(kind, idx, img, px, py, sh=None):
        nonlocal canvas
        lay = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
        if sh:
            shi, (sx, sy), bl = sh
            sl = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); sl.paste(shi, (px + sx, py + sy)); lay = sl.filter(ImageFilter.GaussianBlur(bl))
        il = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); il.paste(img, (px, py)); lay = Image.alpha_composite(lay, il)
        canvas = Image.alpha_composite(canvas, lay)
        parts.append(dict(kind=kind, idx=idx, layer=lay, x=0, y=0, cx=px + img.width / 2, cy=py + img.height / 2))

    for i in [2, 0, 3, 1]:   # 与静态片头相同的叠放顺序
        pc = pieces[i]; cx, cy = centers[i]
        add('piece', i, pc, int(cx - pc.width / 2), int(cy - pc.height / 2), T._shadow(pc))
    for j, (ci, dx, dy, rot) in enumerate([(0, -30, -34, 38), (3, 30, 34, 32)]):
        tp = T.tape_piece(random.Random(300 + j), 900 + j, rot=rot); cx, cy = centers[ci]
        add('tape', j, tp, int(cx + dx * U - tp.width / 2), int(cy + dy * U - tp.height / 2))
    if T.DYMO:
        lb = T.dymo_label(T.DYMO)
        lx = int(CW / 2 + T.DYMO_DX * U - lb.width / 2); ly = int(max(c[1] for c in centers) + T.DYMO_DY * U)
        add('dymo', 0, lb, lx, ly, T._shadow(lb, off=(2, 3), blur=2.0, op=0.6))
    bb = canvas.getchannel('A').point(lambda v: 255 if v > 6 else 0).getbbox()
    # 部件图层放到整幅画面坐标：先裁到部件自身范围，记录左上角
    for p in parts:
        b = p['layer'].getbbox(); p['img'] = p['layer'].crop(b); p['x'], p['y'] = b[0], b[1]
        p['cx'] -= 0; p['cy'] -= 0
        del p['layer']
    return canvas, parts, bb


def _ease_out(p): return 1 - (1 - p) ** 3
def _ease_back(p, k=1.6): p -= 1; return 1 + (k + 1) * p ** 3 + k * p ** 2
def _clamp(v): return max(0.0, min(1.0, v))


def _fade(img, a):
    if a >= 1: return img
    out = img.copy(); out.putalpha(img.getchannel('A').point(lambda v: int(v * a))); return out


def _put(frame, img, x, y, a=1.0, scale=1.0, rot=0.0, cx=None, cy=None):
    if a <= 0: return
    if scale != 1.0 or rot:
        w0, h0 = img.size
        im2 = img.resize((max(1, int(w0 * scale)), max(1, int(h0 * scale))), Image.BICUBIC) if scale != 1.0 else img
        if rot: im2 = im2.rotate(rot, resample=Image.BICUBIC, expand=True)
        cx = x + w0 / 2 if cx is None else cx; cy = y + h0 / 2 if cy is None else cy
        x, y = int(round(cx - im2.width / 2)), int(round(cy - im2.height / 2)); img = im2
    frame.alpha_composite(_fade(img, a), (int(x), int(y))) if 0 <= x and 0 <= y and x + img.width <= W and y + img.height <= H else _safe(frame, _fade(img, a), int(x), int(y))


def _safe(frame, img, x, y):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); lay.paste(img, (x, y), img); frame.alpha_composite(lay)


def timeline(n_lines):
    t = {}; s = 0.08
    for i in range(n_lines): t[('line', i)] = (s + 0.11 * i, 0.42)
    b0 = s + 0.11 * n_lines + 0.02; t['badge'] = (b0, 0.32)
    p0 = b0 + 0.26
    for k, idx in enumerate([0, 1, 2, 3]): t[('piece', idx)] = (p0 + 0.11 * k, 0.17)   # 朋→克→英→语
    e = p0 + 0.11 * 3 + 0.17
    t[('tape', 0)] = (e - 0.02, 0.16); t[('tape', 1)] = (e + 0.04, 0.16)
    t[('dymo', 0)] = (e + 0.08, 0.2)
    return t, e + 0.28


def render_frames(en, zh, hl, ghost, outdir, variant=1):
    """输出动画帧 outdir/a0000.png…，返回 [(文件, 时长)]；最后一帧为完整静态片头。"""
    bg, lines, (badge, bc), parts = _title_layers(en, zh, hl, ghost, variant)
    tl, end = timeline(len(lines)); n = int(math.ceil(end * FPS)); files = []
    bbox_badge = badge.getbbox(); bimg = badge.crop(bbox_badge)
    for f in range(n + 1):
        t = f / FPS; fr = bg.copy()
        for i, lay in enumerate(lines):
            t0, dur = tl[('line', i)]; p = _clamp((t - t0) / dur)
            if p > 0: _put(fr, lay, 0, int(round((1 - _ease_out(p)) * 26 * S)), a=_ease_out(p))
        t0, dur = tl['badge']; p = _clamp((t - t0) / dur)
        if p > 0:
            sc = 0.86 + 0.14 * _ease_back(p) if p < 1 else 1.0
            _put(fr, bimg, bbox_badge[0], bbox_badge[1], a=_clamp(p * 2.5), scale=sc)
        for pt in parts:
            t0, dur = tl[(pt['kind'], pt['idx'])]; p = _clamp((t - t0) / dur)
            if p <= 0: continue
            img = pt['img']
            if p >= 1: _put(fr, img, pt['x'], pt['y']); continue
            if pt['kind'] == 'piece':
                sc = 1 + 0.55 * (1 - _ease_back(p, 2.2)); rot = (1 - _ease_out(p)) * (9 if pt['idx'] % 2 else -9)
                _put(fr, img, pt['x'], pt['y'], a=_clamp(p * 4), scale=sc, rot=rot)
            elif pt['kind'] == 'tape':
                _put(fr, img, pt['x'], pt['y'], a=_ease_out(p), scale=1 + 0.25 * (1 - _ease_out(p)))
            else:
                _put(fr, img, pt['x'] - int((1 - _ease_out(p)) * 70 * U), pt['y'], a=_ease_out(p))
        fn = f'{outdir}/a{f:04d}.png'; fr.convert('RGB').save(fn); files.append((fn, 1 / FPS))
    return files
