"""Archive only explicitly safe public scalar diagnostics, never private audio."""
from pathlib import Path
import json
import shutil
from archive_batch import digest, load, now, write

B=Path(__file__).resolve().parent
W=B/'source62-audio-diagnostic-v2-record-assets-20261114'
P=Path('声音诊断记录/2026-11-14-书34多莉-受控候选尚非正式修复')
H=Path('/workspace/work/dolly62-audio-user-review-20261114')

def main():
    manifest=H/'safe-public-evidence-manifest-v2.json'
    assert digest(manifest)=='0a1bd73a0faf83c3a2d0f0a3aa104f10bcb33178eacbbc7bad7dbd5505c45690'
    bindings=[]
    def add(source,relative,size=None,sha=None):
        source=Path(source);assert source.suffix.lower() in {'.json','.py','.log','.txt','.md'}
        assert size is None or source.stat().st_size==size;actual=digest(source);assert sha is None or actual==sha
        target=W/'payload'/P/relative;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert digest(target)==actual
        else:shutil.copyfile(source,target)
        bindings.append({'original_path':str(source),'repo_path':str(P/relative),'bytes':source.stat().st_size,'sha256':actual})
    add(manifest,Path(manifest.name))
    for row in load(manifest)['files']:
        relative=Path(row['name']);assert not relative.is_absolute() and '..' not in relative.parts
        add(H/relative,relative,row['bytes'],row['sha256'])
    add(B/'PENDING-SOURCE62-PUBLIC-DIAGNOSTIC-v2.json',Path('收到时待正式媒体状态.json'))
    add(Path(__file__),Path('归档程序')/Path(__file__).name)
    meta={'kind':'source62-public-scalar-diagnostic-candidate-history-not-final-media','created_utc':now(),'prefix':str(P),'asset_branch':'codex/source62-audio-diagnostic-v2-records-20261114','articles':[],'private_PCM_GT_audio_cache_or_media_copied':False,'formal_native_repair_or_production_quality_pass_claimed':False,'new_final_accepted_voice_identity_claimed':False,'existing_source62_active_video_index_and_release_unchanged':True,'all_PDF_work_paused':True}
    write(W/'payload'/P/'逐项原件绑定与范围.json',{'files':bindings,**meta});write(W/'prepared-archive.json',meta)
    index=[{'repo_path':str(p.relative_to(W/'payload')),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted((W/'payload').rglob('*')) if p.is_file()]
    write(W/'payload-file-index.json',index);print(json.dumps({'work_dir':str(W),'files':len(index),'bytes':sum(r['bytes'] for r in index),'media_or_quality_acceptance_claimed':False},ensure_ascii=False))

if __name__=='__main__':main()
