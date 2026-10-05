import sys,os
sys.path.insert(0,'logo/C_graffiti'); sys.path.insert(0,'.')
import title_logo as T
from PIL import Image
tag,anc,tb=T.graffiti_tag(100, angle=T.TAG_ANGLE)
bg=Image.new('RGBA',(tag.width,tag.height),(22,64,50,255))
bg.alpha_composite(tag); bg=bg.convert('RGB')
from PIL import ImageDraw; ImageDraw.Draw(bg).rectangle(tb,outline=(80,80,80))
bg.resize((bg.width*2,bg.height*2),Image.LANCZOS).save(sys.argv[1] if len(sys.argv)>1 else 'logo/C_graffiti/tag_zoom.png')
