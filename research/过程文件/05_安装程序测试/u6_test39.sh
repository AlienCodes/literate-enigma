#!/bin/bash
# Run the test suite in the gradio-4.24 / py3.9 venv against the U6 worktree.
WT=<仓库>/.claude/worktrees/wf_08725f86-d54-6
cd "$WT" || exit 1
export PYTHONPATH="$WT"
exec timeout 900 <草稿目录>/gsv39/bin/python -m pytest -q -p no:cacheprovider tests --deselect tests/test_gptsovits_fake.py::test_train_select_and_narrate "$@"
