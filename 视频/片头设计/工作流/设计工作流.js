export const meta = {
  name: 'punk-english-title-logo',
  description: 'Design the "朋克英语" brand mark for the video title page: 5 independent design directions (videos and judging happen afterwards)',
  phases: [
    { title: 'Design', detail: '5 independent design directions, each renders title pages for articles 01/02/03' },
  ],
}

const S = '/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad'
const V = S + '/video'

const CONTEXT = `
## Background
We make bilingual (English/Chinese) intensive-reading videos for Chinese students preparing for the 考研 English exam. Every video starts with a static title page rendered by PIL (Python) from ${V}/title2.py (function frame_title2). Read that file fully first; also look at ${V}/render.py lines 1-30 (font helpers R.EN(size,weight) = Inter variable font, R.ZH(size,weight) = Noto Sans SC variable font; fonts are loaded from the relative path 'fonts/', so your Python must run with cwd=${V} and sys.path containing ${V}).

The current title page: dark green vertical gradient background with a soft central glow; a small teal kicker line "—— 考研英语精读 · No.03 ——" above the title; a huge English title (Inter 900, up to 3 lines, centered) where some words get a yellow→orange gradient glow ('hl') and some words dissolve into light particles from left to right ('ghost'); below it the Chinese title on a yellow (255,214,64) rounded rectangle (radius 18*S) with dark text; and a giant faint watermark article number in the lower right.

## The user's new request (verbatim meaning)
1. Videos must NOT show article numbers any more: remove the "考研英语精读 · No.NN" kicker AND the big watermark number. Re-center the layout vertically after removing them.
2. Add a brand mark / logo of the four characters 「朋克英语」 (means "Punk English", the user's brand). It must look good, like a real trademark/logo. It appears ONLY on this opening title page (nowhere else in the video). The user said it should appear "after/behind the article title" on the opening page — you decide the exact placement that looks best (e.g. below the Chinese title badge, a corner, or a lockup), as long as the article title stays the hero.
3. The four characters 朋克英语 must be exactly those four characters. A small secondary decoration (e.g. a tiny "PUNK ENGLISH" or an icon) is allowed only if it clearly improves the logo; never let it compete with the four characters.

## Hard constraints
- Do NOT modify ${V}/title2.py, ${V}/render.py, ${V}/make_video.py or anything under ${V}/scripts. Work only inside your own directory (given below). Copy title2.py into it and modify the copy.
- Keep the existing title styling (hl gradient glow words, ghost dissolve words, yellow rounded Chinese badge, background) unless a small tweak is needed to harmonise with the logo; the article title must remain the dominant element.
- Your renderer must expose the same signature: frame_title2(no,en,zh,hl,ghost,out,variant=1) (the 'no' argument is now ignored for display) so it can drop in for title2.py later.
- Everything must scale with S (R.S, from env VIDEO_S; S=1 → 1920x1080 draft, S=2 → 3840x2160 final). Multiply every pixel size by S. PIL MaxFilter/MinFilter sizes must be odd (use e.g. 15*S+(S+1)%2).
- Fonts: you may use the fonts already in ${V}/fonts (Inter.ttf, NotoSansSC.ttf) or download ONE OR TWO OFL-licensed fonts from the Google Fonts GitHub repo (https://raw.githubusercontent.com/google/fonts/main/ofl/<family>/<File>.ttf — e.g. zcoolqingkehuangyou/ZCOOLQingKeHuangYou-Regular.ttf, zcoolkuaile/ZCOOLKuaiLe-Regular.ttf, zhimangxing/ZhiMangXing-Regular.ttf, mashanzheng/MaShanZheng-Regular.ttf, longcang/LongCang-Regular.ttf, liujianmaocao/LiuJianMaoCao-Regular.ttf; check the directory listing via https://api.github.com/repos/google/fonts/contents/ofl/<family> if a filename 404s). Save downloaded fonts into YOUR directory (not ${V}/fonts) and load them by absolute path. Verify every one of 朋克英语 actually has a glyph in the font (render each char and compare against the .notdef box / use fontTools cmap) — a missing glyph is a failure.
- Deterministic output (seed any randomness).
- Render these three test title pages at S=1 into your directory (and LOOK at each PNG with the Read tool, fix anything ugly, overlapping, cut off or unbalanced before returning):
  t01.png: frame_title2('01','The Robber Who Thought Lemon Juice Made Him Invisible','以为柠檬汁能隐身的劫匪',['Lemon','Juice'],['Invisible'],out)
  t02.png: frame_title2('02','The Truth About One Marshmallow','一颗棉花糖的真相',['Marshmallow'],[],out)
  t03.png: frame_title2('03','The Doctor Who Drank Bacteria to Win an Argument','喝下细菌的医生',['Drank','Bacteria'],['Argument'],out)
  Then also run once with VIDEO_S=2 to render t03_4k.png and confirm it works (no exceptions, logo crisp, proportions identical to the S=1 version).
- Also save a close-up crop of just the logo from t03.png as logo_crop.png (padding around it) so judges can inspect detail.
`

