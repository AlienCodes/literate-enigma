import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import gradio.blocks as gb  # noqa: E402

_orig = gb.Blocks.handle_streaming_diffs


def traced(self, fn_index, data, session_hash, run, final, simple_format=False):
    pend = self.pending_diff_streams.get(session_hash, {}) if session_hash else {}
    first = run not in pend
    name = getattr(self.fns[fn_index].fn, "__name__", "?") if hasattr(self, "fns") else "?"
    print(f"DIFF fn={fn_index}:{name} run={run} first={first} final={final} pending={list(pend)}", file=sys.stderr, flush=True)
    return _orig(self, fn_index, data, session_hash=session_hash, run=run, final=final, simple_format=simple_format)


gb.Blocks.handle_streaming_diffs = traced
from voicetwin.config import load_config  # noqa: E402
from voicetwin.webui.launcher import launch  # noqa: E402

launch(load_config(), host="127.0.0.1", port=7877)
