export const meta = {
  name: 'review-05-translation',
  description: 'Independent review of article 05 interlinear translation: 6 lens reviewers, per-sentence adversarial judges, per-sentence editors, chief-editor consistency pass',
  phases: [
    { title: 'Review', detail: '6 reviewers, distinct lenses' },
    { title: 'Judge', detail: '2 judges per sentence, accept only if both accept' },
    { title: 'Edit', detail: 'merge accepted findings per sentence' },
    { title: 'Chief', detail: 'whole-text consistency pass, judged again' },
  ],
}

const A = args
const COMMON = `你在为一个考研英语精读视频系列做译文审校。视频是"逐词对照"：每句英文拆成若干 chunk（每个 chunk 在视频里是一块高亮），每个 chunk 里再分成若干"对齐组"（英文组 => 中文组），中文写在对应英文的正下方；从上往下、从左往右把中文连起来读，必须是通顺的一整句中文。
这是教材，用户要求译文"精准、地道、通顺"，零瑕疵。用户亲笔改过的译法永远优先。

【必须先读的文件】（用 Read 工具读全文，不要凭印象）
- 风格总纲：${A.style}（以已定稿的第01–03篇为样板，第一节是必须遵守的要点，后面是各篇详细分析和用户亲笔修改清单）
- 踩坑总表：${A.pit}（"一、翻译"和"二、对齐/数据"等节里 T、D、W 开头的条目，都是真实出过的错）
- 第04篇制作记录：${A.rec04}（重要：看"用户修正稿 → 4K 定稿"一节——第二轮审校改了很多，用户一条都没采用，而是在第一稿上自己改了 8 处。说明：不要为改而改，只提确实更好的；用户能接受"都是**至关重要的**"这类"是…的"、"考生们"、"暗示/意味着"这类斜杠并列、彩色括号说明）
- 第04篇定稿脚本：${A.j04}；第03篇定稿：${A.j03}（最近的样板，align 是 [英文组, 中文组] 列表）
- 第05篇文章：${A.article}（"## 英文"是原文；"## 中文"是文章版译文，可参考但不是标准；"## 速查表"是每个重点词的词性和释义；"## 史实与来源"里有对译法的硬性要求，例如 promptly 译"很快"、detained 译"拘留"、known to be 译"已知"、someone 译"有人"不点明性别、seemingly 译"似乎"、A tip-off, not the screening… 照译"一条举报"、英文没写明的因果中文不加"因此""于是"、不写受害者姓名）
- 第05篇初稿（要审的对象）：${A.draft}

【格式与硬约束】
- 重点词（英文里 **加粗** 的词）在中文里写成 **中文**(english)，括号里照抄英文原样。重点词集合是固定的，不能增删。
- 英文一个字母都不能改（包括标点）。chunk 划分可以提建议（初稿还没给用户看过），但必须有明确的好处。
- 原文没有、为了讲清楚而补的内容放进全角（），需要用户认可；只让中文成句、不添意思的虚词可以直接加。
- note 是 chunk 下方单独一行的说明：全角（）包住，"英文结构：中文"，10–40 字，只讲真正难的句型、插入语、省略、术语；01–04 的 note 数分别是 7、2、12、14，初稿有 15 条。
- 每个 chunk 是视频里的一块，英文最好不超过 10 个词；一组中文太长会让整屏字号变小。
- 中文用全角标点；数字写法跟英文一致（英文是阿拉伯数字就写阿拉伯数字，是单词就写汉字）；人名第一次全名加"·"。`

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          sentence: { type: 'string', description: '句号，如 S5' },
          chunk: { type: 'string', description: '如 S5-3；涉及整句或 chunk 重新划分时写 S5' },
          problem: { type: 'string', description: '问题是什么，为什么是问题（具体到字）' },
          rule: { type: 'string', description: '依据：风格总纲第几条 / 踩坑编号 / 01–04 哪句的先例 / 文章史实要求' },
          severity: { type: 'string', enum: ['必须改', '建议改'] },
          proposal: { type: 'string', description: '改后的完整写法，格式与初稿列表完全相同：每个 chunk 一行 "S5-3  英文组 => 中文组  |  英文组 => 中文组"，有 note 另起一行 "      note: （…）"；只写受影响的 chunk；英文一个字母都不能变' },
        },
        required: ['sentence', 'chunk', 'problem', 'rule', 'severity', 'proposal'],
      },
    },
  },
  required: ['findings'],
}
const VERDICT = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: { index: { type: 'integer' }, accept: { type: 'boolean' }, reason: { type: 'string' } },
        required: ['index', 'accept', 'reason'],
      },
    },
  },
  required: ['verdicts'],
}
const EDIT = {
  type: 'object',
  properties: {
    sentence: { type: 'string' },
    chunks: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          align: { type: 'array', items: { type: 'object', properties: { en: { type: 'string' }, zh: { type: 'string' } }, required: ['en', 'zh'] } },
          note: { type: 'string', description: '没有 note 就写空字符串' },
        },
        required: ['align', 'note'],
      },
    },
    changes: { type: 'string', description: '相对初稿改了什么（逐条）' },
  },
  required: ['sentence', 'chunks', 'changes'],
}

