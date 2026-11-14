from pathlib import Path
import sys,json,subprocess
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root));import publish_review as P
files={'.github/first50-review/native_review.py':(root/'native_review.py').read_bytes(),'.github/workflows/publish-first50-review.yml':(root/'publish-first50-review.yml').read_bytes()};result=P.archive_records('native-primary-only-guard',files)
api=P.D.GitHub();repo=P.REPOS[0];parent=api.api(repo,'git/ref/heads/'+P.BRANCH)['object']['sha'];tree=api.api(repo,'git/commits/'+parent)['tree']['sha'];commit=api.api(repo,'git/commits','POST',{'message':'开始实际发布用户审核的40篇新4K视频与完整PDF','tree':tree,'parents':[parent]})['sha'];api.api(repo,'git/refs/heads/'+P.BRANCH,'PATCH',{'sha':commit,'force':False});assert api.api(repo,'git/ref/heads/'+P.BRANCH)['object']['sha']==commit
P.save('NATIVE-LAUNCH.json',{'repository':repo,'branch':P.BRANCH,'commit':commit,'source_guard_archived_both':result,'actual_event':'push from non-skip commit, no fake Actions environment'});print(commit,flush=True)
