export const meta = {
  name: 'punk-english-title-judging',
  description: 'Three independent judges score the 5 title-page logo videos; a critic double-checks the top 3',
  phases: [
    { title: 'Judge', detail: '3 judges with different lenses score all 5 versions' },
    { title: 'Check', detail: 'critic re-examines the top 3 for defects and confirms or challenges the ranking' },
  ],
}

const S = '/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad'
const J = S + '/video/judge'
const LG = S + '/video/logo'
const KEYS = ['A_stamp', 'B_neon', 'C_graffiti', 'D_wordmark', 'E_ransom']
const DESC = {
  A_stamp: '玫红色方形印章，"朋克/英语"分两行，斜盖在中文标题黄色标签右边，有磨损墨点（Noto Sans SC Black）',
  B_neon: '粉红霓虹灯管字（站酷庆科黄油体）+ 青色霓虹角框 + 轻微 RGB 错位，居中在中文标题下方',
  C_graffiti: '马善政毛笔涂鸦字，亮粉渐变 + 黄色细描边 + 深色外框投影，油漆滴痕和喷溅点，微斜，下方小字 PUNK ENGLISH，居中在中文标题下方',
  D_wordmark: 'App 图标式：黄→橙渐变圆角方块内深色闪电 + 白色粗方块字"朋克英语"（站酷庆科黄油体）+ 青绿小字 PUNK ENGLISH，居中在中文标题下方',
  E_ransom: '勒索信拼贴：四个字各在不同颜色撕边纸片上（黑底白字、荧光粉、米白纸手写、亮黄），纸胶带，下方黑色打标签机胶条 PUNK ENGLISH，居中在中文标题下方',
}
const files = k => `  - video title frame (1080p, extracted from the actual video): ${J}/${k}_video_title.png
  - phone-size preview (480x270, simulates a phone in landscape / small window): ${J}/${k}_phone.png
  - the next frame after the title (first content screen, to judge continuity): ${J}/${k}_video_next.png
  - same design on two other article titles: ${LG}/${k}/t01.png (longest title, 3 lines) and ${LG}/${k}/t02.png (short title)
  - logo close-up: ${LG}/${k}/logo_crop.png`

const CONTEXT = `Background: a video series for Chinese students preparing for the 考研 English exam (bilingual intensive reading, each video ~2.5 minutes, published on Bilibili/Douyin). The channel brand is 「朋克英语」 ("Punk English"). The user asked for a good-looking, trademark-like 「朋克英语」 mark that appears ONLY on the opening title page, and for article numbers to be removed. Five designers each produced one version; each version has been rendered into a full video of article 03 that is identical except for the title page. Your job: judge the five versions and pick the best three. Open EVERY image listed with the Read tool before scoring.`

const SCORE_SCHEMA = {
  type: 'object',
  properties: {
    scores: { type: 'array', items: { type: 'object', properties: {
      key: { type: 'string' },
      beauty: { type: 'number' }, logo_quality: { type: 'number' }, punk_feel: { type: 'number' }, legibility_phone: { type: 'number' }, hierarchy_and_harmony: { type: 'number' }, consistency_across_titles: { type: 'number' },
      total: { type: 'number', description: 'beauty*0.25+logo_quality*0.2+punk_feel*0.15+legibility_phone*0.15+hierarchy_and_harmony*0.15+consistency_across_titles*0.1; each criterion 1-10' },
      strengths: { type: 'array', items: { type: 'string' } },
      problems: { type: 'array', items: { type: 'string' } },
      comment_zh: { type: 'string', description: 'one or two plain Chinese sentences for the end user' },
    }, required: ['key', 'beauty', 'logo_quality', 'punk_feel', 'legibility_phone', 'hierarchy_and_harmony', 'consistency_across_titles', 'total', 'strengths', 'problems', 'comment_zh'] } },
    top3: { type: 'array', items: { type: 'string' }, description: 'keys of your best three, best first' },
  },
  required: ['scores', 'top3'],
}

