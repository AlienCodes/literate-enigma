# Title page with the 「朋克英语」 rubber-stamp / seal brand mark (direction A_stamp).
# Drop-in replacement for title2.frame_title2(no,en,zh,hl,ghost,out,variant=1).
# The article number `no` is accepted but no longer displayed.
import os, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
_VID_CANDIDATES = [os.getcwd(), HERE, os.path.abspath(os.path.join(HERE, '..', '..'))]
for _p in _VID_CANDIDATES:
    if os.path.exists(os.path.join(_p, 'render.py')):
        if _p not in sys.path: sys.path.insert(0, _p)
        break
import render as R
if not os.path.exists(R.F + 'Inter.ttf'):          # make font loading cwd-independent
    for _p in _VID_CANDIDATES:
        if os.path.exists(os.path.join(_p, 'fonts', 'Inter.ttf')):
            R.F = os.path.join(_p, 'fonts') + '/'; break

S = R.S
W, H = 1920 * S, 1080 * S

# ---------------------------------------------------------------- logo font
LOGO_TEXT = '朋克英语'
# Noto Sans SC Black (OFL, already in video/fonts): after testing ZCOOL QingKe HuangYou and
# Noto Serif SC Black inside the seal, the sans was the only face whose knocked-out strokes stay
# legible at ~50 px per character (phone size).
LOGO_FONT = os.path.join(R.F, 'NotoSansSC.ttf')
LOGO_WGHT = 900


def _logo_font(size):
    f = ImageFont.truetype(LOGO_FONT, size)
    if LOGO_WGHT:
        f.set_variation_by_axes([LOGO_WGHT])
    return f


def _check_glyphs(path, text):
    """Fail loudly if any logo character would fall back to .notdef."""
    from fontTools.ttLib import TTFont
    cmap = TTFont(path, lazy=True).getBestCmap()
    miss = [c for c in text if ord(c) not in cmap]
    if miss: raise ValueError(f'logo font lacks glyphs: {miss}')
    f = _logo_font(120)
    def bm(c):
        im = Image.new('L', (160, 160)); ImageDraw.Draw(im).text((10, 0), c, font=f, fill=255); return im.tobytes()
    nd = bm('\U000F0000')                       # private-use char -> .notdef box
    for c in text:
        if bm(c) == nd: raise ValueError(f'logo glyph {c} renders as .notdef')
_check_glyphs(LOGO_FONT, LOGO_TEXT)

# ---------------------------------------------------------------- seal look
SEAL_INK = (252, 42, 92)           # hot punk vermilion-magenta (pairs with the yellow badge, pops on green)
SEAL_REL = 1.04                    # seal edge = badge height x this (so it scales with S and title size)
SEAL_ANGLE = -7.0                  # degrees, PIL counter-clockwise positive -> tilted clockwise
SEAL_SEED = 1977                   # deterministic texture (year punk broke)
SS = 4                             # supersampling for the seal


def _vnoise(rng, cells, size):
    """Smooth value noise: `cells`x`cells` random grid bicubically resized to size.
    Same seed -> same continuous field at any resolution (S-invariant)."""
    a = rng.rand(cells, cells).astype(np.float32)
    return np.asarray(Image.fromarray(a).resize((size, size), Image.BICUBIC))


