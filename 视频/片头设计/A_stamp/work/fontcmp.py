import sys,os; sys.path.insert(0,'logo/A_stamp')
os.environ['SEAL_INK']='255,40,100'
import title_logo as T
from PIL import Image, ImageFont
fonts={'zcool':T.LOGO_FONT,'noto':None}
tiles=[]
for fname in ['zcool','noto']:
    for thin in [True,False]:
        if fname=='noto':
            def gc(ch,w,h,_o=T._glyph_cell):
                import render as R
                from PIL import ImageDraw
                fs=int(h*1.4); f=R.ZH(fs,900)
                im=Image.new('L',(fs*2,fs*2)); ImageDraw.Draw(im).text((fs//3,fs//3),ch,font=f,fill=255)
                im=im.crop(im.getbbox()); return im.resize((w,h),Image.LANCZOS)
            T._glyph_cell=gc
        else:
            T._glyph_cell=orig if 'orig' in dir() else T._glyph_cell; orig=T._glyph_cell
        src=open('logo/A_stamp/title_logo.py').read()
        s,c=T.make_seal(154)
        bg=Image.new('RGBA',(c,c),(16,44,36,255)); bg.alpha_composite(s); tiles.append(bg.convert('RGB'))
out=Image.new('RGB',(len(tiles)*(tiles[0].width+10),tiles[0].height*3+10))
for i,t in enumerate(tiles):
    out.paste(t,(i*(t.width+10),0)); out.paste(t.resize((t.width*2,t.height*2),Image.LANCZOS).crop((0,0,t.width,t.height*2)),(i*(t.width+10),t.height+10))
out.save('logo/A_stamp/work/fontcmp.png')
