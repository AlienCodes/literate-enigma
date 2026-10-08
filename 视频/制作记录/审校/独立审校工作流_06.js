export const meta = {
  name: 'review-06-translation',
  description: 'Independent review of article 06 interlinear translation: 6 lens reviewers, per-sentence judges, consolidation with built-in tie-break (T20), verification, must-fix audit, chief-editor pass',
  phases: [
    { title: 'Review', detail: '6 reviewers, distinct lenses' },
    { title: 'Judge', detail: '2 judges per sentence' },
    { title: 'Merge', detail: 'consolidated + both-only versions per sentence' },
    { title: 'Verify', detail: '2 fresh judges accept consolidated or fall back' },
    { title: 'Chief', detail: 'whole-text consistency, judged; must-fix audit' },
  ],
}
const A = args
const COMMON = `你在为一个考研英语精读视频系列做译文审校。视频是"逐词对照"：每句英文拆成若干 chunk（每个 chunk 在视频里是一块高亮），每个 chunk 再分成若干"对齐组"（英文组 => 中文组），中文写在对应英文的正下方；从上往下、从左往右把中文连起来读，必须是通顺的一整句中文。这是教材，用户要求"精准、地道、通顺"，零瑕疵；用户亲笔改过的译法永远优先。

【必须先读的文件】（用 Read 读全文，不要凭印象）
- 风格总纲：${A.style}（第一节是必须遵守的要点，后面是 01–03 的详细分析和用户亲笔修改清单）
- 踩坑总表：${A.pit}（T、D、W 开头的条目都是真实出过的错；T4：before/after、increase/decrease、more/less 这类方向词必须逐个核对，before 不能放在"之后"上面）
- 第04篇制作记录：${A.rec04}（"用户修正稿 → 4K 定稿"一节：第二轮审校改了很多，用户一条都没采用，而是在第一稿上自己改了 8 处。说明：不要为改而改，只提确实更好的；用户能接受"都是**至关重要的**"这类"是…的"、斜杠并列、彩色括号说明）
- 第04篇定稿脚本：${A.j04}；第03篇定稿：${A.j03}（align 是 [英文组, 中文组] 列表）
- 第06篇文章：${A.article}（"## 英文"是原文——已按用户的硬性标准加了三处牛津逗号；"## 中文"是文章版译文，可参考但不是标准；"## 速查表"给每个重点词的词性和释义；"## 史实与来源"里有硬性要求：不写冯·奥斯滕是骗子、"仍坚信"只属于珠宝商、英文没写明的因果中文不加"因此""于是"）
- 第06篇初稿（要审的对象）：${A.draft}

【格式与硬约束】
- 重点词（英文里 **加粗** 的词）在中文里写成 **中文**(english)，括号里照抄英文原样（含大小写，如 Double-blind）。重点词集合固定，不能增删；过去时的"了"放进加粗。
- 英文一个字母都不能改（包括标点）。chunk 划分可以提建议（初稿还没给用户看过），但必须有明确好处。
- 原文没有、为了讲清楚而补的内容放进全角（），需要用户认可；只让中文成句、不添意思的虚词可以直接加；还原代词所指（They → 这些培养皿）可以直接写。
- note：全角（）包住，"英文结构：中文"，10–40 字，只讲真正难的句型、插入语、省略、术语；01–05 的 note 数是 7、2、12、14、14，初稿 11 条。
- 每个 chunk 英文最好不超过 10 个词；一组中文太长会让整屏字号变小。中文全角标点；数字写法跟英文一致（英文是单词就写汉字：thirteen → 十三，two → 两）；人名第一次全名加"·"；英文没有引号中文也不加。`

const FINDINGS = { type: 'object', properties: { findings: { type: 'array', items: { type: 'object', properties: {
  sentence: { type: 'string', description: '句号，如 S5' },
  chunk: { type: 'string', description: '如 S5-3；涉及整句或 chunk 重新划分时写 S5' },
  problem: { type: 'string', description: '问题是什么，为什么是问题（具体到字）' },
  rule: { type: 'string', description: '依据：风格总纲第几条 / 踩坑编号 / 01–04 哪句的先例 / 文章史实要求' },
  severity: { type: 'string', enum: ['必须改', '建议改'] },
  proposal: { type: 'string', description: '改后的完整写法，格式与初稿列表相同：每个 chunk 一行 "S5-3  英文组 => 中文组  |  英文组 => 中文组"，有 note 另起一行 "      note: （…）"；只写受影响的 chunk；英文一个字母都不能变' },
}, required: ['sentence', 'chunk', 'problem', 'rule', 'severity', 'proposal'] } } }, required: ['findings'] }
const VERDICT = { type: 'object', properties: { verdicts: { type: 'array', items: { type: 'object', properties: {
  index: { type: 'integer' }, accept: { type: 'boolean' },
  kind: { type: 'string', enum: ['采纳', '实质反对', '只是版本之争或重复'], description: '不采纳时说明是实质反对（问题不存在/改法更差），还是只因为与另一条重复、冲突、选了另一个版本' },
  reason: { type: 'string' } }, required: ['index', 'accept', 'kind', 'reason'] } } }, required: ['verdicts'] }