const LENSES = [
  { key: '精准', prompt: '你的角度：精准。逐组核对中文是否准确表达了英文：意思、方向（谁对谁做了什么）、时态语态（被动保留"被"、过去完成译出"早已/曾/事先"等）、限定和对冲（seemingly、known to be、someone 等）、有没有添加原文没有的信息或漏掉原文的词（"原文每个词都有着落"）、文章"史实与来源"里的硬性要求。' },
  { key: '通顺', prompt: '你的角度：通顺地道。把每句的中文组从上往下连起来读，像不像中国老师在讲课时会说的话；有没有生硬、拗口、翻译腔、书面压缩、文言（即、其、这一、自身）、啰嗦、重复；一个 chunk 单独读能不能读通；全篇连起来读是否连贯。不要为了通顺牺牲精准。' },
  { key: '重点词', prompt: '你的角度：重点词。逐个检查 54 个重点词：词性规则（形容词带"的"、方式副词带"地"、程度频度观点类副词不带"地"、名词译名词动词译动词、"了"放进加粗、"们"不用）、加粗只覆盖等值部分、优先用贴合语境的考研词典义（参考速查表）、必要时用"核心义（语境说明）"两层写法、不同英文重点词不能用相同或几乎相同的中文、同一句里两个重点词的中文顺序。' },
  { key: '切分', prompt: '你的角度：对齐切分与版式。中英语序一致的地方是否细切（01–03 平均每组 1.75–2.74 个英文词，初稿是 3.23，偏粗）；中文必须倒序的地方是否整组；虚词是否并入相邻实词组；句首时间状语、转折词是否单独成组；chunk 划分是否合理（每块是一个意群、不过长）；note 数量是否过多、格式是否对、是否和行内括号重复、是否写成了整句释义。' },
  { key: '踩坑', prompt: '你的角度：踩坑总表逐条。把踩坑总表里 T1–T19、D1–D6、W4 以及标点、数字、专名的每一条，逐条拿来对初稿每一句，找出任何一处重犯。特别注意 T1（添加信息、原文内容放进括号）、T2/T3（词性）、T5/T9（切分粒度）、T6/T7（生硬、拆得不通顺）、T13（比较结构）、T15（前后不统一）、T16（数字）、T19（"了"在加粗外、是…的、数字写法、引号、即、们）。' },
  { key: '考研学生', prompt: '你的角度：考研学生。你是一个英语中等、准备考研的学生，看着这个视频学习：哪些句子结构你会看不懂、对不上英文（需要 note 而没有）；哪些 note 讲得不对、不清楚、没讲到考点、或者纯属多余；哪些中文让你误解了英文的结构或词义；重点词的中文是否是你在考研词汇书里会背到的义项。' },
]

phase('Review')
const reviews = await parallel(LENSES.map(L => () =>
  agent(`${COMMON}\n\n${L.prompt}\n\n请逐句审完全部 19 句，列出你发现的每一个问题（宁多勿漏，但每条都要具体、有依据、给出完整改法）。没有问题的句子不用写。`,
    { label: `review:${L.key}`, phase: 'Review', schema: FINDINGS })))
const all = []
reviews.forEach((r, i) => { if (r) for (const f of r.findings) all.push({ ...f, lens: LENSES[i].key }) })
log(`审校意见共 ${all.length} 条`)

const bySent = {}
for (const f of all) { const s = (f.sentence || f.chunk || '').match(/S\d+/); if (!s) continue; (bySent[s[0]] = bySent[s[0]] || []).push(f) }
const sents = Object.keys(bySent).sort((a, b) => +a.slice(1) - +b.slice(1))

const fmt = fs => fs.map((f, i) => `【${i}】(${f.lens}，${f.severity}) ${f.chunk}\n问题：${f.problem}\n依据：${f.rule}\n改法：\n${f.proposal}`).join('\n\n')

const JUDGES = [
  { key: '忠实与规则', prompt: '你是裁判甲（忠实与规则）。对每条意见，先尝试反驳它：它说的问题是否真的存在？改法是否更忠实于英文、更符合风格总纲和 01–04 定稿的先例、更符合用户口味（看第04篇用户最终采用了什么）？改法有没有引入新问题（添加信息、词性错、英文被改、重点词丢失或标记错、和别的句子不统一）？拿不准就判不采纳。' },
  { key: '通顺与教学', prompt: '你是裁判乙（通顺与教学）。对每条意见，先尝试反驳它：改后中文是否真的更通顺地道、学生是否真的更容易对上英文、note 是否真的更有用？有没有为改而改（用户在第04篇没采用大量此类改动）？改法是否让字数变多、版面变挤而没有明显收益？拿不准就判不采纳。' },
]

phase('Judge')
const judged = await parallel(sents.map(s => () => parallel(JUDGES.map(J => () =>
  agent(`${COMMON}\n\n${J.prompt}\n\n下面是针对 ${s} 的 ${bySent[s].length} 条审校意见（编号从 0 开始）。请先读初稿里 ${s} 及其前后句，再逐条给出采纳与否和理由（index 用意见编号）。如果两条意见互相冲突，最多采纳其中更好的一条。\n\n${fmt(bySent[s])}`,
    { label: `judge:${J.key}:${s}`, phase: 'Judge', schema: VERDICT })))
  .then(vs => ({ s, vs }))))

