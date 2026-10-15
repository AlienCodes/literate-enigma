"""token 账本（2026-10-15 用户：“测量……从头到尾一整个环节，在哪个地方消耗的 token 量是最大的……值不值得”）。
读本会话的全部记录（主对话、子代理、工作流），按 API 返回的用量统计，不输出原文（记录里有密钥）。
折算：按价格比例把各类 token 折成“等效 token”：新输入 ×1、写缓存 ×1.25、读缓存 ×0.1、输出 ×5。
用法：python3 token账本.py [会话目录]"""
import json, glob, os, re, sys, collections
D = sys.argv[1] if len(sys.argv) > 1 else glob.glob('/root/.claude/projects/*/*.jsonl')[0][:-6]
W = dict(input_tokens=1, cache_creation_input_tokens=1.25, cache_read_input_tokens=0.1, output_tokens=5)
eq = lambda u: sum(u.get(k, 0) or 0 for k in W for _ in [0]) and sum((u.get(k, 0) or 0) * w for k, w in W.items())
def rows(f):
    seen = set()
    for l in open(f, errors='ignore'):
        try: j = json.loads(l)
        except Exception: continue
        yield j, seen
calls = collections.Counter(); ctx = collections.Counter(); src = collections.Counter(); day = collections.Counter(); tool = collections.Counter(); raw = collections.Counter()
files = [(D + '.jsonl', '主对话')] + [(f, '子代理') for f in glob.glob(D + '/subagents/**/*.jsonl', recursive=True)] + [(f, '工作流') for f in glob.glob(D + '/workflows/**/*.jsonl', recursive=True)]
carry = []          # 主对话里每个工具结果的“拖带”：之后每次调用都要重读它，直到压缩
for f, kind in files:
    seen = set(); pend = {}; nm_ = {}; order = []; main = kind == '主对话'; live = []   # live: [大小, 名字, 次数]
    for l in open(f, errors='ignore'):
        try: j = json.loads(l)
        except Exception: continue
        if main and (j.get('subtype') == 'compact_boundary' or j.get('isCompactSummary')):
            carry += live; live = []
        m = j.get('message') or {}
        if j.get('type') == 'assistant' and isinstance(m, dict) and m.get('usage'):
            for x in live: x[2] += 1
            names = [c.get('name', '?') + ('·' + (c.get('input', {}).get('description') or '')[:24] if c.get('name') == 'Bash' else '') for c in m.get('content', []) if isinstance(c, dict) and c.get('type') == 'tool_use']
            for c in m.get('content', []):
                if isinstance(c, dict) and c.get('type') == 'tool_use': pend[c['id']] = c.get('name', '?') + ('：' + os.path.basename(str(c.get('input', {}).get('file_path', ''))) if c.get('name') == 'Read' else ('·' + (c.get('input', {}).get('description') or '')[:20] if c.get('name') == 'Bash' else ''))
            mid = m.get('id'); nm_.setdefault(mid, []).extend(n.split('·')[0] for n in names)
            if mid in seen: continue
            seen.add(mid); u = m['usage']; e = eq(u); order.append((mid, e, kind))
            calls[kind] += 1; ctx[kind] += sum(u.get(k, 0) or 0 for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens')); src[kind] += e; day[(j.get('timestamp') or '')[:10]] += e
            for k in W: raw[k] += u.get(k, 0) or 0
        if main and j.get('type') == 'user' and isinstance(m.get('content'), list):
            for c in m['content']:
                if isinstance(c, dict) and c.get('type') == 'tool_result':
                    cc = c.get('content'); img = isinstance(cc, list) and any(isinstance(x, dict) and x.get('type') == 'image' for x in cc)
                    n = 4800 if img else (len(json.dumps(cc, ensure_ascii=False)) if not isinstance(cc, str) else len(cc))
                    live.append([n, pend.get(c.get('tool_use_id'), '?'), 0])
    if main: carry += live
    for mid, e, k_ in order: tool[(nm_[mid][0] if nm_.get(mid) else '只回话') + f'（{k_}）'] += e
tot = sum(src.values())
print(f'全部等效 token：{tot/1e6:.1f}M（新输入 {raw["input_tokens"]/1e6:.1f}M、写缓存 {raw["cache_creation_input_tokens"]/1e6:.1f}M、读缓存 {raw["cache_read_input_tokens"]/1e6:.0f}M、输出 {raw["output_tokens"]/1e6:.1f}M）')
print('按来源：', '；'.join(f'{k} {v/tot:.0%}' for k, v in src.most_common()))
print('调用次数与平均每次带的上下文：', '；'.join(f'{k} {calls[k]} 次、平均 {ctx[k]/calls[k]/1000:.0f}k' for k in calls), f'（子代理共 {len(files)-1} 个记录文件）')
print('按日期：', '；'.join(f'{k[5:]} {v/1e6:.1f}M' for k, v in sorted(day.items())))
print('按调用的工具（这一步的花费）：', '；'.join(f'{k} {v/tot:.0%}' for k, v in tool.most_common(8)))
# 拖带成本：结果字符数/3 ≈ token，每次之后的调用按读缓存 0.1 折算
cs = collections.Counter()
for n, name, k in carry: cs[('Read 看图片' if n == 4800 else 'Read 读文件') if name.startswith('Read') else re.sub(r'·.*', '', name)] += n / 3 * k * 0.1
ct = sum(cs.values())
print(f'工具结果留在上下文里被反复重读（拖带）：约 {ct/1e6:.1f}M，占 {ct/tot:.0%}；按工具：', '；'.join(f'{k} {v/ct:.0%}' for k, v in cs.most_common(6)))
big = sorted(carry, key=lambda x: -x[0] / 3 * x[2] * 0.1)[:8]
print('拖带最多的单个结果：', '；'.join(f'{nm[:30]}（{n//1000}k 字×{k} 次）' for n, nm, k in big))
