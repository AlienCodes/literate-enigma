"""Resolve immutable request bytes from current deltas or unchanged baseline."""
from pathlib import Path
import delivery as D

AUDIT=Path('/workspace/work/video-audit70-20261113')
ROOTS=[AUDIT/'payload',*[AUDIT/f'preflight-frozen66-v2-part{i}/mirror'for i in(1,2,3)],Path('/workspace/work/audit-repo')]

def immutable_request_inputs(native,extra_roots=()):
    n=native['article'];expected=native['request_source_sha256']
    md=[key for key in expected if key.startswith('新版定稿/')and key.endswith('.md')]
    D.require(len(md)==1,'Actual producer request must identify one original manuscript')
    names={'json':f'视频/脚本/{n}.json','gen':f'视频/工具/初稿生成/gen{n}.py','md':md[0]};resolved={}
    for kind,rel in names.items():
        found=next((root/rel for root in [*map(Path,extra_roots),*ROOTS]if (root/rel).is_file()and D.digest(root/rel)==expected[rel]),None)
        D.require(found is not None,'Attach immutable producer request bytes matching recorded SHA: '+rel)
        resolved[kind]=found
    return resolved
