"""Metric-based Chinese wrapping with punctuation and Latin-token protection."""
from html import escape
from html.parser import HTMLParser
import re
from functools import lru_cache
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph as NativeParagraph

NO_START=set('，。、；：？！）】》〉」』〕］｝”’%,;:!?')
NO_END=set('（【《〈「『〔［｛“‘(')
ATOM=re.compile(r'(?:第)?\d+(?:[.,]\d+)*(?:(?:万|亿|千|百)?(?:百分位|公里|毫米|厘米|微米|公顷|英里|分钟|小时|千克|公斤|美元|英镑|年|月|日|岁|人|次|倍|个|份|种|项|克|米|秒|升|伏|局|手|封|道|笔)|[%％℃])?|[A-Za-z][A-Za-z0-9’\'._/-]*|……|——|\s+')

class Runs(HTMLParser):
    def __init__(self,style):
        super().__init__(convert_charrefs=True)
        self.base=(style.fontName,float(style.fontSize),None)
        self.stack=[self.base];self.chars=[]
    def handle_starttag(self,tag,attrs):
        if tag=='font':
            a=dict(attrs);f,s,c=self.stack[-1]
            self.stack.append((a.get('name',f),float(a.get('size',s)),a.get('color',c)))
        elif tag=='br':self.chars.append(None)
    def handle_startendtag(self,tag,attrs):
        if tag=='br':self.chars.append(None)
    def handle_endtag(self,tag):
        if tag=='font' and len(self.stack)>1:self.stack.pop()
    def handle_data(self,data):self.chars.extend((ch,self.stack[-1]) for ch in data)

@lru_cache(maxsize=60000)
def char_width(ch,font,size):return pdfmetrics.stringWidth(ch,font,size)

def token_width(token):return sum(char_width(ch,*st[:2]) for ch,st in token)
def whitespace(token):return all(ch.isspace() for ch,_ in token)
def first(token):return token[0][0]
def last(token):return token[-1][0]

def tokens(chars):
    out=[];segment=[]
    def emit(seg):
        text=''.join(ch for ch,_ in seg);i=0
        while i<len(seg):
            m=ATOM.match(text,i);end=m.end() if m else i+1
            out.append(seg[i:end]);i=end
    for ch in chars:
        if ch is None:emit(segment);segment=[];out.append(None)
        else:segment.append(ch)
    emit(segment);return out

def format_lines(text,style,width):
    parser=Runs(style);parser.feed(text)
    lines=[];line=[];used=0;limit=width-1.2
    def push(items):
        items=items[:]
        while items and whitespace(items[-1]):items.pop()
        while items and whitespace(items[0]):items.pop(0)
        lines.append([ch for token in items for ch in token])
    for token in tokens(parser.chars):
        if token is None:push(line);line=[];used=0;continue
        if not line and whitespace(token):continue
        tw=token_width(token)
        if line and used+tw>limit:
            carry=[]
            while line and whitespace(line[-1]):line.pop()
            # A sequence such as a Latin word + closing quote + full stop
            # needs one stable break, not separate one-character adjustments.
            # Pull back until the remaining line may end and its successor
            # may start. This also carries an exposed opening quote forward.
            while line and (last(line[-1]) in NO_END or
                            first(carry[0] if carry else token) in NO_START):
                carry.insert(0,line.pop())
            while line and whitespace(line[-1]):line.pop()
            if not line:
                raise ValueError('Protected CJK token exceeds line width')
            push(line);line=carry;used=sum(token_width(t) for t in carry)
            if whitespace(token):continue
        if used+tw>limit+.1:
            raise ValueError('Unbreakable token too wide: '+''.join(ch for ch,_ in token))
        line.append(token);used+=tw
    if line:push(line)
    def serialize(chars):
        groups=[]
        for ch,st in chars:
            if groups and groups[-1][0]==st:groups[-1][1].append(ch)
            else:groups.append([st,[ch]])
        output=[]
        for st,cs in groups:
            s=escape(''.join(cs))
            if st==parser.base:output.append(s)
            else:
                attrs=f'name="{escape(st[0],quote=True)}" size="{st[1]}"'
                if st[2]:attrs+=' color="'+escape(st[2],quote=True)+'"'
                output.append('<font '+attrs+'>'+s+'</font>')
        return ''.join(output)
    return '<br/>'.join(serialize(line) for line in lines)

class SafeParagraph:
    def __init__(self,text,style,*args,**kwargs):
        self.text=text;self.style=style;self.args=args;self.kwargs=kwargs;self.inner=None
    def wrap(self,width,height):
        text=self.text;style=self.style
        if style.wordWrap=='CJK':
            text=format_lines(text,style,width)
            style=style.clone('safeChinese',wordWrap=None,splitLongWords=False)
        self.inner=NativeParagraph(text,style,*self.args,**self.kwargs)
        return self.inner.wrap(width,height)
    def drawOn(self,*args,**kwargs):return self.inner.drawOn(*args,**kwargs)