const LENSES = [
  { name: 'brand', text: 'You are an award-winning brand identity designer. Judge whether each mark is a real, memorable, well-crafted logo: letterform quality, stroke weight, texture craft, colour, spacing, alignment, whether it looks cheap or premium, and whether the article title remains the hero.' },
  { name: 'audience', text: 'You represent the target audience: Chinese 考研 students aged 20-25 scrolling Bilibili/Douyin on a phone. Judge mainly from the phone-size previews: can 朋克英语 be read instantly, does it feel cool/punk yet trustworthy for study content, would you remember the brand, does the page look clean (not cluttered)?' },
  { name: 'editor', text: 'You are a senior video editor/motion designer for education channels. Judge how each title page works as the opening of the video: first-impression impact, how it transitions into the first content screen (style continuity with the dark-green content pages), whether the logo sits naturally in the layout on long and short titles, and any overlap, cut-off or imbalance.' },
]

// different presentation order per judge to avoid position bias
const ORDERS = [
  ['A_stamp', 'B_neon', 'C_graffiti', 'D_wordmark', 'E_ransom'],
  ['E_ransom', 'D_wordmark', 'C_graffiti', 'B_neon', 'A_stamp'],
  ['C_graffiti', 'E_ransom', 'A_stamp', 'D_wordmark', 'B_neon'],
]

phase('Judge')
const judges = (await parallel(LENSES.map((l, i) => () => agent(
  `${l.text}

${CONTEXT}

Versions (presented in this order):
${ORDERS[i].map((k, n) => `${n + 1}. ${k} — ${DESC[k]}\n${files(k)}`).join('\n')}

Score each version 1-10 on each criterion (be discriminating, use the full range, do not give everyone similar scores), list concrete strengths and problems, and give your top 3.`,
  { label: `judge:${l.name}`, phase: 'Judge', schema: SCORE_SCHEMA }
).then(r => r ? { ...r, lens: l.name } : null)))).filter(Boolean)

const totals = {}, rankSum = {}
for (const k of KEYS) { totals[k] = 0; rankSum[k] = 0 }
for (const j of judges) {
  const sorted = [...j.scores].sort((a, b) => b.total - a.total)
  sorted.forEach((s, idx) => { totals[s.key] += s.total; rankSum[s.key] += idx + 1 })
}
const ranked = [...KEYS].sort((a, b) => (totals[b] - totals[a]) || (rankSum[a] - rankSum[b]))
log('ranking: ' + ranked.map(k => `${k}=${totals[k].toFixed(2)}`).join(', '))

phase('Check')
const top3 = ranked.slice(0, 3)
const check = await agent(
  `You are a sceptical design critic doing a final check before results go to the client. ${CONTEXT}

Three judges (brand designer, target-audience student, video editor) produced this aggregate ranking (sum of weighted totals, higher is better):
${ranked.map((k, n) => `${n + 1}. ${k} — ${totals[k].toFixed(2)} — ${DESC[k]}`).join('\n')}

Judges' main problems found:
${judges.map(j => `[${j.lens}] ` + j.scores.map(s => `${s.key}: ${s.problems.join('; ')}`).join(' | ')).join('\n')}

Task: open the images for ALL five versions yourself (do not trust the judges blindly):
${KEYS.map(k => `${k}:\n${files(k)}`).join('\n')}
Try to REFUTE the top-3 selection (${top3.join(', ')}): is there a defect in any of them that should disqualify it (unreadable at phone size, overlap, cut-off, looks broken on long/short titles, glyph errors in 朋克英语), or is the 4th/5th version clearly better than a top-3 one? Default to confirming the ranking unless you find a concrete, verifiable reason. Report defects per version with exact location.`,
  { label: 'check:top3', phase: 'Check', schema: {
    type: 'object',
    properties: {
      confirmed: { type: 'boolean' },
      final_top3: { type: 'array', items: { type: 'string' } },
      reason: { type: 'string' },
      defects: { type: 'array', items: { type: 'object', properties: { key: { type: 'string' }, defect: { type: 'string' }, severity: { type: 'string' } }, required: ['key', 'defect', 'severity'] } },
    },
    required: ['confirmed', 'final_top3', 'reason', 'defects'],
  } }
)

return { ranked: ranked.map(k => ({ key: k, total: +totals[k].toFixed(2), rankSum: rankSum[k] })), judges, check }