const accepted = {}
for (const r of judged.filter(Boolean)) {
  const [a, b] = r.vs
  if (!a || !b) continue
  const okA = new Set(a.verdicts.filter(v => v.accept).map(v => v.index))
  const okB = new Set(b.verdicts.filter(v => v.accept).map(v => v.index))
  const acc = bySent[r.s].map((f, i) => ({ f, i })).filter(x => okA.has(x.i) && okB.has(x.i)).map(x => ({ ...x.f, whyA: a.verdicts.find(v => v.index === x.i)?.reason, whyB: b.verdicts.find(v => v.index === x.i)?.reason }))
  if (acc.length) accepted[r.s] = acc
}
log(`两位裁判都采纳的意见：${Object.values(accepted).reduce((n, x) => n + x.length, 0)} 条，涉及 ${Object.keys(accepted).length} 句`)

phase('Edit')
const edits = await parallel(Object.keys(accepted).map(s => () =>
  agent(`${COMMON}\n\n你是这一句的编辑。下面是两位裁判都采纳了的审校意见（针对 ${s}）。请读初稿里的 ${s}，把这些意见合并成这一句的最终写法：输出这一句全部 chunk（按顺序，包括没改的 chunk 原样照抄），每个 chunk 给出 align（英文组、中文组）和 note（没有就写空字符串）。要求：英文组按顺序拼起来必须与原句英文一字不差（包括标点和 ** 加粗标记）；每个加粗英文词在同一 chunk 的中文里有 **中文**(english) 标记；只改意见要求改的地方，不要顺手改别的。\n\n${accepted[s].map((f, i) => `【${i}】${f.chunk}：${f.problem}\n改法：\n${f.proposal}\n裁判甲：${f.whyA}\n裁判乙：${f.whyB}`).join('\n\n')}`,
    { label: `edit:${s}`, phase: 'Edit', schema: EDIT })))
const editMap = {}
const accKeys = Object.keys(accepted)
edits.forEach((e, i) => { if (e) editMap[accKeys[i]] = { ...e, sentence: accKeys[i] } })
log(`编辑完成 ${Object.keys(editMap).length}/${accKeys.length} 句`)

phase('Chief')
const edited = Object.values(editMap).map(e => `${e.sentence}（已改）\n` + e.chunks.map((c, k) => `${e.sentence}-${k + 1}  ` + c.align.map(g => `${g.en} => ${g.zh}`).join('  |  ') + (c.note ? `\n      note: ${c.note}` : '')).join('\n')).join('\n\n')
const chief = await agent(`${COMMON}\n\n你是总编辑。初稿在 ${A.draft}；下面这些句子已经按审校结果改过（以这里为准，其余句子以初稿为准）。请把改后的全篇当成一个整体通读：①全篇中文从头到尾连读是否连贯；②同一事物前后说法是否统一（如 青年/少年、女孩、吻合/相符、检测、筛查、样本、凶手、DNA 的写法）；③note 总数和分布是否合适、格式是否统一；④标点、数字、专名是否统一；⑤改过的句子有没有引入新问题。只提确实需要改的，每条给完整改法。\n\n${edited}`,
  { label: 'chief', phase: 'Chief', schema: FINDINGS })
const chiefF = chief ? chief.findings : []
const chiefJudged = chiefF.length ? await parallel(JUDGES.map(J => () =>
  agent(`${COMMON}\n\n${J.prompt}\n\n下面是总编辑对全篇（初稿 ${A.draft}，以及以下已改句子）的一致性意见，编号从 0 开始，请逐条判。\n\n已改句子：\n${edited}\n\n意见：\n${fmt(chiefF.map(f => ({ ...f, lens: '总编辑' })))}`,
    { label: `judge:${J.key}:chief`, phase: 'Chief', schema: VERDICT }))) : []
let chiefAcc = []
if (chiefJudged.length === 2 && chiefJudged[0] && chiefJudged[1]) {
  const okA = new Set(chiefJudged[0].verdicts.filter(v => v.accept).map(v => v.index))
  const okB = new Set(chiefJudged[1].verdicts.filter(v => v.accept).map(v => v.index))
  chiefAcc = chiefF.filter((f, i) => okA.has(i) && okB.has(i))
}
return {
  counts: { findings: all.length, accepted: Object.values(accepted).reduce((n, x) => n + x.length, 0), sentencesEdited: Object.keys(editMap).length, chiefFindings: chiefF.length, chiefAccepted: chiefAcc.length },
  edits: editMap,
  accepted,
  rejected: sents.map(s => ({ s, items: bySent[s].filter(f => !(accepted[s] || []).some(a => a.chunk === f.chunk && a.problem === f.problem)).map(f => `${f.lens}/${f.chunk}: ${f.problem}`) })),
  chiefAccepted: chiefAcc,
}
