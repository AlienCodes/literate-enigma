#!/usr/bin/env python3
"""Read-only 4K card proof for public full-text rewrites; never render video."""
import ast, base64, copy, functools, hashlib, importlib.util, json, os, re, subprocess
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / '.github/summary37-fallback'
OUT = HERE / 'output'
OUT.mkdir(parents=True, exist_ok=True)
REF = 'bd8e8fcd38877d407fa4284fc9088e7325307f12'
EXPECTED_RENDER_BLOB = 'b94498abbc8317f71283b32bcf2cf5bf640bc7a6'
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)
assert git('rev-parse', 'HEAD:视频/工具/render.py').decode().strip() == EXPECTED_RENDER_BLOB
os.environ['VIDEO_S'] = '2'
spec = importlib.util.spec_from_file_location('card_review_renderer', ROOT / '视频/工具/render.py')
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
R.F = str(ROOT / '视频/工具/fonts') + '/'
nodes = ast.parse((ROOT / '视频/工具/make_video.py').read_text()).body
theme = next(n.value for n in nodes if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'T' for t in n.targets) and isinstance(n.value, ast.Call) and any(k.arg == 'BG_TOP' for k in n.value.keywords))
for k in theme.keywords: setattr(R, k.arg, ast.literal_eval(k.value))
original_font = R.ZH
@functools.lru_cache(maxsize=800)
def font(size, weight=400):
    f = original_font(size, weight)
    f.getlength = functools.lru_cache(maxsize=4096)(f.getlength)
    return f
R.ZH = font
before = json.loads((HERE / 'before.json').read_text())
after = json.loads((HERE / '37-48.json').read_text())
latin = re.compile(r"[A-Za-z0-9]+(?:[.,:'’/-][A-Za-z0-9]+)*(?:[%％])?")
def card(no, points, data, suffix):
    text = '（简述：' + ''.join('▸'+label+'：'+body for label, body in points) + '）'
    data = copy.deepcopy(data)
    c = data['sentences'][-1]['chunks'][-1]
    prefix = (c.get('note') or '').split('（简述：', 1)[0].rstrip()
    c['note'] = (prefix+'\n' if prefix else '')+text
    R.apply_script(data)
    size, lines, first = R.简述排(text)
    f, b = R.ZH(size, 400), R.ZH(size, 700)
    indent = f.getlength('• ')
    widths = [sum((b if bold else f).getlength(ch) for ch, bold in line)+(0 if i in first else indent) for i, line in enumerate(lines)]
    assert len(first) == 5
    assert max(widths) <= R.W*.92+.5
    assert len(lines)*size*1.5 <= (R.H-8*R.S)*.9+.5
    starts = sorted(first)+[len(lines)]
    per_point = []
    tokens = []
    items = R.简述条目(text)
    for i, (start, end) in enumerate(zip(starts, starts[1:])):
        rows = [''.join(ch for ch, _ in line) for line in lines[start:end]]
        actual = ''.join(rows)
        expected = '• '+items[i][0]+items[i][1]
        assert actual == expected, (no, suffix, i, actual, expected)
        offsets, offset = [], 0
        for row in rows[:-1]:
            offset += len(row)
            offsets.append(offset)
        for match in latin.finditer(expected):
            assert not any(match.start() < x < match.end() for x in offsets), (no, match.group(), rows)
            tokens.append(match.group())
        per_point.append({'label':points[i][0], 'lines':rows})
    path = OUT / f'{no}-{suffix}.png'
    R.frame_简述(text, 1, str(path))
    assert Image.open(path).size == (3840,2160)
    return {'font_px':size, 'lines':len(lines), 'items':5, 'max_text_width':max(widths),
            'height_used':len(lines)*size*1.5, 'all_characters_exact':True,
            'all_english_numeric_tokens_whole':True, 'tokens_checked':tokens,
            'per_point':per_point, 'png_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}, path
report = {'source_commit':REF, 'renderer_blob':EXPECTED_RENDER_BLOB,
          'after_summary_git_blob':git('hash-object', str(HERE/'37-48.json')).decode().strip(),
          'video_or_audio_rendered':False, 'articles':{}}
for no in sorted(after, key=int):
    data = json.loads(git('show', f'{REF}:视频/脚本/{no}.json'))
    meta, new_path = card(no, after[no], data, 'after')
    if no in ('37','43','45','48'):
        old_meta, old_path = card(no, before[no], data, 'before')
        meta['previous_layout'] = old_meta
        canvas = Image.new('RGB', (1280,1536), '#092621')
        draw = ImageDraw.Draw(canvas)
        for label, path, y in [('BEFORE — public prior summary',old_path,0),('AFTER — full-text review',new_path,768)]:
            draw.text((24,y+10), label, fill=(251,191,36), font=R.ZH(28,700))
            canvas.paste(Image.open(path).resize((1280,720),Image.Resampling.LANCZOS),(0,y+48))
        import io
        buf = io.BytesIO()
        canvas.save(buf, format='JPEG', quality=78, optimize=True)
        preview = {'article':no, 'top':'before', 'bottom':'after', 'mime_type':'image/jpeg',
                   'data':base64.b64encode(buf.getvalue()).decode(),
                   'after_layout':{k:meta[k] for k in ['font_px','lines','max_text_width','height_used']}}
        (OUT/f'{no}-comparison.json').write_text(json.dumps(preview,ensure_ascii=False)+'\n')
    report['articles'][no] = meta
(OUT/'layout-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({no:{k:m[k] for k in ['font_px','lines','max_text_width','all_characters_exact','all_english_numeric_tokens_whole']} for no,m in report['articles'].items()},ensure_ascii=False))
