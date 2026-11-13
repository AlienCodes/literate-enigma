from __future__ import annotations

import hashlib
import json
import math
import re
from html import escape
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output'
OUT.mkdir(exist_ok=True)
W, H = 176 * 72 / 25.4, 250 * 72 / 25.4
M = 37.0
CW = W - 2 * M
FOREST = colors.HexColor('#284E43')
INK = colors.HexColor('#293B35')
MUTED = colors.HexColor('#77837A')
PALE = colors.HexColor('#F3F5EF')
PAPER = colors.HexColor('#FDFBF6')
YELLOW = colors.HexColor('#E7C46E')
LINE = colors.HexColor('#DFE5DB')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


TEXT = load(ROOT / 'content/01-text.json')
VOCAB = load(ROOT / 'content/01-vocabulary.json')
SOURCE = load(ROOT / 'sources/01.json')
SUMMARY = SOURCE['approved_summary']
ILLUSTRATION = ROOT / 'illustrations/01-preview.png'

FONT_FILES = {
    'CN': ROOT / 'fonts/NotoSansSC-400.ttf',
    'CNB': ROOT / 'fonts/NotoSansSC-600.ttf',
    'EN': ROOT / 'fonts/LiberationSerif-Regular.ttf',
    'ENI': ROOT / 'fonts/LiberationSerif-Italic.ttf',
    'ENB': ROOT / 'fonts/LiberationSerif-Bold.ttf',
    'SANS': ROOT / 'fonts/LiberationSans-Regular.ttf',
    'SANSB': ROOT / 'fonts/LiberationSans-Bold.ttf',
}
for name, path in FONT_FILES.items():
    pdfmetrics.registerFont(TTFont(name, str(path)))


LAYOUT = []


def style(font, size, leading=None, color=INK, cjk=False):
    return ParagraphStyle('s', fontName=font, fontSize=size,
                          leading=leading or size * 1.45, textColor=color,
                          alignment=TA_LEFT, wordWrap='CJK' if cjk else None,
                          splitLongWords=False, allowWidows=False,
                          allowOrphans=False, spaceAfter=0, spaceBefore=0)


def para(c, text, x, top, width, font='CN', size=11, leading=None,
         color=INK, cjk=True, mark=True):
    p = Paragraph(text, style(font, size, leading, color, cjk))
    pw, ph = p.wrap(width, H * 2)
    if mark:
        if top - ph < 42 or top > H - 24:
            raise RuntimeError(f'Text outside page: {text[:50]} at {top - ph}')
        LAYOUT.append({'page': c.getPageNumber(), 'kind': 'text',
                       'bbox': [x, top - ph, x + width, top],
                       'font': font, 'font_size': size, 'height': ph,
                       'text': re.sub('<[^>]+>', '', text)})
    p.drawOn(c, x, top - ph)
    return top - ph


def text(c, value, x, y, font='CN', size=10, color=INK):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, value)


def rule(c, x, y, width, color=LINE, weight=.6):
    c.setStrokeColor(color)
    c.setLineWidth(weight)
    c.line(x, y, x + width, y)


def footer(c, page):
    rule(c, M, 36, CW)
    text(c, '01  以为柠檬汁能隐身的劫匪', M, 22, size=8.1, color=MUTED)
    c.setFont('SANS', 8.7)
    c.setFillColor(MUTED)
    c.drawRightString(W - M, 22, f'{page:02d} / 06')


def page(c, bookmark, kicker, title, subtitle=None):
    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.bookmarkPage(bookmark)
    c.addOutlineEntry(title, bookmark, level=0, closed=False)
    text(c, kicker, M, H - 39, font='SANS', size=8.4, color=MUTED)
    text(c, title, M, H - 71, font='CNB', size=19, color=FOREST)
    top = H - 91
    if subtitle:
        top = para(c, escape(subtitle), M, top, CW, size=9.3, leading=14,
                   color=MUTED) - 17
    else:
        top -= 10
    return top


