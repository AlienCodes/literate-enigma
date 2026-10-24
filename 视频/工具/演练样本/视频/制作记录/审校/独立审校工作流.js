export const meta = {
  name: 'review-04-translation',
  description: 'Check article 04 translation against the style of finalized 01-03 and every recorded pitfall; adversarially judge each finding',
  phases: [
    { title: 'Style', detail: 'extract translation style + user correction patterns from 01, 02, 03' },
    { title: 'Review', detail: '6 lenses: fidelity, fluency, style, keywords, pitfall checklist, student' },
    { title: 'Judge', detail: 'one adversarial judge per paragraph' },
    { title: 'Final', detail: 'cross-article consistency and final change list' },
  ],
}

const CTX = `
PROJECT: bilingual 考研 English intensive-reading videos (逐词对照: each English chunk is one line on screen; under each English group sits its Chinese). Translations must be 精准、地道、通顺. Articles 01, 02, 03 are FINAL; the user considers them perfect and they are THE style reference. Article 04 is a draft under review.
FILES (read them yourself with your file tools):
- Final reference scripts: /home/user/postgraduate-vocabulary/视频/脚本/01.json , 02.json , 03.json
- Article under review: /home/user/postgraduate-vocabulary/视频/脚本/04.json
- User's correction history/decisions per article: /home/user/postgraduate-vocabulary/视频/制作记录/01.md , 02.md , 03.md  (04.md lists what I changed today in my own review)
- Pitfall table (every past mistake; must never be repeated): /home/user/postgraduate-vocabulary/视频/踩坑总表.md
- Hard rules: /home/user/postgraduate-vocabulary/视频/硬性条件.md ; translation standard: /home/user/postgraduate-vocabulary/视频/README.md section "五、翻译标准"
JSON FORMAT: sentences[] (each has para) -> chunks[]; chunk.en = English line (**bold** = keyword; {{...}} = display-only gloss); chunk.zh = Chinese; chunk.align = list of [en_group, zh_group] pairs (English groups joined with single spaces == en; zh groups concatenated == zh; the pair ["\\n",""] is a manual line-break marker); optional chunk.note = grammar/background note shown on its own line under the chunk, written in full-width （）.
ZH CONVENTIONS: keyword Chinese is bold and immediately followed by the English keyword in ASCII parentheses, e.g. **脱口说出**(rattle off). Added explanations go in full-width （）.
NUMBERING: refer to sentences as S1..S17 in file order (1-based) and chunks 1-based within the sentence.
HARD CONSTRAINTS for any proposed fix: never change the English text, the chunk boundaries, or the ["\\n",""] line-break markers (user rule L13: no line-break changes without the user's permission). You MAY change zh groups, how a chunk's English is split into align groups (joined English must stay identical), and notes. Keyword POS rule T2/T3: Chinese part of speech must match the English (adjective → "…的", adverb → "…地") — check how 01–03 actually applied it. Never add information that is not in the original except inside full-width （）, and any such addition needs user approval. Do not add or remove keywords.
`

const FIND_RULES = `
OUTPUT RULES: report only real problems. severity: must = wrong / violates a rule or a recorded pitfall; should = clearly better and more in line with 01–03; optional = taste. For each finding give: sentence (S number as integer), chunk (integer), issue (简体中文), pitfall_ids (ids from 踩坑总表 or 硬性条件 if any), severity, proposed_align = the COMPLETE new align list for that chunk as [[en_group, zh_group], ...] (English groups joined with spaces must equal the chunk's English exactly; keep ["\\n",""] markers exactly in place), proposed_note (new note text in full-width （）; "" to remove the note; omit to keep it unchanged), rationale (简体中文). Every proposal must itself satisfy all hard constraints and the zh conventions.
`

const STYLE_SCHEMA = {
  type: 'object',
  properties: {
    article: { type: 'string' },
    rules: { type: 'array', items: { type: 'object', properties: {
      aspect: { type: 'string' }, rule: { type: 'string' }, examples: { type: 'array', items: { type: 'string' } } }, required: ['aspect', 'rule', 'examples'] } },
    user_corrections: { type: 'array', items: { type: 'object', properties: {
      where: { type: 'string' }, before: { type: 'string' }, after: { type: 'string' }, lesson: { type: 'string' } }, required: ['where', 'after', 'lesson'] } },
  },
  required: ['article', 'rules', 'user_corrections'],
}

const FINDING = { type: 'object', properties: {
  sentence: { type: 'integer' }, chunk: { type: 'integer' }, issue: { type: 'string' },
  pitfall_ids: { type: 'array', items: { type: 'string' } },
  severity: { type: 'string', enum: ['must', 'should', 'optional'] },
  proposed_align: { type: 'array', items: { type: 'array', items: { type: 'string' } } },
  proposed_note: { type: 'string' }, rationale: { type: 'string' } },
  required: ['sentence', 'chunk', 'issue', 'severity', 'rationale'] }