const EDIT = { type: 'object', properties: {
  chunks: { type: 'array', items: { type: 'object', properties: {
    align: { type: 'array', items: { type: 'object', properties: { en: { type: 'string' }, zh: { type: 'string' } }, required: ['en', 'zh'] } },
    note: { type: 'string', description: '没有 note 就写空字符串' } }, required: ['align', 'note'] } },
  changes: { type: 'string', description: '相对初稿改了什么（逐条，写明来自哪条意见）' } }, required: ['chunks', 'changes'] }
const VERD1 = { type: 'object', properties: { accept: { type: 'boolean' }, reason: { type: 'string' } }, required: ['accept', 'reason'] }

const LENSES = [
  { key: '精准', prompt: '你的角度：精准。逐组核对中文是否准确表达了英文：意思、方向（T4）、时态语态（被动保留"被"、过去完成译出"早已/曾"等）、限定和对冲、有没有添加原文没有的信息或漏掉原文的词（"原文每个词都有着落"）、代词所指、文章"史实与来源"里的硬性要求。' },
  { key: '通顺', prompt: '你的角度：通顺地道。把每句的中文组从上往下连起来读，像不像中国老师讲课时会说的话；有没有生硬、拗口、翻译腔、书面压缩、文言（即、其、这一、自身）、啰嗦、重复；一个 chunk 单独读能不能读通；全篇连起来读是否连贯。不要为了通顺牺牲精准。' },
  { key: '重点词', prompt: '你的角度：重点词。逐个检查 50 个重点词：词性规则（形容词带"的"、方式副词带"地"、程度频度观点类副词不带"地"、名词译名词动词译动词、"了"放进加粗、"们"不用）、加粗只覆盖等值部分（"被"在加粗外）、优先用贴合语境的考研词典义（参考速查表）、必要时用"核心义（语境说明）"两层写法、不同英文重点词不能用相同或几乎相同的中文、同一组里两个重点词的中文顺序。' },
  { key: '切分', prompt: '你的角度：对齐切分与版式。中英语序一致的地方是否细切（01–03 平均每组 1.75–2.74 个英文词，初稿 3.46，偏粗）；中文必须倒序的地方是否整组；虚词是否并入相邻实词组；句首时间状语、转折词是否单独成组；chunk 划分是否合理（每块是一个意群、不过长）；note 数量、格式、是否和行内括号重复、是否写成了整句释义。' },
  { key: '踩坑', prompt: '你的角度：踩坑总表逐条。把踩坑总表里 T1–T20、D1–D6、W4 以及标点、数字、专名的每一条，逐条拿来对初稿每一句，找出任何一处重犯。特别注意 T1（添加信息、原文内容放进括号）、T2/T3（词性）、T4（方向词）、T5/T9（切分）、T6/T7（生硬）、T13（比较、"X in Y"这类比例结构）、T15（前后不统一）、T16（数字）、T19（"了"在加粗外、是…的、数字写法、引号、即、们）。' },
  { key: '考研学生', prompt: '你的角度：考研学生。你英语中等、准备考研，看着这个视频学习：哪些句子结构你会看不懂、对不上英文（需要 note 而没有）；哪些 note 讲得不对、不清楚、没讲到考点或纯属多余；哪些中文让你误解了英文的结构或词义；重点词的中文是不是考研词汇书里会背到的义项。' },
]
const JUDGES = [
  { key: '忠实与规则', prompt: '你是裁判甲（忠实与规则）。对每条意见先尝试反驳：问题是否真的存在？改法是否更忠实于英文、更符合风格总纲和 01–04 定稿先例、更符合用户口味（看第04篇用户最终采用了什么）？改法有没有引入新问题（添加信息、词性错、英文被改、重点词丢失或标记错、和别的句子不统一）？拿不准就不采纳。' },
  { key: '通顺与教学', prompt: '你是裁判乙（通顺与教学）。对每条意见先尝试反驳：改后中文是否真的更通顺地道、学生是否真的更容易对上英文、note 是否真的更有用？有没有为改而改（用户在第04篇没采用大量此类改动）？是否让字数变多、版面变挤而没有明显收益？拿不准就不采纳。' },
]
const fmt = fs => fs.map((f, i) => `【${i}】(${f.lens}，${f.severity}) ${f.chunk}\n问题：${f.problem}\n依据：${f.rule}\n改法：\n${f.proposal}`).join('\n\n')
const show = (s, chunks) => chunks.map((c, k) => `${s}-${k + 1}  ` + c.align.map(g => `${g.en} => ${g.zh}`).join('  |  ') + (c.note ? `\n      note: ${c.note}` : '')).join('\n')

