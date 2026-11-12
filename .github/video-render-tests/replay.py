#!/usr/bin/env python3
"""Replay an independently rendered old end page two frames early, then inspect pilot frames."""
import base64
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
from PIL import Image

ROOT=Path.cwd()
spec=importlib.util.spec_from_file_location('production',ROOT/'.github/video-batch/run.py')
r=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def replay():
    r.materialize(['视频/工具/render.py','视频/工具/make_video.py','视频/工具/fonts'])
    r.materialize=lambda paths: None
    real_voice_end=r.voice_end
    def early_voice_end(path,video_seconds):
        end,checks=real_voice_end(path,video_seconds)
        return end-2/30,checks
    # This is an isolated, explicitly artificial timing fixture. Its audio is
    # the real approved03 recording, and no fixture is saved as a deliverable.
    r.OUT=ROOT/'pilot-fixture-early'
    r.OUT.mkdir(exist_ok=True)
    r.voice_end=early_voice_end
    r.end_card('03')
    fixture_report=json.loads((r.OUT/'03-verification.json').read_text())
    fixture_video=next(r.OUT.glob('*.mp4'))
    env={**os.environ,'GIT_AUTHOR_NAME':'Timing replay','GIT_AUTHOR_EMAIL':'timing-replay@example.invalid',
         'GIT_COMMITTER_NAME':'Timing replay','GIT_COMMITTER_EMAIL':'timing-replay@example.invalid'}
    video_blob=r.get(['git','hash-object','-w',fixture_video]).strip()
    script_blob=r.get(['git','hash-object','-w',r.OUT/'03-script.json']).strip()
    def tree(entries):
        payload=''.join(f'{mode} {kind} {sha}\t{name}\0' for mode,kind,sha,name in entries)
        return r.command(['git','mktree','-z'],input=payload,capture_output=True,text=True).stdout.strip()
    videos=tree([('100644','blob',video_blob,Path(fixture_report['source']).name)])
    scripts=tree([('100644','blob',script_blob,'03.json')])
    video=tree([('040000','tree',scripts,'脚本')])
    root=tree([('040000','tree',videos,'最终版4K视频'),('040000','tree',video,'视频')])
    commit=r.command(['git','commit-tree',root,'-m','Temporary old-independent-page fixture'],
                     env=env,capture_output=True,text=True).stdout.strip()
    r.BASE=commit
    r.OUT=ROOT/'completion-output/independent-early-replay'
    r.OUT.mkdir(parents=True,exist_ok=True)
    r.voice_end=real_voice_end
    r.end_card('03')
    report=json.loads((r.OUT/'03-verification.json').read_text())
    assert report['old_summary_handling']['kind']=='standalone'
    assert report['held_final_body_frames']==2,report
    assert report['end_page_frames']==60 and report['end_page_seconds']==2
    assert report['original_audio_identical'] and report['original_audio_packet_timings_identical']
    (r.OUT/'replay-result.json').write_text(json.dumps({
        'scenario':'A real03 recording with a fixture old summary beginning two frames before the voice ends.',
        'result':'passed','held_final_body_frames':report['held_final_body_frames'],
        'old_summary_handling':report['old_summary_handling'],
        'old_summary_pixel_verification':report['old_summary_pixel_verification'],
        'new_summary_start_seconds':report['summary_start_seconds'],
        'summary_seconds':report['end_page_seconds'],'original_audio_identical':True,
    },ensure_ascii=False,indent=2)+'\n')
    print('INDEPENDENT_EARLY_CARD_REPLAY_PASSED',flush=True)


def prepare_review():
    dest=ROOT/'pilot-review'
    dest.mkdir(exist_ok=True)
    for no in ['03','23','54','65']:
        folder=ROOT/'pilot-artifacts'/f'pilot-{no}'
        report=next(folder.rglob(f'{no}-verification.json'))
        shutil.copy2(report,dest/f'{no}-verification.json')
        left=Image.open(next(folder.rglob(f'{no}-转场前.png'))).convert('RGB').resize((960,540),Image.Resampling.LANCZOS)
        right=Image.open(next(folder.rglob(f'{no}-简述首帧.png'))).convert('RGB').resize((960,540),Image.Resampling.LANCZOS)
        collage=Image.new('RGB',(1920,540));collage.paste(left,(0,0));collage.paste(right,(960,0))
        output=io.BytesIO();collage.save(output,format='JPEG',quality=88)
        (dest/f'{no}-before-after.b64').write_text(base64.b64encode(output.getvalue()).decode()+'\n')
    shutil.copy2(ROOT/'completion-output/independent-early-replay/replay-result.json',dest/'independent-early-replay.json')


if __name__=='__main__':
    replay() if sys.argv[1]=='replay' else prepare_review()