const DIRECTIONS = [
  { key: 'A_stamp', brief: 'Punk rubber-stamp / Chinese seal (印章) hybrid: the four characters in a slightly rotated stamp with distressed/rough ink texture (deterministic noise eroding the ink), in a punk red or hot magenta, like a seal pressed onto a poster. Think of how a seal sits at the end of calligraphy — it naturally reads as a brand signature.' },
  { key: 'B_neon', brief: 'Neon-sign / glitch: the four characters as glowing neon tubes (hot pink or electric cyan) with a subtle RGB-split glitch offset and soft bloom, like a sign in a punk club. Keep it classy and readable, not noisy.' },
  { key: 'C_graffiti', brief: 'Graffiti / brush: a wild brush or graffiti-style Chinese font (e.g. Zhi Mang Xing, Liu Jian Mao Cao, Ma Shan Zheng) in a bold punk colour with a few deterministic spray-paint splatter dots or a drip, slightly tilted, like a tag sprayed onto the poster.' },
  { key: 'D_wordmark', brief: 'Premium bold wordmark lockup: a heavy blocky display font (e.g. ZCOOL QingKe HuangYou or Noto Sans SC 900) with a small punk icon (lightning bolt, safety pin, or a spiked/star burst) forming a compact logo lockup — like the logo of a cool modern education brand. Clean, confident, high-end; colours harmonised with the existing yellow/teal/green palette.' },
  { key: 'E_ransom', brief: 'Punk zine collage / ransom-note: each of the four characters on its own cut-out paper or tape piece (different colour blocks, slight different rotations, black/yellow/hot-pink/white), like a 1970s punk flyer, placed as a compact sticker cluster. Must still read instantly as 朋克英语 and look intentional, not messy.' },
]

const DESIGN_SCHEMA = {
  type: 'object',
  properties: {
    key: { type: 'string' },
    dir: { type: 'string' },
    script: { type: 'string', description: 'absolute path of your renderer .py' },
    t01: { type: 'string' }, t02: { type: 'string' }, t03: { type: 'string' }, t03_4k: { type: 'string' }, logo_crop: { type: 'string' },
    fonts: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, family: { type: 'string' }, license: { type: 'string' }, source_url: { type: 'string' } }, required: ['file', 'family', 'license'] } },
    placement: { type: 'string' },
    description_zh: { type: 'string', description: '2-3 sentences in simple Chinese describing the look, for the end user' },
    self_critique: { type: 'string' },
  },
  required: ['key', 'dir', 'script', 't01', 't02', 't03', 't03_4k', 'logo_crop', 'fonts', 'placement', 'description_zh', 'self_critique'],
}

phase('Design')
const designs = (await parallel(DIRECTIONS.map(d => () => agent(
  `You are a senior brand/motion graphic designer. ${CONTEXT}

## Your design direction: ${d.key}
${d.brief}

Your working directory: ${V}/logo/${d.key}/ (create it). Put your renderer at ${V}/logo/${d.key}/title_logo.py and all outputs there.
Iterate visually: render, Read the PNG, critique honestly (balance, hierarchy, whitespace, colour harmony with the dark green background and yellow badge, legibility of 朋克英语 at phone size, does it look like a real logo?), improve, repeat at least 2-3 times. Return the structured result.`,
  { label: `design:${d.key}`, phase: 'Design', schema: DESIGN_SCHEMA }
)))).filter(Boolean)

log(`${designs.length} designs rendered`)
return { designs }
