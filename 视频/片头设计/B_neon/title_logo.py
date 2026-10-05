# B_neon: opening title page with a neon-sign 「朋克英语」 brand mark.
# Drop-in replacement for title2.frame_title2 (same signature; `no` is no longer displayed).
# Run with cwd = the video/ directory (render.py loads fonts from the relative path 'fonts/').
import os, sys, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.dirname(os.path.dirname(HERE))
if VIDEO not in sys.path: sys.path.insert(0, VIDEO)
import render as R
S = R.S
W, H = 1920*S, 1080*S
BRAND = '朋克英语'
NEON_FONT = os.path.join(HERE, 'ZCOOLQingKeHuangYou-Regular.ttf')   # OFL, Google Fonts

def odd(n):
    n = max(1, int(round(n))); return n if n % 2 else n+1

def grad(w,h,c1,c2):
    g=Image.new('RGB',(w,h))
    for x in range(w):
        t=x/max(1,w-1); ImageDraw.Draw(g).line([(x,0),(x,h)],fill=tuple(int(a+(b-a)*t) for a,b in zip(c1,c2)))
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

# ---------------------------------------------------------------- neon logo
def _tint(m, c):
    return Image.merge('RGB', [m.point(lambda v, k=k: v*k//255) for k in c])

def _gain(m, a):
    return m.point(lambda v, a=a: min(255, int(v*a)))

PINK  = (255, 54, 150)    # tube colour (hot pink - nods to the yellow+pink punk palette with the badge)
CORE  = (255, 238, 247)   # white-hot centre of the tube
CYAN  = (40, 236, 255)    # RGB-split channel and the 「 」 corner tubes
CYAN_CORE = (215, 252, 255)
RED   = (255, 30, 60)

def neon_logo(u, tag=False):
    """Neon lockup  「朋克英语」  drawn in units of u (= S at the design size).
    Returns (light, (ox,oy), (vis_w,vis_h)): an additive RGB light layer on black, the offset
    of the visual box (bracket corners) inside it and the visual size of the lockup."""
    fs = 70*u
    f = ImageFont.truetype(NEON_FONT, fs)
    bb = f.getbbox(BRAND); tw, th = bb[2]-bb[0], bb[3]-bb[1]
    bo = 21*u          # bracket offset from the characters
    bl = 30*u          # bracket arm length
    bw = 4*u           # bracket tube width
    tag_h = tag_gap = 0
    if tag:
        sub = R.EN(15*u, 700); st = 'PUNK ENGLISH'; sbb = sub.getbbox(st)
        tag_gap = 22*u; tag_h = sbb[3]-sbb[1]
    vis_w = tw + 2*bo; vis_h = th + 2*bo + tag_gap + tag_h
    pad = 80*u
    w, h = int(vis_w + 2*pad), int(vis_h + 2*pad); ox, oy = pad, pad
    # pink tube mask: the four characters
    M = Image.new('L', (w, h), 0)
    ImageDraw.Draw(M).text((ox + bo - bb[0], oy + bo - bb[1]), BRAND, font=f, fill=255)
    # cyan accent mask: 「 」 corner tubes (+ optional tag line)
    C = Image.new('L', (w, h), 0); cd = ImageDraw.Draw(C)
    x0, y0, x1, y1 = ox, oy, ox + vis_w, oy + th + 2*bo
    r = bw/2
    for pts in ([(x0, y0+bl), (x0, y0), (x0+bl, y0)], [(x1-bl, y1), (x1, y1), (x1, y1-bl)]):
        cd.line(pts, fill=255, width=bw, joint='curve')
        for p in (pts[0], pts[2]): cd.ellipse([p[0]-r, p[1]-r, p[0]+r, p[1]+r], fill=255)
    if tag:
        widths = [sub.getlength(c) for c in st]; tr = (tw - sum(widths))/(len(st)-1)
        x = ox + bo; ty = y1 + tag_gap - sbb[1]
        for c, cw in zip(st, widths):
            cd.text((x, ty), c, font=sub, fill=255); x += cw + tr
    out = Image.new('RGB', (w, h), 0)
    # bloom on the wall: three radii
    for rad, a in ((48*u, 0.50), (18*u, 0.95), (6*u, 1.30)):
        out = ImageChops.screen(out, _tint(_gain(M.filter(ImageFilter.GaussianBlur(rad)), a), PINK))
    for rad, a in ((20*u, 0.75), (6*u, 1.1)):
        out = ImageChops.screen(out, _tint(_gain(C.filter(ImageFilter.GaussianBlur(rad)), a), CYAN))
    # glitch: RGB split - cyan channel slips left, red channel slips right
    d = 3*u
    out = ImageChops.screen(out, _tint(_gain(ImageChops.offset(M, -d, 0), 0.62), CYAN))
    out = ImageChops.screen(out, _tint(_gain(ImageChops.offset(M, d, 0), 0.32), RED))
    # glass tube + white-hot core
    out = Image.composite(Image.new('RGB', (w, h), PINK), out, M.filter(ImageFilter.GaussianBlur(0.8*u)))
    core = M.filter(ImageFilter.MinFilter(4*u+1)).filter(ImageFilter.GaussianBlur(1.5*u))
    out = Image.composite(Image.new('RGB', (w, h), CORE), out, _gain(core, 1.1))
    out = Image.composite(Image.new('RGB', (w, h), CYAN), out, C.filter(ImageFilter.GaussianBlur(0.7*u)))
    cc = C.filter(ImageFilter.MinFilter(2*u+1)).filter(ImageFilter.GaussianBlur(0.8*u))
    out = Image.composite(Image.new('RGB', (w, h), CYAN_CORE), out, _gain(cc, 0.9))
    return out, (ox, oy), (vis_w, vis_h)

def paste_light(im, layer, x, y):
    """Screen-blend an additive light layer onto im at integer (x,y), clipped to the frame."""
    x, y = int(round(x)), int(round(y))
    box = (max(0, x), max(0, y), min(im.width, x+layer.width), min(im.height, y+layer.height))
    reg = im.crop(box); lay = layer.crop((box[0]-x, box[1]-y, box[2]-x, box[3]-y))
    im.paste(ImageChops.screen(reg, lay), box[:2])
    return im

# ---------------------------------------------------------------- title page
def frame_title2(no,en,zh,hl,ghost,out,variant=1):
    im=base(variant)
    AC1,AC2=(255,214,64),(255,120,80)
    words=[(w,('h' if w.strip(',.') in hl else 'g' if w.strip(',.') in ghost else 'n')) for w in en.split()]
    for es in range(168*S,60,-4):
        ef=R.EN(es,900); lines=wrap(words,ef,1680*S)
        if len(lines)<=3: break
    zf=R.ZH(int(es*0.57),900)
    lhE=int(es*1.08); ph=int(es*0.57*1.55)
    # logo lockup (size fixed in S units, independent of the title size)
    logo,(lox,loy),(lw,lh)=neon_logo(S)
    GAP_LOGO=64*S
    cap_top=ef.getbbox('T')[1]                      # Inter puts cap top ~0.24em below y
    vis_h=len(lines)*lhE-cap_top+48*S+ph+GAP_LOGO+lh
    y=(H-vis_h)/2-cap_top-6*S                        # optical centre, a hair above middle
    for ln in lines:
        lw_=ef.getlength(' '.join(w for w,_ in ln)); x=(W-lw_)/2
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
    y+=ph+GAP_LOGO
    # the neon sign (screen-blended: it only adds light)
    paste_light(im,logo,W/2-lw/2-lox,y-loy)
    im.save(out)

if __name__=='__main__':
    o=os.path.join(HERE,'t01.png')
    frame_title2('01','The Robber Who Thought Lemon Juice Made Him Invisible','以为柠檬汁能隐身的劫匪',['Lemon','Juice'],['Invisible'],o)
