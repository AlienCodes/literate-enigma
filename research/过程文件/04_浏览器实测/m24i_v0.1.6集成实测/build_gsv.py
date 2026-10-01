import sys

sys.path.insert(0, "<仓库>/.claude/worktrees/wf_08725f86-d54-11/tests")
from fake_gptsovits import build_fake_root  # noqa: E402

print(build_fake_root(sys.argv[1]))
