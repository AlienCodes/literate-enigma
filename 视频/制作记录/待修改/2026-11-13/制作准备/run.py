#!/usr/bin/env python3
"""Run the previously verified official article05 pipeline with four data edits."""
from pathlib import Path
import sys

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
import patch

original = Path(".github/video05fix-production/run.py")
source = original.read_text()
needle = '    current.write_text(json.dumps(d,ensure_ascii=False,indent=1)+"\\n")\n    run(["bash",T/"新管/做.sh","05","--不推"],log="canonical-draft.log")'
assert source.count(needle) == 1
source = source.replace(needle, '    patch.apply(d, ROOT, W, OUT, status)\n' + needle)
needle = '    save();print(json.dumps(status,ensure_ascii=False),flush=True)\nexcept Exception as exc:'
assert source.count(needle) == 1
source = source.replace(needle, '    patch.export(ROOT, W, OUT, status)\n' + needle)
exec(compile(source, str(original), "exec"), {"__name__": "__main__", "__file__": str(original.resolve()), "patch": patch})

