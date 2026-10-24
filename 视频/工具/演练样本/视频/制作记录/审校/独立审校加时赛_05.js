export const meta = {
  name: 'review-05-tiebreak',
  description: 'Tie-break for article 05 review: consolidate singly-accepted variants per sentence, then two fresh judges accept or reject the consolidated version',
  phases: [
    { title: 'Consolidate', detail: 'one editor per split sentence' },
    { title: 'Judge', detail: 'two fresh judges per consolidated sentence' },
  ],
}
const A = args
const COMMON = `你在为一个考研英语精读视频系列做译文审校（逐词对照：每句英文拆成若干 chunk，每个 chunk 再分成对齐组"英文组 => 中文组"，从上往下连读中文必须是通顺整句）。这是教材，要求精准、地道、通顺；用户亲笔改过的译法永远优先。
必读：风格总纲 ${A.style}；踩坑总表 ${A.pit}；第04篇制作记录 ${A.rec04}（用户没采用第二轮审校的大量改动，而是自己在第一稿上改了8处：不要为改而改）；第05篇文章 ${A.article}（"史实与来源"里有硬性译法要求）。
硬约束：英文一个字母都不能改；重点词写成 **中文**(english)，集合固定；原文没有的补充放全角（）并需用户认可；note 全角（）包住、10–40 字、只讲难点；中文全角标点；数字写法跟英文一致。
本轮的数据文件：${A.split}（JSON 数组，每项是一句：orig=初稿，base=已经采纳了"两位裁判都同意的意见"之后的当前版本，items=这一句的全部审校意见，每条带两位裁判"甲（忠实与规则）""乙（通顺与教学）"的判定和理由，bothAccepted=两位都采纳的意见编号）。`

const EDIT = {
  type: 'object',
  properties: {
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
    included: { type: 'string', description: '相对 base 加进了哪些意见（编号）及理由；没加的为什么不加' },
  },
  required: ['chunks', 'included'],
}
const VERD = { type: 'object', properties: { accept: { type: 'boolean' }, reason: { type: 'string' } }, required: ['accept', 'reason'] }

const SENTS = A.sentences
const results = await pipeline(SENTS,
  s => agent(`${COMMON}\n\n你是 ${s} 的合并编辑。上一轮的问题：几位审校员对同一个问题给出了略有不同的改法，两位裁判各自挑了不同的版本，结果按"两位都采纳同一条"的规则，大家都同意要改的地方也没改成（例如 S11 的 before 下面放"之后才"，六位审校员都指出、两位裁判都同意必须改，却因为版本不同没有落实）。\n请读数据文件里 ${s} 这一项：以 base 为起点，逐条看只被一位裁判采纳的意见——如果另一位裁判不采纳的理由只是"与另一条重复/冲突、选了另一个版本、note 写法之争"，而对实质改动是同意的，就把这个实质改动合并进来（在冲突的版本之间，按两位裁判理由里共同认可的部分取舍；note 之争取更保守、更短的写法）；如果另一位裁判是从实质上反对（认为问题不存在、或改法更差），就不加。两位都不采纳的一律不加。\n输出这一句合并后的全部 chunk（按顺序，没改的原样照抄）。英文组按顺序拼起来必须与原句英文一字不差（包括标点和 ** 标记）；每个加粗英文词在同一 chunk 的中文里有 **中文**(english)。`,
    { label: `consolidate:${s}`, phase: 'Consolidate', schema: EDIT }),
  (ed, s) => {
    if (!ed) return null
    const txt = ed.chunks.map((c, k) => `${s}-${k + 1}  ` + c.align.map(g => `${g.en} => ${g.zh}`).join('  |  ') + (c.note ? `\n      note: ${c.note}` : '')).join('\n')
    const J = [
      { key: '忠实与规则', p: '你是裁判甲（忠实与规则）：先尝试反驳——合并版是否比 base 更忠实于英文、更符合风格总纲和 01–04 定稿先例、更符合用户口味？有没有引入新问题（添加信息、词性错、英文被改、重点词丢失、和别的句子不统一）？' },
      { key: '通顺与教学', p: '你是裁判乙（通顺与教学）：先尝试反驳——合并版连读是否比 base 更通顺地道、学生是否更容易对上英文、note 是否更有用？有没有为改而改、字数变多而没有收益？' },
    ]
    return parallel(J.map(j => () => agent(`${COMMON}\n\n${j.p}\n\n这是 ${s}。请读数据文件里 ${s} 的 base 和 items（含上一轮两位裁判的理由），再看下面的"合并版"。合并版明显更好就采纳；拿不准、或只是换个说法，就不采纳（保留 base）。\n\n合并版：\n${txt}\n\n合并编辑的说明：${ed.included}`,
      { label: `judge2:${j.key}:${s}`, phase: 'Judge', schema: VERD })))
      .then(vs => ({ s, ed, txt, vs, accept: vs.every(v => v && v.accept) }))
  })
return results.filter(Boolean)
