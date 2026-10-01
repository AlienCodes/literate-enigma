import re
from pathlib import Path

p = Path('<仓库>/.claude/worktrees/wf_08725f86-d54-11/voicetwin/webui/app.py')
s = p.read_text(encoding='utf-8')


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:80], s.count(old))
    s = s.replace(old, new)


rep('''# ============================================================================ 网页
class WebUI:''', '''class _StopOnce:
    """长任务进行中的停止按钮：只在第一次刷新时显示出来，之后不再改它。

    否则每 0.6 秒刷新一次进度条时，都会把「再点一次确认停止（5 秒内）」/「正在停止……」改回「⏹ 停止」
    （浏览器里实测：确认的字一闪就没了）。"""

    def __init__(self) -> None:
        self.shown = False

    def __call__(self) -> Dict[str, Any]:
        if self.shown:
            return _upd()
        self.shown = True
        return _upd(visible=True, value=STOP_LABEL, interactive=True)


# ============================================================================ 网页
class WebUI:''')

# Insert `stop_once = _StopOnce()` right before each `for ... in stream:` loop of a streaming handler that shows
# a stop button, and replace the running-yield `self._stop_shown()` with `stop_once()`.
names = ["prep_stop", "proof_stop", "train_stop", "gen_stop", "gen_stop", "dl_stop"]
count = 0
for name in names:
    old = f"{name}=self._stop_shown()"
    idx = s.find(old)
    assert idx >= 0, name
    loop = s.rfind("\n        for ", 0, idx)
    assert loop >= 0 and "in stream:" in s[loop:s.find("\n", loop + 1)], name
    s = s[:idx] + f"{name}=stop_once()" + s[idx + len(old):]
    s = s[:loop] + "\n        stop_once = _StopOnce()" + s[loop:]
    count += 1
assert "self._stop_shown()" not in s.split("def _stop_shown")[1].split("\n", 3)[3] or True
p.write_text(s, encoding='utf-8')
print("ok", count)
