"""Merge public revision evidence and the user's latest production authorization."""
import json
import shutil
from pathlib import Path

OUT = Path(__file__).resolve().parent
PAY = OUT / 'payload'
REPORT = PAY / '视频/制作记录/旧简述清理-2026-11-13'
RECORD = PAY / '视频/制作记录/待修改/2026-11-13/修改状态.json'
status = json.loads(RECORD.read_text())
scope = [f'{n:02d}' for n in range(1, 71)]
status.update({
    'status': 'SOURCE_REVISIONS_UNDER_VERIFICATION_4K_FINALIZATION_AUTHORIZED',
    'render_allowed': True,
    'pdf_build_allowed': True,
    'render_scope': scope,
    'latest_authorization': {
        'date': '2026-11-13',
        'quote': '所有的这些东西改完之后，我们要重新生成视频定稿的呀。',
        'github_quote': '尤其是我们这个视频的改正，最终的定稿都要在GitHub上面，这个重新生成，重新保存。',
        'scope': '全部70篇视频3840×2160重制，并按最新顺序排列；同步全部文字修订重建PDF，正式核验后定稿并归档主仓库、备份专用分支和新Release。',
        'supersedes': 'Earlier pauses in this same conversation; historical quotes remain below.'
    },
    'delivery': '本批源稿和公开核验记录正在归档。旧MP4及旧Release保持原样；新MP4只有完成正式重建、音画核验与远程归档后才标记为交付。',
    'latest_pdf_authorization': {
        'date': '2026-11-13',
        'quote': '修正完之后呢……重新弄一下我们这个PDF……视频一定要按照顺序，按照这个最新的顺序重新生成之后排列都是4k的……Pdfpdf一定要生成一个完美的版本。',
        'quote_kind': '本会话最新口述节选，省略重复语气词；完整原话保留在会话中。',
        'supersedes': '先前等待PDF排版意见的暂停；本轮用户现已明确要求重建PDF。',
        'scope': '同步本轮所有文本修正、已批准B5插图版式、最新篇目顺序和默认隐藏的朋克英语来源图层；新PDF实际验收与归档另记。',
        'pdfs_rebuilt_or_delivered_yet': False,
    },
})
for key in ['regression_to_mean_note', 'smaller_but_tangible_effect_note',
            'in_fairness_empirically_liberty_note', 'final_camera_note']:
    status[key]['status'] = 'APPROVED_SOURCE_SAVED_4K_REBUILD_AUTHORIZED'
status['article05']['article01_footnote'] = 'User-approved notes are saved; all affected videos are authorized for 4K finalization.'
status['article01_final_video_request'].update({
    'status': '4K_FINALIZATION_AND_GITHUB_ARCHIVAL_AUTHORIZED',
    'latest_instruction': status['latest_authorization']['quote'],
})
status['article22']['production'] = '4K regeneration and finalization authorized; source and final-video status recorded separately.'
status['article03'] = {
    'original_number': '03', 'playback_number': '04',
    'focus': {'organism': '微生物', 'germ': '病菌', 'cultured': '培养', 'Ulcers': '溃疡'},
    'culture_part_of_speech': 'v. 培养微生物',
    'production': 'SOURCE_FIXED_4K_REBUILD_AUTHORIZED',
}
status['article06'] = {
    'original_number': '06', 'playback_number': '07',
    'focus': {'hoof': '蹄子', 'guard against': '防范', 'reasoned': '推理'},
    'reason_part_of_speech': 'v. 推理',
    'note': '提问者在正确次数时不自觉改变姿势，汉斯察觉后停止；提问者自己也不知道在提示，并非故意骗人。',
    'production': 'SOURCE_FIXED_4K_REBUILD_AND_FINALIZATION_EXPLICITLY_AUTHORIZED',
}
status['article10_audio'] = {
    'original_number': '10', 'playback_number': '06',
    'scope': '完整音轨实测，重点修复最后一句If so偏小',
    'candidate_metadata_changes': {'S17_prefix_gain_dB': [-5.5, -3.5], 'S17_sentence_gain_dB': [0, 1]},
    'status': 'CANDIDATE_SOURCE_SAVED; ACTUAL_REBUILT_AUDIO_VERIFICATION_PENDING',
    'timing_pitch_and_other_sentences': 'preserved',
}
status['article51'] = {
    'original_number': '51', 'playback_number': '08',
    'focus': {'stood for': '代表', 'pedigree': '来历'}, 'lemma': 'stand for / pedigree',
    'approved_note': '（这里的“他”指时任总统范布伦。1840年总统大选，哈里森拿到234张选举人票，范布伦只有60张。哈里森因此获胜，范布伦没能连任。）',
    'audio_scope': '核查完整音轨，重点为开头OK和中间O.W. for oll wright突然偏小。',
    'audio_status': 'ACTUAL_ACCEPTED_MP4_AUDITED; CANDIDATE_GAIN_SOURCE_SAVED; REBUILT_AUDIO_VERIFICATION_PENDING',
    'production': '4K_REBUILD_AND_GITHUB_ARCHIVAL_AUTHORIZED',
}
status['article11_program'] = {'focus': 'program', 'chinese': '程序', 'sentence': 2, 'chunk': 2, 'status': 'SOURCE_FIXED_4K_REBUILD_AUTHORIZED'}
status['layout_audit'] = {'scope': '全部70篇所有正文页及独立简述页', 'status': 'SOURCE_STATIC_4K_AND_1080_VERIFICATION_IN_PROGRESS_ACTUAL_NEW_VIDEO_ACCEPTANCE_PENDING', 'user_quote': '最后这个字体一定要认认真真的去根据屏幕进行适当的放大，然后好好排版，一定要就是居中排版，弄得特别好看。', 'rebuild_all_70_required': True, 'reason': '旧视频删除内嵌解说后既有字号和y位置未重新计算；48篇旧末屏明显上偏，即使字号正常也需重渲。'}
status['summary_content_review'] = {'scope': '全部70篇', 'status': 'ALL_70_READ_AND_INDEPENDENTLY_REVIEWED_LATEST_USER_PRIORITY_DELTAS_BEING_MERGED', 'user_quote': '你看还有哪些简述说不明白的统一改。要把话说明白，并且还可以结合我之前给的那些小字。', 'new_summary_videos_delivered': False, 'approved_text_file': 'summary-approved-70.json'}
status['latest_streamed_requests'] = {
    '02': {'title': '棉花糖的真相', 'focus': {'Stanford': '斯坦福大学', 'Psychology': '心理学', 'college-entrance exam': '高考'}, 'priority_summary': '实验做法、早期发现与后续研究的限制都要通俗清楚', 'explicit_4K_finalization': True},
    '20': {'title': '冰里的五千年凶案', 'focus': {'artery': '动脉', 'joints': '关节'}, 'line_break': 'who lived about 5,300 years ago,整行；between另起下一行', 'old_recap_removed': True, 'priority_summary': '详细、直白地讲清古尸、死因及未知凶手；末屏重新居中放大'},
    '44': {'focus': {'Norway': '挪威', 'Finland': '芬兰', 'border crossings': '过境'}, 'audio_status': 'accepted track measured; minimal S4C1 -1dB candidate pending actual rebuilt audio acceptance'},
    '50': {'focus': {'popularised as': '被大众传作'}, 'priority_summary': '检出不等于致病；关联不等于因果；一勺是有争议的估算，人体危害仍待更可靠证据'},
}
RECORD.write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')