phase('Review')
const reviews = await parallel(LENSES.map(L => () =>
  agent(`${COMMON}\n\n${L.prompt}\n\n请逐句审完全部 19 句，列出你发现的每一个问题（宁多勿漏，每条都要具体、有依据、给出完整改法）。没有问题的句子不用写。`,
    { label: `review:${L.key}`, phase: 'Review', schema: FINDINGS })))
const all = []
reviews.forEach((r, i) => { if (r) for (const f of r.findings) all.push({ ...f, lens: LENSES[i].key }) })
const bySent = {}
for (const f of all) { const m = `${f.sentence} ${f.chunk}`.match(/S\d+/); if (m) (bySent[m[0]] = bySent[m[0]] || []).push(f) }
const sents = Object.keys(bySent).sort((a, b) => +a.slice(1) - +b.slice(1))
log(`审校意见 ${all.length} 条，涉及 ${sents.length} 句`)

const perSent = await pipeline(sents,
  s => parallel(JUDGES.map(J => () => agent(`${COMMON}\n\n${J.prompt}\n\n下面是针对 ${s} 的 ${bySent[s].length} 条审校意见（编号从 0 开始）。先读初稿里 ${s} 及其前后句，再逐条判定。不采纳时，kind 要写清是"实质反对"（问题不存在或改法更差）还是"只是版本之争或重复"（实质改动你同意，只是另一条写得更好或和别的意见重复）。\n\n${fmt(bySent[s])}`,
    { label: `judge:${J.key}:${s}`, phase: 'Judge', schema: VERDICT }))),
  (vs, s) => {
    const [a, b] = vs
    if (!a || !b) return { s, final: null, note: '裁判结果缺失' }
    const V = (x, i) => x.verdicts.find(v => v.index === i) || { accept: false, kind: '实质反对', reason: '未判' }
    const items = bySent[s].map((f, i) => ({ f, i, a: V(a, i), b: V(b, i) }))
    const both = items.filter(x => x.a.accept && x.b.accept)
    const single = items.filter(x => (x.a.accept !== x.b.accept) && ((x.a.accept ? x.b : x.a).kind !== '实质反对'))
    if (!both.length && !single.length) return { s, final: null, items }
    const lst = xs => xs.map(x => `【${x.i}】${x.f.chunk}：${x.f.problem}\n改法：\n${x.f.proposal}\n裁判甲（${x.a.accept ? '采纳' : x.a.kind}）：${x.a.reason}\n裁判乙（${x.b.accept ? '采纳' : x.b.kind}）：${x.b.reason}`).join('\n\n')
    const ask = (which, xs) => agent(`${COMMON}\n\n你是 ${s} 的编辑。把下面这些意见合并成这一句的最终写法（${which}）。输出这一句全部 chunk（按顺序，没改的原样照抄初稿），每个 chunk 给出 align 和 note（没有写空字符串）。英文组按顺序拼起来必须与原句英文一字不差（包括标点、空格和 ** 标记，组的首尾不要带空格）；每个加粗英文词在同一 chunk 的中文里有 **中文**(english)；几条意见改同一处时，按两位裁判理由里共同认可的部分取舍；只改意见要求改的地方。\n\n${lst(xs)}`,
      { label: `edit:${which === '只含两位都采纳的' ? 'both' : 'merged'}:${s}`, phase: 'Merge', schema: EDIT })
    const p = [both.length ? ask('只含两位都采纳的', both) : Promise.resolve(null)]
    if (single.length) p.push(ask('两位都采纳的 + 一位采纳、另一位只是版本之争的', both.concat(single)))
    return Promise.all(p).then(([bo, me]) => ({ s, items, both: bo, merged: me || null, singleIdx: single.map(x => x.i) }))
  },
  r => {
    if (!r || !r.merged) return { ...r, final: r && r.both ? r.both : null, verified: null }
    return parallel(JUDGES.map(J => () => agent(`${COMMON}\n\n${J.prompt}\n\n这是 ${r.s}。初稿见 ${A.draft}。下面"合并版"在两位裁判都同意的改动之外，还加进了只有一位裁判采纳、另一位只是版本之争的改动（意见编号 ${r.singleIdx.join('、')}）。"保守版"只含两位都采纳的改动${r.both ? '' : '（这句没有，保守版即初稿）'}。请判断合并版是否明显好于保守版：明显更好就采纳，拿不准就不采纳。\n\n合并版：\n${show(r.s, r.merged.chunks)}\n编辑说明：${r.merged.changes}\n\n保守版：\n${r.both ? show(r.s, r.both.chunks) : '（同初稿）'}`,
      { label: `verify:${J.key}:${r.s}`, phase: 'Verify', schema: VERD1 })))
      .then(vs => { const ok = vs.every(v => v && v.accept); return { ...r, verified: vs, final: ok ? r.merged : r.both } })
  })

