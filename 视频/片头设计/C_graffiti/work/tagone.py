import sys,os
sys.path.insert(0,os.path.abspath('logo/C_graffiti')); sys.path.insert(0,'.')
import title_logo as T
from PIL import Image
tag,anc,tb=T.graffiti_tag(T.LOGO_SIZE, angle=T.TAG_ANGLE)
bg=Image.new('RGBA',(tag.width,tag.height),(22,64,50,255))
bg.alpha_composite(tag); bg.convert('RGB').save(sys.argv[1])
