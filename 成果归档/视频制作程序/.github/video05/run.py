#!/usr/bin/env python3
"""Run the established 05 pipeline; always retain useful diagnostics and machine state."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import traceback

ROOT = Path.cwd()
spec = importlib.util.spec_from_file_location('production', ROOT / '.github/video-completion/run.py')
production = importlib.util.module_from_spec(spec)
spec.loader.exec_module(production)
production.OUT.mkdir(exist_ok=True)
machine = Path(os.environ['RUNNER_TEMP']) / 'completion-machine'
diagnostics = ROOT / 'diagnostics05'
diagnostics.mkdir(exist_ok=True)
failed = None
try:
    production.create_five()
except Exception as exc:
    failed = exc
    traceback.print_exc()
finally:
    work = machine / 'video'
    for directory in ['做_05', 'work_05', 'scripts']:
        source = work / directory
        if source.exists():
            for p in source.rglob('*'):
                if p.is_file() and p.suffix in ('.wav', '.json', '.txt', '.log', '.csv'):
                    if directory == 'scripts' and p.name != '05.json':
                        continue
                    target = diagnostics / directory / p.relative_to(source)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, target)
    if work.exists():
        for p in work.iterdir():
            if p.is_file() and ('05' in p.name or 'dossier' in p.name) and p.suffix in ('.json', '.txt', '.log'):
                shutil.copy2(p, diagnostics / p.name)
    if failed:
        (diagnostics / 'failure.txt').write_text(repr(failed) + '\n')
if failed:
    sys.exit(1)