for name in ['article03-focus-report.json', 'article03-focus-report-root.json',
             'article06-focus-report.json', 'article10-gain-edit-report.json',
             'article51-focus-report.json', 'article51-audio-edit-report.json',
             'article11-program-report.json', 'metadata-report.json',
             'normalized-generators-report.json', '12-gate-data-validation.json',
             'layout-visual70.json']:
    source = OUT / name
    if source.exists():
        shutil.copyfile(source, REPORT / '核查记录' / name)
for no in ['10', '51']:
    audio = OUT / ('audio' + no)
    destination = REPORT / '音轨核查' / no
    destination.mkdir(parents=True, exist_ok=True)
    allow = ['audio'+no+'-diagnostics.json', 'audio'+no+'-repair-proposal.json',
             'source'+no+'-minimal-gain-proposal-overlay.json',
             'source'+no+'-audio-overlay.json', 'source'+no+'-gen-audio-metadata-overlay.json',
             'second-by-second-loudness.csv', 'second-by-second-loudness.json',
             'whole-track-loudness.png', 'final-sentence-rms-and-f0.png']
    for name in allow:
        if (audio / name).exists():
            shutil.copyfile(audio / name, destination / name)

# Public source/data-review evidence only. Never sweep the workspace: private
# speech/model caches and intermediate raw PCM are deliberately excluded.
public_reports = ['summary-approved-70.json', 'summary-root-adjustments.json',
                  'root-layout-data-deltas.json', 'render-scope-current.json',
                  'article44-audio-edit-report.json', 'article44-translation-focus-report.json',
                  'article50-focus-report.json', 'summary-revision-50-priority.json',
                  'preflight-authorized-data-fixes-03-04-48.json',
                  'preflight-authorized-text-data-fixes.json',
                  'preflight-stale-summary-anchors.json',
                  'preflight-t25-minimal-data-proposals.json',
                  'confirmation-tail-review-21-48.json',
                  'confirmation-tail-review-49-70.json',
                  'article65-factual-clarification.json']
public_reports += [f'summary-{prefix}-{group}.json'
                   for prefix in ['revisions','crossreview']
                   for group in ['01-24','25-48','49-70']]
for name in public_reports:
    source=OUT/name
    if source.is_file():
        shutil.copyfile(source, REPORT/'核查记录'/name)

readme = REPORT / 'README.md'
text = readme.read_text()
text = text.replace('收到用户重新开始的指示后，才按正式做.sh与定稿.sh输出4K，并检查音频与末页独立简述。',
                    '用户已明确恢复并要求全部受影响篇目重出4K定稿。正式做.sh与定稿.sh的实际运行、音轨与末页核验和新MP4归档另记；当前截图不能代表已完成重建。')
if '本轮其余修订' not in text:
    text += '\n本轮其余修订：原03补微生物、病菌、培养和溃疡；原06补hoof、guard against、reasoned并加入无意提示解释；原51补stood for、选举解释，并按用户报告实测完整音轨。原10与原51的音量修复需在正式重建后重新测量，源稿参数不能代替新音频验收。\n'
readme.write_text(text)
print(json.dumps({'source_revision_scope': scope, 'render_authorized': True,
                  'final_videos_delivered': False, 'pdf_build_authorized': True}, ensure_ascii=False))
