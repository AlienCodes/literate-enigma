#!/bin/bash
# Rebuild an old-version workspace (old code from git archive in v18x/), then run each repro with the CURRENT code.
# usage: ./repro_all.sh   (needs /tmp/gsv39/bin/python; deletes its temp workspaces at the end)
set -e
S=/tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/sweep/upgrade
cd $S
for v in 153ca72:v182 aec67a5:v183 d2483ac:v184; do d=${v##*:}; [ -d $d ] || { mkdir -p $d; git -C /home/user/literate-enigma archive ${v%%:*} voicetwin tests | tar -x -C $d; }; done
rm -rf ws && mkdir -p ws/v184_clean
/tmp/gsv39/bin/python build_old.py $S/v184 $S/ws/v184_clean/ws clean > /dev/null 2>&1
run() { rm -rf run/$1 && mkdir -p run/$1 && cp -r ws/v184_clean/ws run/$1/ws && ln -sfn $S/ws/v184_clean/lectures run/$1/lectures
        echo "=== $2"; /tmp/gsv39/bin/python $2 run/$1/ws 2>&1 | grep -v "^[0-9][0-9]:[0-9][0-9]:[0-9][0-9] |"; }
run pend repro_pending.py
run grey repro_grey.py
run nopy repro_nopinyin.py; /tmp/gsv39/bin/python after_reinstall.py run/nopy/ws 2>&1 | grep -v "^[0-9][0-9]:[0-9][0-9]:[0-9][0-9] |"
run rst repro_restore.py
run dl repro_dltext.py
run ur repro_undo_replace.py
rm -rf run/rev && mkdir -p run/rev && cp -r ws/v184_clean/ws run/rev/ws
echo "=== old undo not remembered"; /tmp/gsv39/bin/python old_rev.py $S/v184 run/rev/ws 2>&1 | grep -v "^[0-9][0-9]:" ; /tmp/gsv39/bin/python new_rev.py run/rev/ws 2>&1 | grep -v "^[0-9][0-9]:"
echo "=== full upgrade walk (all versions): check_new.py"; 
rm -rf ws run
