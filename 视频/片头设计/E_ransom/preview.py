# dev helper: render t03 and a 2.5x zoom of the logo region
import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'logo/E_ransom')
from PIL import Image
import title_logo as T
D = 'logo/E_ransom/'
x, y, w, h = T.frame_title2('03', 'The Doctor Who Drank Bacteria to Win an Argument', '喝下细菌的医生',
                            ['Drank', 'Bacteria'], ['Argument'], D + 't03.png')
im = Image.open(D + 't03.png'); p = 60 * T.S
c = im.crop((x - p, y - p, x + w + p, y + h + p))
c.resize((c.width * 5 // 2 // T.S, c.height * 5 // 2 // T.S), Image.LANCZOS).save(D + 'zoom.png')
