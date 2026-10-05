# Title page with the 「朋克英语」 graffiti tag logo (direction C_graffiti).
# Drop-in replacement for title2.frame_title2: same signature, `no` is ignored for display.
# Must run with cwd = video dir (render.py loads fonts from the relative path 'fonts/').
import os, sys, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont
_HERE = os.path.dirname(os.path.abspath(__file__))
_VID = os.path.abspath(os.path.join(_HERE, '..', '..'))
if _VID not in sys.path: sys.path.insert(0, _VID)
import render as R
S = R.S
W, H = 1920*S, 1080*S
LOGO_FONT = os.path.join(_HERE, 'MaShanZheng-Regular.ttf')   # OFL, Google Fonts
LOGO_TXT = '朋克英语'
PLACEMENT = 'below'            # 'below' = signature lockup centred under the Chinese badge | 'corner'
GLINT = True                   # 4-point sparkle on the first character
TAG_ANGLE = 4.0                # degrees, + = rising to the right (sprayed-on tilt)
SUBC = (248, 250, 246, 215)    # colour of the tiny 'PUNK ENGLISH' subline
LOGO_SIZE = 96                 # glyph em of the tag, px at S=1 (scaled by S inside)
KEYLINE = (255, 214, 64)       # thin yellow keyline = the badge yellow -> ties the pink tag to the page palette
KL_W = 2.2                     # keyline width in % of the em
GAP_LOGO = 56                  # px at S=1 between badge and the tag's solid ink (a bit more than title->badge,
                               # so title+badge read as one unit and the tag reads as a sign-off)

def odd(v):
    v = max(1, int(round(v)))
    return v if v % 2 else v+1

def grad(w,h,c1,c2):
    g=Image.new('RGB',(w,h))
    for x in range(w):
        t=x/max(1,w-1); ImageDraw.Draw(g).line([(x,0),(x,h)],fill=tuple(int(a+(b-a)*t) for a,b in zip(c1,c2)))
    return g

def vgrad(w,h,c1,c2):
    g=Image.new('RGB',(w,h)); d=ImageDraw.Draw(g)
    for y in range(h):
        t=y/max(1,h-1); d.line([(0,y),(w,y)],fill=tuple(int(a+(b-a)*t) for a,b in zip(c1,c2)))
    return g

def base(variant):
    im=Image.new('RGB',(W,H))
    top,bot=(10,30,24),(16,44,36)
    d=ImageDraw.Draw(im)
    for y in range(H): d.line([(0,y),(W,y)],fill=tuple(int(a+(b-a)*y/H) for a,b in zip(top,bot)))
    glow=Image.new('L',(W,H),0); ImageDraw.Draw(glow).ellipse([W/2-700*S,H/2-380*S,W/2+700*S,H/2+380*S],fill=90)
    glow=glow.filter(ImageFilter.GaussianBlur(160*S))
    col=(40,120,90) if variant!=2 else (120,90,20)
    im=Image.composite(Image.new('RGB',(W,H),col),im,glow)
    return im

def wrap(words,font,maxw):
    lines=[[]]
    for w in words:
        t=' '.join(x for x,_ in lines[-1]+[w])
        if lines[-1] and font.getlength(t)>maxw: lines.append([w])
        else: lines[-1].append(w)
    return lines

# ---------------------------------------------------------------- graffiti tag
SS = 3   # the tag is built at 3x and downsampled -> smooth splatter dots / drips at any S

def _glyph(ch, fs, stroke, rot, m):
    fi = ImageFont.truetype(LOGO_FONT, fs)
    bb = fi.getbbox(ch, stroke_width=stroke)
    g = Image.new('L', (bb[2]-bb[0]+2*m, bb[3]-bb[1]+2*m), 0)
    ImageDraw.Draw(g).text((m-bb[0], m-bb[1]), ch, font=fi, fill=255, stroke_width=stroke, stroke_fill=255)
    return g.rotate(rot, resample=Image.BICUBIC, expand=True)