const REVIEW_SCHEMA = { type: 'object', properties: {
  findings: { type: 'array', items: FINDING },
  checklist: { type: 'array', items: { type: 'object', properties: {
    id: { type: 'string' }, applies: { type: 'boolean' }, ok: { type: 'boolean' }, evidence: { type: 'string' } }, required: ['id', 'applies', 'ok', 'evidence'] } } },
  required: ['findings'] }

const CHUNK_OUT = { type: 'object', properties: {
  sentence: { type: 'integer' }, chunk: { type: 'integer' },
  align: { type: 'array', items: { type: 'array', items: { type: 'string' } } },
  note_action: { type: 'string', enum: ['keep', 'set', 'remove'] }, note: { type: 'string' }, reason: { type: 'string' } },
  required: ['sentence', 'chunk', 'align', 'note_action', 'reason'] }

const JUDGE_SCHEMA = { type: 'object', properties: {
  decisions: { type: 'array', items: { type: 'object', properties: {
    idx: { type: 'integer' }, accepted: { type: 'boolean' }, reason: { type: 'string' } }, required: ['idx', 'accepted', 'reason'] } },
  final_chunks: { type: 'array', items: CHUNK_OUT },
  own_additions: { type: 'array', items: { type: 'string' } } },
  required: ['decisions', 'final_chunks'] }

const FINAL_SCHEMA = { type: 'object', properties: {
  changes: { type: 'array', items: CHUNK_OUT },
  consistency_notes: { type: 'array', items: { type: 'string' } },
  needs_user_confirmation: { type: 'array', items: { type: 'string' } },
  style_verdict: { type: 'string' },
  summary: { type: 'string' } },
  required: ['changes', 'needs_user_confirmation', 'style_verdict', 'summary'] }

phase('Style')
const styles = (await parallel(['01', '02', '03'].map(n => () => agent(
  `${CTX}
TASK: You are a translation-style analyst. Study FINAL article ${n} (/home/user/postgraduate-vocabulary/视频/脚本/${n}.json) together with its correction history (/home/user/postgraduate-vocabulary/视频/制作记录/${n}.md) and the 踩坑总表 translation section. Extract the concrete, reusable translation style the user approved, as rules with real examples quoted from ${n}.json. Cover at least: how finely English is split into align groups and when whole clauses are kept together; how keywords are rendered (context sense vs dictionary sense, part of speech, adverbs with 地, adjectives with 的, participles); how comparisons/discontinuous phrases are handled; when and how full-width （） additions are used; what notes look like (format, length, which grammar points get a note); punctuation, quotes, proper nouns, journals, numbers; tone/register of the Chinese (how colloquial vs formal). Also list every correction the user personally made in ${n} (before → after, and the lesson about the user's taste). Write in 简体中文.`,
  { label: `style:${n}`, phase: 'Style', schema: STYLE_SCHEMA })))).filter(Boolean)
const styleText = JSON.stringify(styles)
log(`style reports: ${styles.length}`)

phase('Review')
const LENSES = [
  { key: 'fidelity', prompt: `精准 lens. For every sentence of 04 compare the Chinese with the English meaning precisely: nothing added outside （）, nothing omitted, correct referents, logical relations (and/yet/so/or), directions (larger/smaller, precede, trail, rear/front), numbers and units, and the exact sense of each phrase in THIS context (e.g. "rattle off", "hard-won", "Hopefuls", "went with", "Longer service", "left the cause uncertain", "dispelled the second notion", "tackled the first", "began alike", "entail a trade-off", "trailed … on one test of recalling an intricate figure", "occupied room once claimed by something else"). Flag every mistranslation or imprecision and give a fix.` },
  { key: 'fluency', prompt: `地道通顺 lens. For each sentence, concatenate the zh of all its chunks, strip ** and (english) markers, and read it as a native Chinese reader. Flag every place that is translationese, ungrammatical, redundant, choppy, or unnatural (pitfalls T6, T7, T15). The reading order follows the English chunk order, so some inversion is unavoidable — within that constraint find the most natural Chinese, the way 01–03 solved similar problems. Propose rewrites that keep all hard constraints.` },
  { key: 'style', prompt: `风格一致 lens. The user says 01–03 are perfect. Compare 04 against them systematically using the style reports: align-group granularity, keyword rendering, notes (format, length, which points get notes), （） additions, punctuation and quotes, proper nouns (people, places, journals), numbers, register. List every place where 04 departs from the established 01–03 style and propose fixes.` },
  { key: 'keywords', prompt: `重点词 lens. For EVERY **bold** English keyword in 04: (a) marker format exactly like 01–03; (b) part of speech matches (T2/T3) — check how 01–03 treated adverbs, adjectives, participles; (c) the bold Chinese covers exactly the keyword's meaning and not its neighbours (T5); (d) discontinuous phrases: both parts bold + same marker (T14); (e) the sense is right in this context and is a good gloss for a 考研 learner; (f) the same keyword/term is rendered consistently across the article. Do not propose adding/removing keywords.` },
  { key: 'pitfalls', prompt: `踩坑逐条 lens. Go through EVERY row id in 踩坑总表.md sections 一（翻译）, 二（对照数据）, 六（Word / 文本往返） and every numbered item in 硬性条件.md sections 二（翻译）and 三（英文原文与重点词）. For each one decide whether it applies to 04's translation draft and whether 04 currently violates it, with concrete evidence (quote the chunk). Output a checklist entry for EVERY id in those sections (for 硬性条件 items use ids like HC2.1, HC3.2) — do not skip any — plus a finding for each violation.` },
  { key: 'student', prompt: `教学 lens (考研学生). Read 04 as a 考研 student learning from the interlinear video. Where would the student be confused by structure or vocabulary? Compare with the kinds of notes 01–03 give (e.g. into which 语序, blame A on B, so + adj + a + noun, 插入语). Flag missing or unclear notes for genuinely difficult grammar (e.g. "its rear, or posterior, portion", the ellipsis in "and its front, or anterior, portion smaller", "Every street learned, it seems, occupied room once claimed by something else", "the 39 who qualified", appositive "the tissue dense with nerve cells", "of equivalent experience and stress", "Name two addresses and …"), and notes that are wrong or unhelpful. Keep note style identical to 01–03; do not overload — only what a student needs.` },
]
const reviews = await parallel(LENSES.map(l => () => agent(
  `${CTX}
STYLE REPORTS extracted from the final articles 01–03:
${styleText}

TASK — reviewer (${l.key}): ${l.prompt}
${FIND_RULES}`,
  { label: `review:${l.key}`, phase: 'Review', schema: REVIEW_SCHEMA })))

