# dev helper: logo crops + S=1 vs S=2 proportion check (run after rendering t03_4k with VIDEO_S=2)
import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'logo/E_ransom')
from PIL import Image, ImageChops, ImageStat
import title_logo as T
assert T.S == 1
D = 'logo/E_ransom/'
x, y, w, h = T.frame_title2('03', 'The Doctor Who Drank Bacteria to Win an Argument', '喝下细菌的医生',
                            ['Drank', 'Bacteria'], ['Argument'], D + 't03.png')
a = Image.open(D + 't03.png').convert('RGB'); b = Image.open(D + 't03_4k.png').convert('RGB')
p = 36
box = (x - p, y - p, x + w + p, y + h + p)
a.crop(box).save(D + 'logo_crop.png')
b.crop(tuple(v * 2 for v in box)).save(D + 'logo_crop_4k.png')
small = b.resize(a.size, Image.LANCZOS)
diff = ImageChops.difference(a, small)
print('logo box', box, 'mean abs diff (4k downscaled vs 1080p):', [round(v, 2) for v in ImageStat.Stat(diff).mean],
      'logo region:', [round(v, 2) for v in ImageStat.Stat(diff.crop(box)).mean])
c = Image.new('RGB', ((box[2] - box[0]) * 2, box[3] - box[1]))
c.paste(a.crop(box), (0, 0)); c.paste(small.crop(box), (box[2] - box[0], 0))
c.resize((c.width * 2, c.height * 2), Image.LANCZOS).save(D + 'work_compare.png')