def graffiti_tag(size=100, sub=True, angle=-4):
    """Graffiti tag of 朋克英语. size = glyph em in px at S=1.
    Returns (RGBA tag at frame resolution, anchor (cx,cy) = centre of the lettering, bbox of all ink)."""
    rnd = random.Random(20240917)
    u = size*S*SS/100.0                      # 1 unit = 1% of the glyph em (at build resolution)
    pad = int(90*u)
    rot  = [-3, 4, -2, 3]                    # per-character jitter: hand-sprayed rhythm
    dy   = [3, -5, 2, -4]
    sc   = [1.08, 0.96, 1.0, 1.04]
    gap  = [-4*u, -1*u, -3*u]                # ink-to-ink gaps between outlined characters
    OL  = int(round(6.5*u))                  # outline thickness
    FAT = int(round(1.4*u))                  # slight fattening of the brush strokes
    KL  = max(1, int(round(KL_W*u)))         # keyline thickness
    m = OL + FAT + int(6*u)
    G = []
    for i, ch in enumerate(LOGO_TXT):
        fs = int(size*S*SS*sc[i])
        f_ = _glyph(ch, fs, FAT, rot[i], m); o = _glyph(ch, fs, FAT+OL, rot[i], m)
        k_ = _glyph(ch, fs, FAT+KL, rot[i], m)
        G.append((f_, o, o.getbbox(), k_))
    tw = sum(g[2][2]-g[2][0] for g in G) + sum(gap)
    th = max(g[2][3]-g[2][1] for g in G)
    M = Image.new('L', (int(tw+2*pad), int(th+2*pad)), 0); OUT = M.copy(); KM = M.copy()
    x = pad
    for i, (f_, o, b, k_) in enumerate(G):
        ox = int(x - b[0]); oy = int(pad + (th-(b[3]-b[1]))/2 - b[1] + dy[i]*u)
        OUT.paste(255, (ox, oy), o)
        M.paste(255, (ox + (o.width-f_.width)//2, oy + (o.height-f_.height)//2), f_)
        KM.paste(255, (ox + (o.width-k_.width)//2, oy + (o.height-k_.height)//2), k_)
        x += (b[2]-b[0]) + (gap[i] if i < 3 else 0)
    ux0, uy0, ux1, uy1 = OUT.getbbox()                       # unrotated lettering box
    ax, ay = (ux0+ux1)/2, (uy0+uy1)/2
    if angle:   # tilt the lettering as sprayed; drips are added afterwards so gravity stays vertical
        M = M.rotate(angle, resample=Image.BICUBIC, center=(ax, ay))
        KM = KM.rotate(angle, resample=Image.BICUBIC, center=(ax, ay))
        OUT = OUT.rotate(angle, resample=Image.BICUBIC, center=(ax, ay))
    x0, y0, x1, y1 = OUT.getbbox()

    # ---- paint drips, running from the lowest ink near chosen columns
    drips = Image.new('L', M.size, 0); dd = ImageDraw.Draw(drips)
    px = M.load()
    for frac, ln, wd in [(0.06, 34, 7.0), (0.36, 16, 5.6), (0.93, 46, 7.6)]:
        cx = int(x0 + (x1-x0)*frac); best = None
        for xx in range(cx-int(9*u), cx+int(9*u), max(1, SS//2)):
            for yy in range(y1-1, y0, -1):
                if px[xx, yy] > 160:
                    if best is None or yy > best[1]: best = (xx, yy)
                    break
        if not best: continue
        bx, by = best; w = wd*u; L = ln*u; top = by - 9*u
        steps = 24; pts_l = []; pts_r = []
        for k in range(steps+1):                 # body tapers from w to 0.62w, flared where it leaves the stroke
            t = k/steps; yy = top + (L+9*u)*t
            hw = w/2*(0.62 + 0.38*(1-t)**2) + w*0.55*max(0, 1-t*5)**2
            pts_l.append((bx-hw, yy)); pts_r.append((bx+hw, yy))
        dd.polygon(pts_l + pts_r[::-1], fill=255)
        r = w*0.46; dd.ellipse([bx-r, by+L-r*0.9, bx+r, by+L+r*1.25], fill=255)   # drop bulb
    FILL = ImageChops.lighter(M, drips)
    KFILL = ImageChops.lighter(KM, drips.filter(ImageFilter.MaxFilter(odd(2*KL+1))))
    DOUT = ImageChops.lighter(OUT, drips.filter(ImageFilter.MaxFilter(odd(OL*1.2))))
    SH  = ImageChops.offset(DOUT, int(5*u), int(6*u))
    SPR = OUT.filter(ImageFilter.GaussianBlur(16*u))

    PINK1, PINK2 = (255, 102, 174), (255, 30, 112)          # hot punk pink, light -> deep
    INK, SHC = (9, 22, 17), (2, 9, 7)
    tag = Image.new('RGBA', M.size, (0, 0, 0, 0))
    def put(col, mask, a=1.0):
        nonlocal tag
        layer = Image.new('RGBA', M.size, col + (0,))
        layer.putalpha(mask if a == 1.0 else mask.point(lambda v: int(v*a)))
        tag = Image.alpha_composite(tag, layer)
    put(PINK2, SPR, 0.20)                                   # overspray haze
    put(SHC, SH, 0.75)                                      # block shadow
    put(INK, DOUT)                                          # outline
    if KEYLINE: put(KEYLINE, KFILL)                         # light keyline
    fb = FILL.getbbox(); fillimg = Image.new('RGBA', M.size)
    fillimg.paste(vgrad(M.width, fb[3]-fb[1], PINK1, PINK2), (0, fb[1])); fillimg.putalpha(FILL)
    tag = Image.alpha_composite(tag, fillimg)
    shine = ImageChops.subtract(M, ImageChops.offset(M, int(-1*u), int(3*u))).filter(ImageFilter.GaussianBlur(0.6*u))
    put((255, 222, 238), shine, 0.55)                      # wet-paint top-edge shine

    if sub:   # tiny secondary wordmark, sits between the drips, tilted with the lettering
        fsz = int(14*u); ef = R.EN(fsz, 800); txt = 'PUNK ENGLISH'; trk = 0.38*fsz
        tw2 = sum(ef.getlength(c) for c in txt) + trk*(len(txt)-1)
        tx = ax - tw2/2 + 4*u; ty = uy1 + 9*u; tx0 = tx
        sl = Image.new('RGBA', M.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(sl)
        for c in txt:
            dl.text((tx, ty), c, font=ef, fill=SUBC); tx += ef.getlength(c) + trk
        sm = Image.new('L', M.size, 0)
        ImageDraw.Draw(sm).rectangle([tx0, ty + ef.getbbox('P')[1], tx - trk, ty + ef.getbbox('P')[3]], fill=255)
        if angle:
            sl = sl.rotate(angle, resample=Image.BICUBIC, center=(ax, ay)); sm = sm.rotate(angle, resample=Image.BICUBIC, center=(ax, ay))
    # ---- spray splatter (deterministic)
    sp = Image.new('L', M.size, 0); sd = ImageDraw.Draw(sp)
    def dot(cx, cy, r, v=255): sd.ellipse([cx-r, cy-r, cx+r, cy+r], fill=v)
    bx, by = x1 + 2*u, y0 + (y1-y0)*0.28                    # burst flicked off the end of the tag
    dot(bx, by, 4.2*u)
    for _ in range(26):
        a = rnd.gauss(-0.35, 0.55); d = (9 + rnd.random()**1.4*58)*u
        r = max(0.9*u, (3.4 - d/(22*u))*u*rnd.uniform(0.5, 1.0))
        dot(bx + math.cos(a)*d, by + math.sin(a)*d, r)
    for (fx, fy, r) in [(-0.03, 0.80, 3.4), (0.62, 1.06, 2.0), (0.70, -0.06, 1.8)]:
        cx = x0 + (x1-x0)*fx; cy = y0 + (y1-y0)*fy; dot(cx, cy, r*u)
        for k in range(5):
            a = rnd.random()*6.283; d = r*u*(1.9+rnd.random()*2.0); dot(cx+math.cos(a)*d, cy+math.sin(a)*d, r*u*rnd.uniform(0.2, 0.4))
    # fine mist hugging the outline (what a real can leaves at the edge)
    ring = ImageChops.subtract(OUT.filter(ImageFilter.GaussianBlur(7*u)).point(lambda v: 255 if v > 12 else 0), OUT)
    rp = ring.load(); n = 0
    while n < 90:
        cx = rnd.uniform(x0-16*u, x1+16*u); cy = rnd.uniform(y0-16*u, y1+16*u)
        if 0 <= cx < M.width and 0 <= cy < M.height and rp[int(cx), int(cy)]:
            dot(cx, cy, rnd.uniform(0.55, 1.0)*u, int(rnd.uniform(120, 220))); n += 1
    sp = ImageChops.subtract(sp, DOUT)
    if sub: sp = ImageChops.subtract(sp, sm.filter(ImageFilter.MaxFilter(odd(9*u))))   # keep the subline clean
    put(PINK2, sp)

    # 4-point glint on the first character (classic graffiti highlight)
    if GLINT:
        gl = Image.new('L', M.size, 0); gd = ImageDraw.Draw(gl)
        # sit it on the top-left shoulder of 朋 (topmost fill pixel in the first ~8% of columns)
        mp = M.load(); gx = gy = None
        for yy in range(y0, y1):
            for xx in range(x0, int(x0 + (x1-x0)*0.09)):
                if mp[xx, yy] > 200: gx, gy = xx + 2*u, yy + 3*u; break
            if gx is not None: break
        a, b_ = 10*u, 1.8*u
        gd.polygon([(gx, gy-a), (gx+b_, gy-b_), (gx+a, gy), (gx+b_, gy+b_), (gx, gy+a), (gx-b_, gy+b_), (gx-a, gy), (gx-b_, gy-b_)], fill=255)
        put((255, 246, 250), gl, 0.95)
    solid = ImageChops.lighter(DOUT, SH)
    if sub: tag = Image.alpha_composite(tag, sl); solid = ImageChops.lighter(solid, sm)
    # solid ink (outline + drips + block shadow + subline) is what layout aligns to;
    # the soft haze and the splatter are allowed to overhang
    bbox = solid.getbbox()
    tag = tag.resize((tag.width//SS, tag.height//SS), Image.LANCZOS)
    return tag, (ax/SS, ay/SS), tuple(v/SS for v in bbox)

def place_tag(im, tag, bbox, left, top):
    """paste tag so that its solid-ink bbox top-left lands on (left, top)."""
    im.alpha_composite(tag, (int(round(left-bbox[0])), int(round(top-bbox[1]))))
    return im

# ---------------------------------------------------------------- page
def frame_title2(no,en,zh,hl,ghost,out,variant=1):
    im=base(variant); d=ImageDraw.Draw(im)
    AC1,AC2=(255,214,64),(255,120,80)
    words=[(w,('h' if w.strip(',.') in hl else 'g' if w.strip(',.') in ghost else 'n')) for w in en.split()]
    for es in range(168*S,60,-4):
        ef=R.EN(es,900); lines=wrap(words,ef,1680*S)
        if len(lines)<=3: break
    zf=R.ZH(int(es*0.57),900)
    lhE=int(es*1.08); ph=int(es*0.57*1.55)
    tag, anc, tb = graffiti_tag(LOGO_SIZE, angle=TAG_ANGLE)
    tag_w, tag_h = tb[2]-tb[0], tb[3]-tb[1]     # solid ink incl. drips and subline
    capoff = ef.getbbox('H')[1]                 # Inter's internal top leading above cap height
    gapL = GAP_LOGO*S
    stack = len(lines)*lhE - capoff + 48*S + ph + (gapL + tag_h if PLACEMENT=='below' else 0)
    y = (H - stack)/2 - capoff                  # optical centring on visible ink
    for ln in lines:
        lw=ef.getlength(' '.join(w for w,_ in ln)); x=(W-lw)/2
        for w,k in ln:
            ww=ef.getlength(w)
            if k=='h':
                m=Image.new('L',(W,H),0); ImageDraw.Draw(m).text((x,y),w,font=ef,fill=255)
                gl=m.filter(ImageFilter.GaussianBlur(18*S)).point(lambda v:int(v*0.7))
                im=Image.composite(Image.new('RGB',(W,H),AC2),im,gl)
                g=Image.new('RGB',(W,H)); g.paste(grad(int(ww)+2,int(es*1.3),AC1,AC2),(int(x),int(y)))
                im=Image.composite(g,im,m)
            elif k=='g':
                m=Image.new('L',(W,H),0); ImageDraw.Draw(m).text((x,y),w,font=ef,fill=255)
                gm=Image.new('L',(int(ww)+2,int(es*1.3)))
                gd=ImageDraw.Draw(gm)
                for i in range(gm.width): gd.line([(i,0),(i,gm.height)],fill=int(255-230*(i/gm.width)**1.3))
                fm=Image.new('L',(W,H),0); fm.paste(gm,(int(x),int(y)))
                im=Image.composite(Image.new('RGB',(W,H),(248,250,246)),im,ImageChops.multiply(m,fm))
                dots=Image.new('L',(W,H),0); dd=ImageDraw.Draw(dots)
                random.seed(3)
                for _ in range(260*S):
                    px=x+ww*0.45+random.random()*ww*0.75; py=y+es*0.15+random.random()*es*0.95
                    rr=(random.random()*4+1)*S; dd.ellipse([px-rr,py-rr,px+rr,py+rr],fill=int(60+120*random.random()))
                im=Image.composite(Image.new('RGB',(W,H),(200,255,230)),im,ImageChops.multiply(dots,m.filter(ImageFilter.MaxFilter(15*S+(S+1)%2))))
            else:
                ImageDraw.Draw(im).text((x,y),w,font=ef,fill=(248,250,246))
            x+=ww+ef.getlength(' ')
        y+=lhE
    d=ImageDraw.Draw(im)
    y+=48*S
    zw=zf.getlength(zh); pad=48*S
    d.rounded_rectangle([(W-zw)/2-pad,y,(W+zw)/2+pad,y+ph],radius=18*S,fill=AC1)
    bb=d.textbbox((0,0),zh,font=zf); d.text(((W-(bb[2]-bb[0]))/2-bb[0],y+(ph-(bb[3]-bb[1]))/2-bb[1]),zh,font=zf,fill=(20,40,32))
    y+=ph
    im=im.convert('RGBA')
    if PLACEMENT=='below':
        im = place_tag(im, tag, tb, W/2 - (anc[0]-tb[0]), y + gapL)
    else:
        im = place_tag(im, tag, tb, W - 70*S - tag_w, H - 60*S - tag_h)
    im.convert('RGB').save(out)

if __name__=='__main__':
    os.chdir(_VID)
    o = sys.argv[1] if len(sys.argv)>1 else _HERE
    frame_title2('01','The Robber Who Thought Lemon Juice Made Him Invisible','以为柠檬汁能隐身的劫匪',['Lemon','Juice'],['Invisible'],os.path.join(o,'t01.png'))
    frame_title2('02','The Truth About One Marshmallow','一颗棉花糖的真相',['Marshmallow'],[],os.path.join(o,'t02.png'))
    frame_title2('03','The Doctor Who Drank Bacteria to Win an Argument','喝下细菌的医生',['Drank','Bacteria'],['Argument'],os.path.join(o,'t03.png'))
