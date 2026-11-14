#!/usr/bin/env python3
"""看本会话现在的上下文有多少 token；主会话到 25 万就照 视频/工具/新管/主会话交接.md 交接。
用户 2026-11-04：“当这个对话差不多就是已经它的上下文大到非常消耗token的时候，我们就自动开启新的对话，做成一个完美的交接”。
  python3 视频/工具/新管/上下文.py          # 主会话每次回用户前跑一次（输出一行）
  python3 视频/工具/新管/上下文.py --自检
只提醒，不卡任何东西。读法：本会话记录（~/.claude/projects/*/<CLAUDE_CODE_SESSION_ID>.jsonl）最后一条回复的 输入+缓存写+缓存读，
和 get_session 的 context_usage.used_tokens 一致（2026-11-04 实测 10.75 万 对 10.51 万）。"""
import os, sys, glob, json, tempfile
线 = 250_000


def 用量(path):
    with open(path, 'rb') as f:
        f.seek(0, 2); n = f.tell(); f.seek(max(0, n - 4_000_000)); tail = f.read().decode('utf-8', 'ignore')
    for line in reversed(tail.splitlines()):
        if '"usage"' not in line: continue
        try: d = json.loads(line)
        except Exception: continue
        u = (d.get('message') or {}).get('usage') if d.get('type') == 'assistant' and not d.get('isSidechain') else None
        if u: return u.get('input_tokens', 0) + u.get('cache_creation_input_tokens', 0) + u.get('cache_read_input_tokens', 0)
    return None


def 报(n):
    if n is None: return '读不到本会话的上下文用量（不影响任何事）'
    return f'本会话上下文 {n / 1e4:.1f} 万 token' + ('：已到 25 万，主会话现在就照 视频/工具/新管/主会话交接.md 交接' if n >= 线 else '（主会话到 25 万交接）')


def 自检():
    def 样(*tokens):
        p = tempfile.mktemp(suffix='.jsonl')
        with open(p, 'w') as f:
            for t in tokens: f.write(json.dumps({'type': 'assistant', 'message': {'usage': {'input_tokens': 2, 'cache_creation_input_tokens': 1000, 'cache_read_input_tokens': t}}}) + '\n')
            f.write('{"type":"user","message":{"content":"半行坏记录\n')
        return 报(用量(p))
    坏, 好 = 样(100_000, 259_000), 样(300_000, 99_000)        # 坏：最后一条 26 万 → 要交接；好：压缩后回到 10 万 → 不提醒
    ok = '交接' in 坏 and '现在就' in 坏 and '现在就' not in 好 and '10.0 万' in 好
    print('上下文自检：' + ('通过' if ok else f'✘ 坏样本“{坏}” 好样本“{好}”')); return ok


if __name__ == '__main__':
    if '--自检' in sys.argv: sys.exit(0 if 自检() else 1)
    sid = os.environ.get('CLAUDE_CODE_SESSION_ID', '')
    ps = sorted(glob.glob(os.path.expanduser(f'~/.claude/projects/*/{sid}.jsonl')), key=os.path.getmtime) if sid else []
    print(报(用量(ps[-1]) if ps else None))
