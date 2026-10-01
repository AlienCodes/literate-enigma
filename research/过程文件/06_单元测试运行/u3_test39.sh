#!/bin/bash
# Run the test suite for the U3 worktree inside the gradio-4.24 / py3.9 venv.
cd <仓库>/.claude/worktrees/wf_08725f86-d54-8 || exit 1
export PYTHONPATH=<仓库>/.claude/worktrees/wf_08725f86-d54-8
exec <草稿目录>/gsv39/bin/python -m pytest -q -p no:cacheprovider "${@:-tests}" --deselect tests/test_gptsovits_fake.py::test_train_select_and_narrate
