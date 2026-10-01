#!/bin/bash
# Run selected tests for the U3 worktree inside the gradio-4.24 / py3.9 venv (no deselect).
cd <仓库>/.claude/worktrees/wf_08725f86-d54-8 || exit 1
export PYTHONPATH=<仓库>/.claude/worktrees/wf_08725f86-d54-8
exec <草稿目录>/gsv39/bin/python -m pytest -q -p no:cacheprovider "$@"
