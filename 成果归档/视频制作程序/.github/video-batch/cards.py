#!/usr/bin/env python3
"""Render all seventy reviewed summaries with complete numeric and Latin words."""
import hashlib
import importlib.util
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path.cwd()
TASK = ROOT / '.github/video-batch'
BASE = 'c9d52b26fe981ef8e4c412189ca289716ab8bf00'
spec = importlib.util.spec_from_file_location('approved_preview', ROOT / '.github/video-preview/run.py')
approved = importlib.util.module_from_spec(spec)
spec.loader.exec_module(approved)
summaries = {}
for path in sorted((TASK / 'summaries').glob('*.json')):
    part = json.loads(path.read_text())
    assert not summaries.keys() & part.keys()
    summaries.update(part)
assert sorted(summaries) == [f'{i:02d}' for i in range(1, 71)]
# The latest ALL70 review supersedes the earlier pilot-only wording lock.
# The six current reviewed JSON files are the production text for every article.
def text(no):
    points = summaries[no]
    assert len(points) == 5 and all(len(p) == 2 and 1 <= len(p[0]) <= 4 and p[1] for p in points)
    assert len(set(p[0] for p in points)) == 5
    return '（简述：' + ''.join('▸' + label + '：' + body for label, body in points) + '）'
approved.summary = text
approved.materialize(['视频/工具/render.py', '视频/工具/make_video.py', '视频/工具/fonts'])
out = ROOT / '简述重制预览'
out.mkdir(exist_ok=True)
audit = {}
contact = Image.new('RGB', (2560, 2100), (14, 36, 30))
draw = ImageDraw.Draw(contact)
for i, no in enumerate(sorted(summaries)):
    data = json.loads(approved.get(['git', 'show', BASE + f':视频/脚本/{no}.json']))
    png = out / f'{no}.png'
    layout = approved.render_card(no, data, 3840, 2160, png)
    assert layout['items'] == 5 and layout['font_px'] >= 100
    audit[no] = {
        'title_en': data['title_en'], 'title_zh': data['title_zh'],
        'characters': sum(len(a) + len(b) + 1 for a, b in summaries[no]),
        'summary_sha256': hashlib.sha256(text(no).encode()).hexdigest(),
        'png_sha256': hashlib.sha256(png.read_bytes()).hexdigest(),
        'layout': layout
    }
    thumb = Image.open(png).convert('RGB')
    thumb.thumbnail((350, 197))
    x, y = (i % 7) * 365, (i // 7) * 210
    contact.paste(thumb, (x, y + 12))
    draw.text((x + 4, y), no, fill=(251, 191, 36))
contact.save(out / '70篇总览.jpg', quality=92)
(out / 'layout-audit.json').write_text(json.dumps({
    'articles': len(audit), 'items': 350, 'source_commit': BASE,
    'summary_revision': approved.get(['git', 'rev-parse', 'HEAD']).strip(),
    'text_review_round': 2,
    'specification': {'width': 3840, 'height': 2160, 'standalone': True, 'seconds': 2,
                      'transition': 'first frame after final voice; original end hold replaced'},
    'articles_detail': audit
}, ensure_ascii=False, indent=2) + '\n')
(out / 'summaries.json').write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + '\n')
print(f'All 70 cards rendered; 350 points; font sizes {sorted(set(x["layout"]["font_px"] for x in audit.values()))}.')