def finish(c):
    footer(c, c.getPageNumber())
    c.showPage()


def cover(c):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.bookmarkPage('cover')
    c.addOutlineEntry('第01篇 插图阅读小册', 'cover', level=0, closed=False)
    text(c, 'STORIES TO READ AND REMEMBER', M, H - 39,
         font='SANS', size=8.1, color=FOREST)
    c.setFillColor(YELLOW)
    c.roundRect(W - M - 35, H - 57, 35, 27, 6, stroke=0, fill=1)
    text(c, '01', W - M - 26, H - 49, font='ENB', size=18, color=FOREST)
    top = H - 84
    top = para(c, '以为柠檬汁<br/>能隐身的劫匪', M, top, CW,
               font='CNB', size=26, leading=35, color=FOREST) - 14
    top = para(c, escape(TEXT['title_en']), M, top, CW,
               font='ENI', size=17.4, leading=21.8, cjk=False) - 21
    iw, ih = ImageReader(str(ILLUSTRATION)).getSize()
    image_height = CW * ih / iw
    bottom = top - image_height
    if bottom < 130:
        raise RuntimeError('Cover illustration leaves insufficient breathing room')
    c.drawImage(str(ILLUSTRATION), M, bottom, width=CW,
                height=image_height, preserveAspectRatio=True, mask='auto')
    LAYOUT.append({'page': 1, 'kind': 'image',
                   'bbox': [M, bottom, W - M, top], 'source': str(ILLUSTRATION)})
    question_top = bottom - 22
    para(c, '我们为什么有时看不见自己的判断失误？', M, question_top,
         CW, font='CN', size=11.2, leading=17, color=FOREST)
    rule(c, M, 91, CW)
    labels = [('READ', '纯净阅读'), ('CHECK', '中文核对'),
              ('LEARN', '词汇记忆'), ('RECALL', '回想巩固')]
    for i, (en, zh) in enumerate(labels):
        x = M + i * CW / 4
        text(c, en, x, 73, 'SANSB', 8.1, FOREST)
        text(c, zh, x, 56, 'CN', 9.1, MUTED)
    finish(c)


def measured_paragraph_height(values, width, font, size, leading, gap, cjk):
    heights = []
    for value in values:
        p = Paragraph(escape(value), style(font, size, leading, INK, cjk))
        heights.append(p.wrap(width, H * 2)[1])
    return sum(heights) + gap * (len(values) - 1), heights


def english(c):
    top = page(c, 'english', '01 / READ', '英文原文')
    values = TEXT['english_paragraphs']
    candidates = [(13.0, 20.3, 8.8), (12.7, 19.8, 8.5),
                  (12.4, 19.3, 8), (12.1, 18.8, 7.8)]
    for size, leading, gap in candidates:
        h, _ = measured_paragraph_height(values, CW, 'EN', size, leading, gap, False)
        if h <= top - 55:
            break
    else:
        raise RuntimeError('English body does not fit comfortably')
    for i, value in enumerate(values):
        top = para(c, escape(value), M, top, CW, 'EN', size,
                   leading, INK, False)
        if i < len(values) - 1:
            top -= gap
    finish(c)


def chinese(c):
    top = page(c, 'chinese', '02 / CHECK', '中文译文')
    values = TEXT['chinese_paragraphs']
    for size, leading, gap in [(12.0, 20.0, 8.5), (11.7, 19.6, 8),
                               (11.4, 19.0, 7.5)]:
        h, _ = measured_paragraph_height(values, CW, 'CN', size, leading, gap, True)
        if h <= top - 128:
            break
    else:
        raise RuntimeError('Chinese body does not fit with percentile note')
    for i, value in enumerate(values):
        top = para(c, escape(value), M, top, CW, 'CN', size, leading)
        if i < len(values) - 1:
            top -= gap
    note_top = min(top - 20, 123)
    note = ('<font name="CNB">读懂 percentile</font><br/>'
            '百分位表示一个人在群体中的相对位置。第12百分位不等于答对了12%的题。')
    note_p = Paragraph(note, style('CN', 9.5, 14.5, FOREST, True))
    note_h = note_p.wrap(CW - 24, 100)[1] + 20
    if note_top - note_h < 49:
        raise RuntimeError('Percentile note overlaps footer')
    c.setFillColor(PALE)
    c.roundRect(M, note_top - note_h, CW, note_h, 6, stroke=0, fill=1)
    para(c, note, M + 12, note_top - 10, CW - 24,
         'CN', 9.5, 14.5, FOREST)
    finish(c)