const all = []
reviews.forEach((r, i) => { if (r) r.findings.forEach(f => all.push({ ...f, lens: LENSES[i].key })) })
const checklists = reviews.map((r, i) => (r && r.checklist && r.checklist.length) ? { lens: LENSES[i].key, checklist: r.checklist } : null).filter(Boolean)
const missing = LENSES.filter((l, i) => !reviews[i]).map(l => l.key)
if (missing.length) log(`WARNING reviewers returned nothing: ${missing.join(', ')}`)
log(`${all.length} findings from ${reviews.filter(Boolean).length} reviewers`)

phase('Judge')
const PARAS = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11], [12, 13, 14], [15, 16, 17]]
const judged = await parallel(PARAS.map((ss, pi) => () => {
  const fs = all.filter(f => ss.includes(f.sentence)).map((f, k) => ({ idx: k, ...f }))
  return agent(
    `${CTX}
STYLE REPORTS from 01–03:
${styleText}

TASK: You are the adversarial judge for paragraph ${pi + 1} of 04 (sentences ${ss.map(s => 'S' + s).join(', ')}). Below are the reviewers' findings for these sentences (JSON, each with idx and the reviewer lens). For EACH finding, first try to REFUTE it: is the current 04 version actually correct, natural, and consistent with 01–03? Is the proposal genuinely better, faithful to the English, fluent, in 01–03 style, and compliant with every hard constraint? Accept only if clearly better; when several findings target the same chunk, merge them into one best version. Then re-read every sentence of this paragraph yourself (English vs Chinese, whole-sentence Chinese read-through) and fix anything all reviewers missed — conservatively — listing those in own_additions.
Output decisions (one per idx) and final_chunks ONLY for chunks that change: sentence, chunk, align (COMPLETE list for the chunk), note_action keep/set/remove, note, reason (简体中文). Before answering, verify mechanically for each changed chunk: English groups joined with spaces equal the chunk's original English exactly; ["\\n",""] markers unchanged; every **bold** English keyword in the chunk has a matching **中文**(english) marker in its zh group; any new （） addition is listed in reason as needing user approval.
FINDINGS:
${JSON.stringify(fs)}`,
    { label: `judge:para${pi + 1}`, phase: 'Judge', schema: JUDGE_SCHEMA }).then(j => ({ para: pi + 1, sentences: ss, findings: fs, judgment: j }))
}))

phase('Final')
const final = await agent(
  `${CTX}
STYLE REPORTS from 01–03:
${styleText}

TASK: You are the final consistency editor for 04. Below are the per-paragraph judgments (each has the findings it saw, its decisions, and final_chunks it wants changed). Produce the FINAL complete change list for the whole article: start from all judges' final_chunks, then (1) check cross-sentence consistency of terms and renderings (e.g. notion, rear/posterior, front/anterior, trainees/non-trainees, cabbies, grey matter, qualify), (2) read the whole article's Chinese from S1 to S17 with the changes applied and fix any remaining unnatural spot, (3) resolve any conflicts, (4) re-verify every hard constraint mechanically for every changed chunk. If a judge's change is wrong, drop or correct it and say why in consistency_notes. Output changes (COMPLETE align list per changed chunk), consistency_notes, needs_user_confirmation (every （） addition or judgment call the user should approve, quoted), style_verdict (简体中文: how well 04 now matches 01–03 style, honestly), and summary (简体中文, for the user: what changed and why, grouped by type).
JUDGMENTS:
${JSON.stringify(judged)}`,
  { label: 'final:consistency', phase: 'Final', schema: FINAL_SCHEMA })

return { styles, checklists, n_findings: all.length, findings: all, judged, final }
