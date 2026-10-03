#!/bin/bash
# Reproduce: undo done in v18.4 is not remembered by v18.5's one-click (ws "w"), control: same undo done in v18.5 (ws "w2").
S=$(cd "$(dirname "$0")" && pwd); cd "$S"; OLD=$S/v184; NEW=/home/user/literate-enigma; PY=/tmp/gsv39/bin/python
[ -d v184 ] || { mkdir -p v184; git -C $NEW archive d2483ac voicetwin tests | tar -x -C v184; }
F() { grep -v "^[0-9][0-9]:[0-9][0-9]:[0-9][0-9] |"; }
rm -rf run && mkdir -p run/w run/w2
$PY step.py $OLD run/w/ws build 2>&1 | F | tail -1
$PY step.py $OLD run/w/ws undo_saved 0 2>&1 | F          # v18.4: adopt, save, red-button undo, save
$PY step.py $NEW run/w/ws show 0 2>&1 | F
$PY step.py $NEW run/w/ws oneclick 2>&1 | F             # v18.5 one-click
echo "=== control: same row undone with v18.5 code"
$PY step.py $OLD run/w2/ws build 2>&1 | F | tail -1
$PY step.py $NEW run/w2/ws undo_saved 0 2>&1 | F
$PY step.py $NEW run/w2/ws oneclick 2>&1 | F
rm -rf run v184