def entry_parts(e, width, core):
    head_size = 11.5 if core else 10.8
    meaning_size = 10.5 if core else 10.2
    meaning_leading = 14.4 if core else 13.7
    head = escape(e['headword'])
    pos = escape(e['pos'])
    pieces = [
        (head, 'ENB', head_size, 14.0 if core else 13.1, False, FOREST),
        (escape(e['meaning_zh']), 'CN', meaning_size, meaning_leading, True, INK),
    ]
    if core:
        pieces.append((escape(e['context_phrase']), 'ENI', 9.5, 12.1,
                       False, MUTED))
    # Positions are displayed separately so grammar labels never squeeze the headword.
    raw = []
    total = 0
    for content, font, size, leading, cjk, color in pieces:
        p = Paragraph(content, style(font, size, leading, color, cjk))
        ph = p.wrap(width, H)[1]
        raw.append((content, font, size, leading, cjk, color, ph))
        total += ph
    return raw, total + (7.8 if core else 4.2)


def vocab_page(c, core):
    entries = [e for e in VOCAB['entries'] if e['core'] is core]
    title = '核心词汇' if core else '文中词汇与搭配'
    sub = ('先记这22项。连着下方的原文短语一起回想。' if core else
           '补齐另外34项。这里保留每个表达在本文中的意思。')
    top = page(c, 'core' if core else 'more', '03 / LEARN', title, sub)
    gutter = 24
    col_w = (CW - gutter) / 2
    # Preserve reading order; choose the most balanced sequential two-column split.
    hs = [entry_parts(e, col_w, core)[1] for e in entries]
    candidates = [(max(sum(hs[:n]), sum(hs[n:])), n)
                  for n in range(1, len(entries))]
    tallest, cut = min(candidates)
    if tallest > top - 49:
        raise RuntimeError(f'{title} overflow: {tallest:.1f} > {top - 49:.1f}')
    rule(c, M + col_w + gutter / 2, top + 3, 0)  # no decorative column wall
    for ci, es in enumerate((entries[:cut], entries[cut:])):
        x = M + ci * (col_w + gutter)
        y = top
        for e in es:
            parts, block_h = entry_parts(e, col_w, core)
            head_width = pdfmetrics.stringWidth(e['headword'], 'ENB', 11.5 if core else 10.8)
            pos_size = 7.9 if len(e['pos']) < 7 else 7.1
            pos_w = pdfmetrics.stringWidth(e['pos'], 'CN', pos_size)
            if head_width + pos_w + 7 <= col_w:
                c.setFont('CN', pos_size)
                c.setFillColor(MUTED)
                c.drawRightString(x + col_w, y - 10.0, e['pos'])
            else:
                # Only the rare long phrase needs its grammatical label omitted visually;
                # the contextual Chinese meaning still establishes its use.
                pass
            start = y
            for content, font, size, leading, cjk, color, ph in parts:
                y = para(c, content, x, y, col_w, font, size,
                         leading, color, cjk)
            y = start - block_h
            rule(c, x, y + 4, col_w, LINE, .4)
    finish(c)


QUESTIONS = [
    ('The ______ had a kernel of truth.', 'rationale'),
    ('His Polaroid self-portrait came out devoid of its subject, '
     'a result he took as ______.', 'conclusive'),
    ('The unskilled, the authors argued, bear a dual burden, '
     'since ______ calls for the same skills as execution.', 'appraisal'),
    ('Studies designed to avoid it still find a smaller but ______ effect.', 'tangible'),
]


