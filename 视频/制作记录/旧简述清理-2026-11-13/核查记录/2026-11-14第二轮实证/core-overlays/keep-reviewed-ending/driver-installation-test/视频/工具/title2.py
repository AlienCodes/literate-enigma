# 片头标题页（2026-10-05 用户选定 E 拼字版）：不写篇号；「朋克英语」勒索信拼贴标志只出现在这一页。
# 来源：片头设计/E_ransom/title_logo.py；字体改为从 fonts/ 读取。frame_title2 签名不变，no 参数不显示。
# Run with cwd = scratchpad/video and that dir on sys.path (fonts/ is relative).
import os, sys, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont
import numpy as np
import render as R

HERE = os.path.dirname(os.path.abspath(__file__))
S = R.S
W, H = 1920 * S, 1080 * S
F_QK = R.F + 'ZCOOLQingKeHuangYou-Regular.ttf'   # OFL, blocky display
F_MS = R.F + 'MaShanZheng-Regular.ttf'           # OFL, brush script
AC1, AC2 = (255, 214, 64), (255, 120, 80)


# ---------------------------------------------------------------- background (unchanged)
def grad(w, h, c1, c2):
    g = Image.new('RGB', (w, h))
    for x in range(w):
        t = x / max(1, w - 1)
        ImageDraw.Draw(g).line([(x, 0), (x, h)], fill=tuple(int(a + (b - a) * t) for a, b in zip(c1, c2)))
    return g


def base(variant):
    im = Image.new('RGB', (W, H))
    top, bot = (10, 30, 24), (16, 44, 36)
    d = ImageDraw.Draw(im)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * y / H) for a, b in zip(top, bot)))
    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).ellipse([W / 2 - 700 * S, H / 2 - 380 * S, W / 2 + 700 * S, H / 2 + 380 * S], fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(160 * S))
    col = (40, 120, 90) if variant != 2 else (120, 90, 20)
    return Image.composite(Image.new('RGB', (W, H), col), im, glow)


def wrap(words, font, maxw):
    lines = [[]]
    for w in words:
        t = ' '.join(x for x, _ in lines[-1] + [w])
        if lines[-1] and font.getlength(t) > maxw:
            lines.append([w])
        else:
            lines[-1].append(w)
    return lines


# ---------------------------------------------------------------- ransom-note logo
SS = 4  # supersampling for the paper cut-outs
LOGO_SCALE = 1.2
U = S * LOGO_SCALE  # px per logo design unit


def _font(kind, px):
    if kind == 'qk':
        return ImageFont.truetype(F_QK, px)
    if kind == 'ms':
        return ImageFont.truetype(F_MS, px)
    return R.ZH(px, 900)


# one entry per character (design units = px at 1080p)
PIECES = [
    # w,h = paper size; rot = paper tilt; grot = extra tilt of the glyph on its paper; dy = vertical jitter;
    # fs = glyph size; torn = (top,right,bottom,left) torn instead of scissor-cut; mw = magazine margin (l,t,r,b)
    dict(ch='朋', font='noto', paper=(22, 22, 22), ink=(250, 247, 238), w=82, h=88, rot=-8, grot=0, dy=5,
         fs=54, torn=(0, 0, 0, 0), margin=(242, 238, 226), mw=(5, 4, 7, 9), gx=-2, gy=-3, ov=7),
    dict(ch='克', font='qk', paper=(255, 51, 143), ink=(18, 18, 18), w=66, h=96, rot=6, grot=-3, dy=-10,
         fs=84, torn=(1, 0, 0, 0), halftone=True, ov=12),
    dict(ch='英', font='ms', paper=(246, 242, 230), ink=(18, 18, 18), w=90, h=78, rot=-4, grot=4, dy=10,
         fs=76, torn=(0, 1, 0, 1), gy=-4, ov=12),
    dict(ch='语', font='noto', paper=AC1, ink=(18, 18, 18), w=76, h=80, rot=9, grot=-4, dy=-5,
         fs=58, torn=(0, 0, 1, 0)),
]
OVERLAP = 11


def _poly(rng, k, x0, y0, w, h, torn, cj=2.4):
    """Return (outer, inner) polygons in SS pixels. Torn edges get a paper-fibre band."""
    c = [(x0 + rng.uniform(-cj, cj) * k, y0 + rng.uniform(-cj, cj) * k),
         (x0 + w + rng.uniform(-cj, cj) * k, y0 + rng.uniform(-cj, cj) * k),
         (x0 + w + rng.uniform(-cj, cj) * k, y0 + h + rng.uniform(-cj, cj) * k),
         (x0 + rng.uniform(-cj, cj) * k, y0 + h + rng.uniform(-cj, cj) * k)]
    outer, inner = [], []
    for e in range(4):
        p0, p1 = c[e], c[(e + 1) % 4]
        if torn[e]:
            L = math.dist(p0, p1)
            dx, dy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
            nx, ny = dy, -dx  # outward normal (clockwise polygon, y down)
            n = max(8, int(L / (1.7 * k)))
            off = 0.0
            for i in range(n):
                t = i / n
                bx, by = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
                off = off * 0.5 + rng.uniform(-1.5, 1.5)
                fib = 0.8 + rng.random() * 2.0
                outer.append((bx + nx * off * k, by + ny * off * k))
                inner.append((bx + nx * (off - fib) * k, by + ny * (off - fib) * k))
        else:
            outer.append(p0)
            inner.append(p0)
    return outer, inner


