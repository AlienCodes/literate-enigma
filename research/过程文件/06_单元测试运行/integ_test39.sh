#!/bin/bash
# Run the test suite in the gradio 4.24 / python 3.9 venv against the integration worktree.
W=<仓库>/.claude/worktrees/wf_08725f86-d54-11
cd "$W" || exit 1
export PYTHONPATH="$W"
exec <草稿目录>/gsv39/bin/python -m pytest -q -p no:cacheprovider "${@:-tests}" --deselect tests/test_gptsovits_fake.py::test_train_select_and_narrate
