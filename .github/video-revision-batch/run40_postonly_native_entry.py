#!/usr/bin/env python3
# Only a new native job may execute this exact40 post-only completion.
import os,subprocess,sys
from pathlib import Path
B=Path(__file__).resolve().parent;R=Path.cwd()
import hashlib
assert hashlib.sha256((B/'root-source40-exact-honest-new-native-postonly-completion-code-adoption-decision.json').read_bytes()).hexdigest()=='1abbc93a3ad7e9527346cc605a2d4ecacf8ad65855c95c6b58388878cb0879f3'
assert os.environ.get('ARTICLE_NO')=='40'
assert os.environ.get('SOURCE40_ORIGINAL_CAPSULE'), 'Sole CI must attach the actual immutable original failed artifact/capsule.'
subprocess.run([sys.executable,str(B/'resume40_post_only.py'),'complete','--reference',str(B/'resume40-reference.json'),'--capsule',os.environ['SOURCE40_ORIGINAL_CAPSULE'],'--request',str(R/'.github/video-revision-batch/request/40'),'--original-program',str(B/'original_run40_failed_wrapper.py'),'--decision',str(B/'root-source40-specific-exact-G35-summary-wrapper-compatibility-decision.json'),'--repository',str(R),'--work',str(Path(os.environ['RUNNER_TEMP'])/'source40-postonly-completion-machine'),'--output',str(R/'article40-delivery')],check=True)