def _to_final(img):
    """SS RGBA -> final-resolution RGBA (premultiplied resize, no dark fringes)."""
    pm = img.convert('RGBa')
    pm = pm.resize((max(1, pm.width // SS), max(1, pm.height // SS)), Image.LANCZOS)
    return pm.convert('RGBA')


def _grain(img, seed, amt=5):
    a = np.asarray(img).astype(np.int16)
    rs = np.random.RandomState(seed)
    n = rs.normal(0, amt, a.shape[:2])[..., None]
    a[..., :3] = np.clip(a[..., :3] + n, 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def paper_piece(sp, rng, seed):
    k = U * SS
    pad = 16 * k
    w, h = sp['w'] * k, sp['h'] * k
    cw, chh = int(w + 2 * pad), int(h + 2 * pad)
    outer, inner = _poly(rng, k, pad, pad, w, h, sp['torn'])
    rgb = Image.new('RGB', (cw, chh), sp.get('margin', sp['paper']))
    alpha = Image.new('L', (cw, chh), 0)
    ImageDraw.Draw(alpha).polygon(outer, fill=255)
    d = ImageDraw.Draw(rgb)
    fibre = tuple(min(255, int(v * 0.35 + 236 * 0.65)) for v in sp['paper'])
    d.polygon(outer, fill=fibre)
    if 'margin' in sp:  # cut out of a magazine page: black block inside an off-white margin
        d.polygon(outer, fill=sp['margin'])
        ml, mt, mr, mb = sp['mw']
        blk, _ = _poly(rng, k, pad + ml * k, pad + mt * k, w - (ml + mr) * k, h - (mt + mb) * k, (0, 0, 0, 0), cj=1.0)
        d.polygon(blk, fill=sp['paper'])
    else:
        d.polygon(inner, fill=sp['paper'])
    if sp.get('halftone'):  # printed-magazine dot screen
        dot = tuple(max(0, int(v * 0.88)) for v in sp['paper'])
        step = 4.2 * k
        hm = Image.new('L', (cw, chh), 0)
        hd = ImageDraw.Draw(hm)
        yy = 0
        while yy < chh:
            xx = (step / 2) if int(yy / step) % 2 else 0
            while xx < cw:
                t = (xx + yy) / (cw + chh)  # dots grow toward bottom-right
                r = (0.2 + 0.85 * t) * k
                hd.ellipse([xx - r, yy - r, xx + r, yy + r], fill=255)
                xx += step
            yy += step * 0.866
        inner_m = Image.new('L', (cw, chh), 0)
        ImageDraw.Draw(inner_m).polygon(inner, fill=255)
        rgb = Image.composite(Image.new('RGB', (cw, chh), dot), rgb, ImageChops.multiply(hm, inner_m))
    # glyph
    f = _font(sp['font'], int(sp['fs'] * k))
    gm = Image.new('L', (cw, chh), 0)
    gd = ImageDraw.Draw(gm)
    bb = gd.textbbox((0, 0), sp['ch'], font=f)
    cx, cy = pad + w / 2, pad + h / 2
    gd.text((cx - (bb[0] + bb[2]) / 2 + sp.get('gx', 0) * k, cy - (bb[1] + bb[3]) / 2 + sp.get('gy', 0) * k),
            sp['ch'], font=f, fill=255)
    if sp.get('grot'):
        gm = gm.rotate(sp['grot'], resample=Image.BICUBIC, center=(cx, cy))
    rgb = Image.composite(Image.new('RGB', (cw, chh), sp['ink']), rgb, gm)
    img = rgb.convert('RGBA')
    img.putalpha(alpha)
    img = img.rotate(sp['rot'], resample=Image.BICUBIC, expand=True)
    img = _to_final(img)
    return _grain(img, seed)


def tape_piece(rng, seed, w=46, h=15, rot=-35, col=(238, 228, 196), op=205):
    k = U * SS
    pad = 8 * k
    cw, chh = int(w * k + 2 * pad), int(h * k + 2 * pad)
    outer, _ = _poly(rng, k, pad, pad, w * k, h * k, (0, 1, 0, 1), cj=0.6)
    a = Image.new('L', (cw, chh), 0)
    ImageDraw.Draw(a).polygon(outer, fill=op)
    img = Image.new('RGBA', (cw, chh), col + (0,))
    img.putalpha(a)
    img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
    return _grain(_to_final(img), seed, 5)


DYMO = 'PUNK ENGLISH'   # tiny embossed label-maker tape under the cluster (secondary mark)
DYMO_DX, DYMO_DY, DYMO_ROT = 40, 37, -3


def dymo_label(text, fs=11, track=2.6, hh=19, col=(20, 20, 22), ink=(236, 236, 230)):
    k = U * SS
    f = R.EN(int(fs * k), 800)
    tw = sum(f.getlength(c) for c in text) + track * k * (len(text) - 1)
    padx = 9 * k
    cw, chh = int(tw + 2 * padx), int(hh * k)
    img = Image.new('RGBA', (cw, chh), col + (255,))
    d = ImageDraw.Draw(img)
    d.line([(0, 1.2 * k), (cw, 1.2 * k)], fill=(70, 70, 74, 255), width=int(1.2 * k))  # glossy top edge
    # slanted scissor cuts at both ends
    a = Image.new('L', (cw, chh), 0)
    ImageDraw.Draw(a).polygon([(1.5 * k, 0), (cw, 0), (cw - 1.5 * k, chh), (0, chh)], fill=255)
    bb = d.textbbox((0, 0), 'PUNK', font=f)
    ty = (chh - (bb[3] - bb[1])) / 2 - bb[1]
    x = padx
    for c in text:
        d.text((x + 0.6 * k, ty + 0.8 * k), c, font=f, fill=(0, 0, 0, 255))    # emboss shadow
        d.text((x, ty), c, font=f, fill=ink + (255,))
        x += f.getlength(c) + track * k
    img.putalpha(a)
    img = img.rotate(DYMO_ROT, resample=Image.BICUBIC, expand=True)
    return _to_final(img)


def _shadow(piece, off=(3, 5), blur=3.0, op=0.55):
    a = piece.getchannel('A').point(lambda v: int(v * op))
    sh = Image.new('RGBA', piece.size, (4, 14, 10, 0))
    sh.putalpha(a)
    return sh, (round(off[0] * U), round(off[1] * U)), blur * U


def ransom_logo():
    """Return the RGBA brand mark cropped to its bounding box (incl. shadows)."""
    CW, CH = int(560 * U), int(260 * U)
    canvas = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    total = sum(p['w'] for p in PIECES) - sum(p.get('ov', OVERLAP) for p in PIECES[:-1])
    x = CW / 2 - total * U / 2
    centers = []
    for i, sp in enumerate(PIECES):
        cx = x + sp['w'] * U / 2
        cy = CH / 2 + sp['dy'] * U
        centers.append((cx, cy))
        x += (sp['w'] - sp.get('ov', OVERLAP)) * U
    # z-order: 英 bottom, then 朋, 语, 克 on top (sticker stacking reads as layered collage)
    order = [2, 0, 3, 1]
    pieces = {i: paper_piece(PIECES[i], random.Random(100 + i), 500 + i * 7) for i in range(len(PIECES))}
    for i in order:
        pc = pieces[i]
        cx, cy = centers[i]
        px, py = int(cx - pc.width / 2), int(cy - pc.height / 2)
        sh, (ox, oy), bl = _shadow(pc)
        layer = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
        layer.paste(sh, (px + ox, py + oy))
        layer = layer.filter(ImageFilter.GaussianBlur(bl))
        canvas = Image.alpha_composite(canvas, layer)
        layer = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
        layer.paste(pc, (px, py))
        canvas = Image.alpha_composite(canvas, layer)
    # masking tape on the first and last pieces
    for j, (ci, dx, dy, rot) in enumerate([(0, -30, -34, 38), (3, 30, 34, 32)]):
        tp = tape_piece(random.Random(300 + j), 900 + j, rot=rot)
        cx, cy = centers[ci]
        layer = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
        layer.paste(tp, (int(cx + dx * U - tp.width / 2), int(cy + dy * U - tp.height / 2)))
        canvas = Image.alpha_composite(canvas, layer)
    if DYMO:
        lb = dymo_label(DYMO)
        sh, (ox, oy), bl = _shadow(lb, off=(2, 3), blur=2.0, op=0.6)
        lx = int(CW / 2 + DYMO_DX * U - lb.width / 2)
        ly = int(max(c[1] for c in centers) + DYMO_DY * U)
        layer = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); layer.paste(sh, (lx + ox, ly + oy))
        canvas = Image.alpha_composite(canvas, layer.filter(ImageFilter.GaussianBlur(bl)))
        layer = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); layer.paste(lb, (lx, ly))
        canvas = Image.alpha_composite(canvas, layer)
    bb = canvas.getchannel('A').point(lambda v: 255 if v > 6 else 0).getbbox()
    return canvas.crop(bb)


# ---------------------------------------------------------------- title page
def frame_title2(no, en, zh, hl, ghost, out, variant=1):
    im = base(variant)
    words = [(w, ('h' if w.strip(',.') in hl else 'g' if w.strip(',.') in ghost else 'n')) for w in en.split()]
    for es in range(168 * S, 60, -4):
        ef = R.EN(es, 900)
        lines = wrap(words, ef, 1680 * S)
        if len(lines) <= 3:
            break
    zf = R.ZH(int(es * 0.57), 900)
    logo = ransom_logo()
    lhE = int(es * 1.08)
    ph = int(es * 0.57 * 1.55)
    GAP_BADGE, GAP_LOGO = 48 * S, 46 * S
    total = len(lines) * lhE + GAP_BADGE + ph + GAP_LOGO + logo.height
    top_ink = ef.getbbox(lines[0][0][0])[1]       # empty space above the cap height
    y = (H - (total - top_ink)) / 2 - top_ink      # optical vertical centring
    for ln in lines:
        lw = ef.getlength(' '.join(w for w, _ in ln))
        x = (W - lw) / 2
        for w, k in ln:
            ww = ef.getlength(w)
            if k == 'h':
                m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text((x, y), w, font=ef, fill=255)
                gl = m.filter(ImageFilter.GaussianBlur(18 * S)).point(lambda v: int(v * 0.7))
                im = Image.composite(Image.new('RGB', (W, H), AC2), im, gl)
                g = Image.new('RGB', (W, H)); g.paste(grad(int(ww) + 2, int(es * 1.3), AC1, AC2), (int(x), int(y)))
                im = Image.composite(g, im, m)
            elif k == 'g':
                m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text((x, y), w, font=ef, fill=255)
                gm = Image.new('L', (int(ww) + 2, int(es * 1.3)))
                gd = ImageDraw.Draw(gm)
                for i in range(gm.width):
                    gd.line([(i, 0), (i, gm.height)], fill=int(255 - 230 * (i / gm.width) ** 1.3))
                fm = Image.new('L', (W, H), 0); fm.paste(gm, (int(x), int(y)))
                im = Image.composite(Image.new('RGB', (W, H), (248, 250, 246)), im, ImageChops.multiply(m, fm))
                dots = Image.new('L', (W, H), 0); dd = ImageDraw.Draw(dots)
                rnd = random.Random(3)
                for _ in range(260 * S):
                    px = x + ww * 0.45 + rnd.random() * ww * 0.75; py = y + es * 0.15 + rnd.random() * es * 0.95
                    rr = (rnd.random() * 4 + 1) * S
                    dd.ellipse([px - rr, py - rr, px + rr, py + rr], fill=int(60 + 120 * rnd.random()))
                im = Image.composite(Image.new('RGB', (W, H), (200, 255, 230)), im,
                                     ImageChops.multiply(dots, m.filter(ImageFilter.MaxFilter(15 * S + (S + 1) % 2))))
            else:
                ImageDraw.Draw(im).text((x, y), w, font=ef, fill=(248, 250, 246))
            x += ww + ef.getlength(' ')
        y += lhE
    d = ImageDraw.Draw(im)
    y += GAP_BADGE
    zw = zf.getlength(zh); pad = 48 * S
    d.rounded_rectangle([(W - zw) / 2 - pad, y, (W + zw) / 2 + pad, y + ph], radius=18 * S, fill=AC1)
    bb = d.textbbox((0, 0), zh, font=zf)
    d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], y + (ph - (bb[3] - bb[1])) / 2 - bb[1]), zh, font=zf, fill=(20, 40, 32))
    y += ph + GAP_LOGO
    im = im.convert('RGBA')
    im.alpha_composite(logo, (int((W - logo.width) / 2), int(y)))
    im.convert('RGB').save(out)
    return (int((W - logo.width) / 2), int(y), logo.width, logo.height)


if __name__ == '__main__':
    D = HERE + '/'
    if S == 1:
        frame_title2('01', 'The Robber Who Thought Lemon Juice Made Him Invisible', '以为柠檬汁能隐身的劫匪',
                     ['Lemon', 'Juice'], ['Invisible'], D + 't01.png')
        frame_title2('02', 'The Truth About One Marshmallow', '一颗棉花糖的真相', ['Marshmallow'], [], D + 't02.png')
        frame_title2('03', 'The Doctor Who Drank Bacteria to Win an Argument', '喝下细菌的医生',
                     ['Drank', 'Bacteria'], ['Argument'], D + 't03.png')
    else:
        frame_title2('03', 'The Doctor Who Drank Bacteria to Win an Argument', '喝下细菌的医生',
                     ['Drank', 'Bacteria'], ['Argument'], D + 't03_4k.png')