def _blur(a, r):
    if r < 0.5: return a
    u = Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8))
    return np.asarray(u.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255.0


def _glyph_cell(ch, w, h):
    """Render one glyph and stretch its ink box to exactly fill a w x h cell (seal-carver style)."""
    fs = int(h * 1.4)
    f = _logo_font(fs)
    im = Image.new('L', (fs * 2, fs * 2)); ImageDraw.Draw(im).text((fs // 3, fs // 3), ch, font=f, fill=255)
    im = im.crop(im.getbbox())
    return im.resize((w, h), Image.LANCZOS)


def make_seal(px):
    """Return (RGBA image, canvas_px) of the distressed seal; seal edge = px output pixels.
    The seal is centred in a square canvas of side canvas_px."""
    P = px * SS                                     # seal edge at hi-res
    C = int(round(P * 1.5)); C += C % 2             # canvas with room for rotation/rough edges
    o = (C - P) // 2
    # B = solid stone face, K = what the carver cut away (frame line + characters)
    b = Image.new('L', (C, C), 0)
    ImageDraw.Draw(b).rounded_rectangle([o, o, o + P, o + P], radius=int(P * 0.06), fill=255)
    k = Image.new('L', (C, C), 0); d = ImageDraw.Draw(k)
    fi, fw = P * 0.058, max(1, int(P * 0.020))
    # inner frame: clean ring = outer rounded rect minus inner one
    d.rounded_rectangle([o + fi, o + fi, o + P - fi, o + P - fi], radius=int(P * 0.035), fill=255)
    d.rounded_rectangle([o + fi + fw, o + fi + fw, o + P - fi - fw, o + P - fi - fw], radius=int(P * 0.035) - fw, fill=0)
    # 2x2 characters, knocked out (白文), modern reading order: 朋克 / 英语
    ci = P * 0.128; gap = P * 0.07
    thin = 2 * int(round(P * 0.005)) + 1            # slightly thinner cuts -> more red between strokes
    cw = int((P - 2 * ci - gap) / 2)
    for i, ch in enumerate(LOGO_TEXT):
        r_, c_ = divmod(i, 2)
        g = _glyph_cell(ch, cw, cw)
        if thin > 1: g = g.filter(ImageFilter.MinFilter(thin))
        x = int(o + ci + c_ * (cw + gap)); y = int(o + ci + r_ * (cw + gap))
        k.paste(255, (x, y), g)
    B = np.asarray(b).astype(np.float32) / 255.0
    K = np.asarray(k).astype(np.float32) / 255.0

    rng = np.random.RandomState(SEAL_SEED)
    def rough(M, ramp, amp, cells):
        """Wider ramp + low-amplitude noise, then a steep threshold -> crisp but irregular edge."""
        Mb = _blur(M, P * ramp)
        n = sum((_vnoise(rng, c, C) - 0.5) * w for c, w in cells)
        return np.clip((Mb + n * amp - 0.5) * 70 + 0.5, 0, 1)
    Bm = rough(B, 0.010, 0.55, [(9, 0.6), (40, 0.5), (130, 0.35)])     # chewed outer edge
    # cuts: wobble by displacement (no threshold -> thin frame line never balloons into blobs)
    yy_i, xx_i = np.mgrid[0:C, 0:C]
    amp = P * 0.006
    dx = ((_vnoise(rng, 48, C) - 0.5) * 2 * amp).astype(np.int32)
    dy = ((_vnoise(rng, 48, C) - 0.5) * 2 * amp).astype(np.int32)
    Km = K[np.clip(yy_i + dy, 0, C - 1), np.clip(xx_i + dx, 0, C - 1)]
    M1 = Bm * (1 - Km)
    # uneven ink pressure: low-freq density + lighter top-left (stamp rocked to the right)
    yy, xx = np.mgrid[0:C, 0:C].astype(np.float32) / C
    dens = 0.90 + 0.10 * _vnoise(rng, 5, C)
    dens *= 0.88 + 0.12 * np.clip(xx * 0.7 + yy * 0.7, 0, 1)
    # ink voids: worn patches mostly near the rim, small specks, fine grain
    r = np.maximum(np.abs(xx - 0.5), np.abs(yy - 0.5)) / (P / C / 2)      # 0 centre .. 1 rim
    rim = np.clip((r - 0.70) / 0.30, 0, 1)
    blot = _vnoise(rng, 22, C) + 0.30 * (_vnoise(rng, 260, C) - 0.5)     # worn patches with ragged borders
    holes = np.clip((blot - 0.92 + 0.24 * rim) * 80, 0, 1)
    speck = 0.62 * _vnoise(rng, 150, C) + 0.38 * _vnoise(rng, 380, C)   # two scales -> ragged, non-round voids
    speck = 0.5 + (speck - 0.5) * 1.35
    holes = np.maximum(holes, np.clip((speck - 0.935 + 0.07 * rim) * 80, 0, 1))
    grain = _vnoise(rng, 480, C)
    A = M1 * np.minimum(1, dens * 1.04) * (1 - holes) * (0.90 + 0.10 * grain)
    alpha = Image.fromarray(np.clip(A * 255, 0, 255).astype(np.uint8))
    rgba = Image.new('RGBA', (C, C), SEAL_INK + (0,)); rgba.putalpha(alpha)
    rgba = rgba.rotate(SEAL_ANGLE, resample=Image.BICUBIC)
    out = rgba.resize((C // SS, C // SS), Image.LANCZOS)
    return out, C // SS


def stamp(im, cx, cy, px):
    """Composite the seal centred at (cx,cy) on RGB image im."""
    seal, c = make_seal(px)
    base = im.convert('RGBA')
    base.alpha_composite(seal, (int(round(cx - c / 2)), int(round(cy - c / 2))))
    return base.convert('RGB')


# ---------------------------------------------------------------- page
def grad(w, h, c1, c2):
    g = Image.new('RGB', (w, h))
    for x in range(w):
        t = x / max(1, w - 1); ImageDraw.Draw(g).line([(x, 0), (x, h)], fill=tuple(int(a + (b - a) * t) for a, b in zip(c1, c2)))
    return g


def base(variant):
    im = Image.new('RGB', (W, H))
    top, bot = (10, 30, 24), (16, 44, 36)
    d = ImageDraw.Draw(im)
    for y in range(H): d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * y / H) for a, b in zip(top, bot)))
    glow = Image.new('L', (W, H), 0); ImageDraw.Draw(glow).ellipse([W / 2 - 700 * S, H / 2 - 380 * S, W / 2 + 700 * S, H / 2 + 380 * S], fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(160 * S))
    col = (40, 120, 90) if variant != 2 else (120, 90, 20)
    im = Image.composite(Image.new('RGB', (W, H), col), im, glow)
    return im


def wrap(words, font, maxw):
    lines = [[]]
    for w in words:
        t = ' '.join(x for x, _ in lines[-1] + [w])
        if lines[-1] and font.getlength(t) > maxw: lines.append([w])
        else: lines[-1].append(w)
    return lines


def frame_title2(no, en, zh, hl, ghost, out, variant=1):
    im = base(variant)
    AC1, AC2 = (255, 214, 64), (255, 120, 80)
    words = [(w, ('h' if w.strip(',.') in hl else 'g' if w.strip(',.') in ghost else 'n')) for w in en.split()]
    for es in range(168 * S, 60, -4):
        ef = R.EN(es, 900); lines = wrap(words, ef, 1680 * S)
        if len(lines) <= 3: break
    zf = R.ZH(int(es * 0.57), 900)
    lhE = int(es * 1.08)
    ph = int(es * 0.57 * 1.55)
    gap = 48 * S
    seal_px = int(round(ph * SEAL_REL))           # seal edge tied to the badge height (scales with S and title size)
    # no kicker / watermark any more: centre the visual block (cap-top of line 1 .. bottom of badge row)
    cap_top = int(es * 0.24)
    block = len(lines) * lhE + gap + ph - cap_top
    y = (H - block) / 2 - cap_top
    for ln in lines:
        lw = ef.getlength(' '.join(w for w, _ in ln)); x = (W - lw) / 2
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
                for i in range(gm.width): gd.line([(i, 0), (i, gm.height)], fill=int(255 - 230 * (i / gm.width) ** 1.3))
                fm = Image.new('L', (W, H), 0); fm.paste(gm, (int(x), int(y)))
                im = Image.composite(Image.new('RGB', (W, H), (248, 250, 246)), im, ImageChops.multiply(m, fm))
                dots = Image.new('L', (W, H), 0); dd = ImageDraw.Draw(dots)
                random.seed(3)
                for _ in range(260 * S):
                    px = x + ww * 0.45 + random.random() * ww * 0.75; py = y + es * 0.15 + random.random() * es * 0.95
                    rr = (random.random() * 4 + 1) * S; dd.ellipse([px - rr, py - rr, px + rr, py + rr], fill=int(60 + 120 * random.random()))
                im = Image.composite(Image.new('RGB', (W, H), (200, 255, 230)), im, ImageChops.multiply(dots, m.filter(ImageFilter.MaxFilter(15 * S + (S + 1) % 2))))
            else:
                ImageDraw.Draw(im).text((x, y), w, font=ef, fill=(248, 250, 246))
            x += ww + ef.getlength(' ')
        y += lhE
    d = ImageDraw.Draw(im)
    y += gap
    zw = zf.getlength(zh); pad = 48 * S
    bw = zw + 2 * pad
    # lockup: [badge][seal] is centred as one unit, the seal signs off the title like a 落款 seal
    lgap = 30 * S; sv = seal_px * 1.10                 # visual width of the tilted seal
    bx0 = (W - bw - lgap - sv) / 2; bx1 = bx0 + bw
    d.rounded_rectangle([bx0, y, bx1, y + ph], radius=18 * S, fill=AC1)
    bb = d.textbbox((0, 0), zh, font=zf)
    d.text((bx0 + (bw - (bb[2] - bb[0])) / 2 - bb[0], y + (ph - (bb[3] - bb[1])) / 2 - bb[1]), zh, font=zf, fill=(20, 40, 32))
    # ---- brand seal 「朋克英语」
    im = stamp(im, bx1 + lgap + sv / 2, y + ph / 2, seal_px)
    im.save(out)


if __name__ == '__main__':
    o = sys.argv[1] if len(sys.argv) > 1 else HERE
    frame_title2('01', 'The Robber Who Thought Lemon Juice Made Him Invisible', '以为柠檬汁能隐身的劫匪', ['Lemon', 'Juice'], ['Invisible'], os.path.join(o, 't01.png'))
    frame_title2('02', 'The Truth About One Marshmallow', '一颗棉花糖的真相', ['Marshmallow'], [], os.path.join(o, 't02.png'))
    frame_title2('03', 'The Doctor Who Drank Bacteria to Win an Argument', '喝下细菌的医生', ['Drank', 'Bacteria'], ['Argument'], os.path.join(o, 't03.png'))