const finals = {}
for (const r of perSent.filter(Boolean)) if (r.final) finals[r.s] = r.final
log(`改动的句子：${Object.keys(finals).join(' ')}`)

phase('Chief')
const edited = Object.entries(finals).map(([s, e]) => `${s}（已改）\n` + show(s, e.chunks)).join('\n\n')
const chief = await agent(`${COMMON}\n\n你是总编辑。初稿在 ${A.draft}；下面这些句子已按审校结果改过（以这里为准，其余以初稿为准）。把改后的全篇当成一个整体通读：①全篇中文从头到尾连读是否连贯；②同一事物前后说法是否统一（提问者、表演/展示、汉斯/它、敲击、提示、委员会/委员）；③note 总数、分布、格式是否统一；④标点、数字、专名是否统一；⑤改过的句子有没有引入新问题（英文组首尾空格、重点词标记、"了"的位置）。只提确实需要改的，每条给完整改法。\n\n${edited}`,
  { label: 'chief', phase: 'Chief', schema: FINDINGS })
const chiefF = chief ? chief.findings.map(f => ({ ...f, lens: '总编辑' })) : []
let chiefAcc = []
if (chiefF.length) {
  const cj = await parallel(JUDGES.map(J => () => agent(`${COMMON}\n\n${J.prompt}\n\n下面是总编辑对全篇的一致性意见（编号从 0 开始），请逐条判。全篇 = 初稿 ${A.draft} + 以下已改句子。\n\n已改句子：\n${edited}\n\n意见：\n${fmt(chiefF)}`,
    { label: `judge:${J.key}:chief`, phase: 'Chief', schema: VERDICT })))
  if (cj[0] && cj[1]) chiefAcc = chiefF.filter((f, i) => cj[0].verdicts.find(v => v.index === i)?.accept && cj[1].verdicts.find(v => v.index === i)?.accept)
}
const must = []
for (const r of perSent.filter(Boolean)) for (const x of (r.items || [])) if (x.f.severity === '必须改' && (x.a.accept || x.b.accept)) must.push({ s: r.s, i: x.i, chunk: x.f.chunk, problem: x.f.problem, proposal: x.f.proposal, a: `${x.a.accept ? '采纳' : x.a.kind}：${x.a.reason}`, b: `${x.b.accept ? '采纳' : x.b.kind}：${x.b.reason}` })
const audit = must.length ? await agent(`${COMMON}\n\n你是核对员（T20：上一篇出过"大家都同意必须改、最后却没改成"的事故）。下面每一条都是至少一位裁判采纳的"必须改"意见。请逐条对照最终稿（初稿 ${A.draft} + 以下已改句子 + 总编辑采纳的意见），判断这个问题在最终稿里是否已经解决；没解决的，说明是否有一位裁判给出了站得住的实质反对理由。\n\n已改句子：\n${edited}\n\n总编辑采纳：\n${chiefAcc.map(f => f.proposal).join('\n')}\n\n必须改意见：\n${must.map((m, k) => `【${k}】${m.chunk}：${m.problem}\n改法：${m.proposal}\n裁判甲：${m.a}\n裁判乙：${m.b}`).join('\n\n')}`,
  { label: 'audit', phase: 'Chief', schema: { type: 'object', properties: { items: { type: 'array', items: { type: 'object', properties: { index: { type: 'integer' }, resolved: { type: 'boolean' }, justified: { type: 'boolean', description: '没解决时：不改是否有站得住的实质理由' }, comment: { type: 'string' } }, required: ['index', 'resolved', 'justified', 'comment'] } } }, required: ['items'] } }) : { items: [] }
return { counts: { findings: all.length, sentencesEdited: Object.keys(finals).length, chief: chiefF.length, chiefAccepted: chiefAcc.length, mustFix: must.length },
  finals, chiefAccepted: chiefAcc, must, audit, perSent: perSent.filter(Boolean).map(r => ({ s: r.s, singleIdx: r.singleIdx, verified: r.verified, usedMerged: !!(r.merged && r.final === r.merged), items: (r.items || []).map(x => ({ i: x.i, lens: x.f.lens, chunk: x.f.chunk, severity: x.f.severity, problem: x.f.problem, a: x.a, b: x.b })) })) }