def recall(c):
    top = page(c, 'recall', '04 / RECALL', '回想与回顾',
               '先遮住下方答案，再把四个词放回原文。')
    for i, (q, answer) in enumerate(QUESTIONS, 1):
        text(c, f'{i:02d}', M, top - 12, 'SANSB', 9, FOREST)
        top = para(c, escape(q), M + 24, top, CW - 24,
                   'EN', 11.6, 17.3, INK, False) - 10
    top -= 7
    rule(c, M, top, CW)
    top -= 26
    text(c, '文章主线', M, top, 'CNB', 13.5, FOREST)
    top -= 17
    for label, content in SUMMARY:
        c.setFillColor(YELLOW)
        c.circle(M + 2.8, top - 7.8, 2.3, stroke=0, fill=1)
        rich = f'<font name="CNB" color="#284E43">{escape(label)}</font>  {escape(content)}'
        top = para(c, rich, M + 13, top, CW - 13,
                   'CN', 10.5, 15.7) - 7
    answers = '1  rationale    2  conclusive    3  appraisal    4  tangible'
    answer_top = min(top - 13, 100)
    if answer_top < 74:
        raise RuntimeError('Recall answers do not fit')
    rule(c, M, answer_top + 9, CW)
    text(c, '参考答案', M, answer_top - 4, 'CN', 8.5, MUTED)
    para(c, escape(answers), M + 52, answer_top + 6, CW - 52,
         'EN', 9.4, 12.8, MUTED, False)
    finish(c)


def audit_inputs():
    grouped = {}
    highlighted = []
    for s in SOURCE['sentences']:
        raw = ' '.join(x['en'] for x in s['chunks'])
        grouped.setdefault(s['para'], []).append(raw.replace('**', ''))
        highlighted.extend(re.findall(r'\*\*(.+?)\*\*', raw))
    original = [' '.join(v) for v in grouped.values()]
    assert TEXT['english_paragraphs'] == original, 'English source changed'
    assert len(TEXT['chinese_paragraphs']) == len(original) == 7
    es = VOCAB['entries']
    assert len(es) == len(highlighted) == 56
    assert [e['source_term'] for e in es] == highlighted
    assert sum(bool(e['core']) for e in es) == 22
    assert all(e['form_in_text'] == e['source_term'] for e in es)
    source_text = ' '.join(original)
    assert all(e['context_phrase'] in source_text for e in es if e['core'])
    assert all(a in source_text for q, a in QUESTIONS)
    for q, a in QUESTIONS:
        assert q.replace('______', a) in source_text
    assert not any('**' in t for t in original)


def main():
    audit_inputs()
    path = OUT / '01-柠檬汁劫匪-插图阅读小册.pdf'
    c = canvas.Canvas(str(path), pagesize=(W, H), pageCompression=1)
    c.setTitle('第01篇 以为柠檬汁能隐身的劫匪 插图阅读小册')
    c.setAuthor('英文阅读小册')
    c.setSubject('纯净英文 中文译文 56项词汇 回想练习')
    cover(c)
    english(c)
    chinese(c)
    vocab_page(c, True)
    vocab_page(c, False)
    recall(c)
    c.save()
    (OUT / '01-layout-audit.json').write_text(json.dumps({
        'pages': 6, 'page_size_mm': [176, 250], 'source_article': '01',
        'english_paragraphs': 7, 'chinese_paragraphs': 7,
        'vocabulary_items': 56, 'core_items': 22,
        'all_english_text_unchanged_except_bold_removal': True,
        'illustration_sha256': hashlib.sha256(ILLUSTRATION.read_bytes()).hexdigest(),
        'pdf_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'placed_elements': LAYOUT,
    }, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'pdf': str(path), 'bytes': path.stat().st_size,
                      'pages': 6, 'position_checks': len(LAYOUT)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
