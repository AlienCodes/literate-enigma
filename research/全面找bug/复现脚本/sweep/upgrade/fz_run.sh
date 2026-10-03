#!/bin/bash
cd /tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/sweep/upgrade
for seed in $(seq $1 $2); do for v in v182 v183 v184; do d=fz/${v}_$seed; rm -rf $d; mkdir -p $d
/tmp/gsv39/bin/python fuzz_upgrade.py old /tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/sweep/upgrade/$v $d $seed > $d/old.log 2>&1
/tmp/gsv39/bin/python fuzz_upgrade.py new /home/user/literate-enigma $d $seed 2>/dev/null | grep '^{' >> fz/results_$1.jsonl
rm -rf $d/我的声音 $d/tmp*
done; done
echo done > fz/done_$1
