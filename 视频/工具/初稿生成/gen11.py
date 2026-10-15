import json,re,glob,os
# 第11篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-10-15 程序打底：英文、重点词与文章逐字核对，重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式（“的”“了”进粗体）。
# 08–10 用户定下的规矩一开始就照做：短语型用法整体标（T22：adjacent to、heralded … as、withdrew from、turned the tide），
# 习语整体标（用户 2026-10-15：“turn the tide……单独用一个 tide 不就是潮汐吗……要把这个整体做出来”）：撞词也保留，写进 allow_clash。
# 被隔开的意思每处都标（T23：与……紧邻、把……誉为），过去时“了”，顺着英文语序排（字不变），结尾解说（T28）。
# 2026-10-15 用户看 1080p 草稿后的 16 条（制作记录/11_待改清单.md）已全部改进来（T10 原样）。
# 2026-10-15 用户要求省 token：不再派多视角审校，程序核查 + 我只看程序拿不准的几处。
S=[
(1,[[[("Go is said to","据说，围棋"),("allow","所允许出现的"),("more **configurations** than the universe has **atoms**,","**布局**(configurations)（数量），比宇宙中的**原子**(atoms)还要多，")]],
    [[("a **daunting**","这是一项**艰巨的**(daunting)"),("**computational** challenge.","**计算**(computational)挑战。")],
     "（be said to do：据说……；a daunting … challenge：同位语，说明前面整句）"]]),
(1,[[[("In October 2015","2015年10月，"),("DeepMind's AlphaGo","DeepMind 的 AlphaGo"),("reached a **milestone**,","达成了一个**里程碑**(milestone)，")]],
    [[("becoming","成为"),("the first program to beat a professional on a full board without a **handicap**.","首个在全尺寸棋盘上不**让子**(handicap)击败职业棋手的程序。")],
     "（becoming…：现在分词短语，补充说明这个里程碑；\nthe first program to do：第一个做……的程序）"]]),
(1,[[[("In March 2016","2016年3月，"),("its **opponent** in a **televised** Seoul **showdown**","在首尔一场**电视转播的**(televised)**对决**(showdown)中，它的**对手**(opponent)")]],
    [[("was Lee Sedol,","是李世石，"),("a South Korean **strategist**","一个韩国**战略家**(strategist)（围棋大师），"),("with 18 international titles.","拥有18个国际冠军头衔。")]]]),
(2,[[[("In game two, on 10 March,","第二局于3月10日进行，"),("AlphaGo's 37th move","AlphaGo 的第37手"),("was a shoulder hit,","是一记肩冲。")]],
    [[("a **tactic**","这种**招数/手段**(tactic)，是"),("placing a stone","将一枚棋子下在"),("**adjacent to** an opponent's on the **diagonal**.","**与**(adjacent to)对方棋子的**斜对角**(diagonal)**相邻**(adjacent to)的地方。")],
     "（shoulder hit：肩冲，围棋术语；\na tactic placing…：同位语，解释 shoulder hit，placing… 作后置定语）"]]),
(2,[[[("On the **grid**'s fifth line,","在**网格**(grid)（方格构成的网状 - 指 棋盘）第五线上落子，"),("it","这"),("was hardly **orthodox**.","几乎不能算是**正统**(orthodox)下法。")]]]),
(2,[[[("Commentators","解说员"),("found","觉得"),("the **unexpected** **placement**","这步**出人意料的**(unexpected)**落子**(placement)\n{{（把人或物放到合适位置）|placement}}"),("**bizarre**;","**十分怪异**(bizarre)；")]],
    [[("one","其中一人还"),("took it for a mistake.","以为是失误。")],
     "（find + 宾语 + 形容词：觉得……怎么样；take A for B：把A当成B）"]]),
(2,[[[("Lee","李世石"),("left the room,","离开了对局室，")]],
    [[("his **pause** for **deliberation**","他这次**暂停**(pause)**思考**(deliberation)"),("lasting over ten minutes.","持续了十多分钟。")],
     "（his pause … lasting…：独立主格，= and his pause … lasted…）"]]),
(3,[[[("DeepMind's **diagnostic** tools","DeepMind 的**诊断**(diagnostic)工具"),("showed","显示，")]],
    [[("AlphaGo","AlphaGo"),("had put the **odds** of a human playing that stone","曾把人类下出这一手的**概率**(odds)"),("at one in 10,000,","估算为万分之一，")]],
    [[("a **staggering** **rarity**.","**惊人的**(staggering)**罕见**(rarity)。")],
     "（put the odds of … at …：把……的概率估算为……；\na staggering rarity：同位语，补充说明这个概率）"]]),
(3,[[[("AlphaGo had first","AlphaGo 起初先"),("learned to **imitate**","学会**模仿**(imitate)"),("strong **amateurs** online,","网上实力很强的**业余者**(amateurs)的下法，")]],
    [[("then","随后，"),("**sharpened** its play over tens of millions of **simulated** games against itself.","在数千万盘的自我对弈**模拟**(simulated)中，它**磨砺了**(sharpened)棋力。")]]]),
(3,[[[("Lee","李世石"),("later","后来"),("**acknowledged**","**承认了**(acknowledged)"),("the stone's **originality** and beauty.","这一手的**独创性**(originality)和美感。")]]]),
(4,[[[("The fourth game, on 13 March,","3月13日的第四局，"),("**reversed** the roles in **neat** **symmetry**.","以**巧妙的**(neat)**对称**(symmetry)，**互换了**(reversed)双方的角色。")]]]),
(4,[[[("Lee's 78th move","李世石的第78手"),("**turned the tide**,","**扭转了局势**(turned the tide)，")]],
    [[("and many professionals","许多职业棋手"),("**heralded** it **as**","**把**(heralded as)它**誉为**(heralded as)"),("**divine**.","**神之一手**(divine)。")],
     "（herald A as B：把A誉为B；\ndivine：神的，神妙的，“神之一手”指围棋中绝妙的一手）"]]),
(4,[[[("DeepMind's team","DeepMind 团队"),("**computed**","**算出了**(computed)")]],
    [[("a professional's **likelihood** of finding it:","职业棋手找到这一手的**可能性**(likelihood)："),("about one in 10,000.","约为万分之一。")]]]),
(4,[[[("Lee's only win","李世石唯一的胜局，")]],
    [[("was","是"),("a **consolation** amid AlphaGo's **overwhelming** 4–1 victory.","AlphaGo 4比1**压倒性的**(overwhelming)胜利中的一点**安慰**(consolation)。")],
     "（amid：在……之中）\n（consolation：通常作名词，\n指失望、悲伤或遭受打击时得到的安慰和心理宽慰）"]]),
(5,[[[("In November 2019","2019年11月，"),("Lee","李世石"),("**withdrew from** the professional **circuit**,","**退出了**(withdrew from)职业**巡回赛**(circuit)（退役），")]],
    [[("a **farewell** he tied","他把这次**告别**(farewell)"),("to","归因于"),("AI's **unrivalled** **dominance**.","人工智能**无可匹敌的**(unrivalled)**统治地位**(dominance)。")],
     "（a farewell he tied to…：同位语，说明前面整件事；\ntie A to B：把A和B联系起来，这里指把A归因于B）"]]),
(5,[[[("Calling AI an **invincible** **entity**,","称人工智能是**不可战胜的/无敌的**(invincible)**存在**(entity)，"),("he said","他说，"),("the **summit** was beyond him.","那个**顶峰**(summit)已非他所能企及。")],
     "（Calling…：现在分词短语作伴随状语；call A B：称A为B；\nbe beyond sb：超出某人的能力）"]]),
(5,[[[("Yet","然而，"),("his one win came from a stone","他唯一的一场胜局，却源自一着棋。")]],
    [[("whose odds, by DeepMind's figures,","根据 DeepMind 的数据，这手棋的胜率，")]],
    [[("were as **slim** as those of AlphaGo's **audacious** shoulder hit.","和 AlphaGo 那次**大胆**(audacious)一样**极低/渺茫/非常微小**(slim)。")],
     "（whose…：定语从句，修饰 a stone；by DeepMind's figures：插入语；\nas slim as those of…：those = the odds）\n（结局：第二局，AlphaGo 下出了人类只有万分之一可能会下的第37手；\n第四局，李世石也下出了职业棋手只有万分之一可能找到的第78手，\n并靠它赢下了五局里唯一的一局。李世石退役时说人工智能无法击败，\n可他唯一的胜利，恰恰来自一手和 AlphaGo 的肩冲一样罕见、\n一样大胆的棋：人类赢机器，用的正是机器赢人类的方式。）"]]),
]
CONF={"短语":{
 "S7 pause … for":"for deliberation 表目的（为思考而暂停），pause 本身就是“暂停”，意思不靠 for 产生（同 09 pleas for 的判法）",
 "S8 odds … of":"odds of sth 里 of 引出概率的内容，odds 本身就是“概率”，意思不靠 of 产生（同 10 involvement in 的判法）",
 "S13 likelihood … of":"likelihood of doing 里 of 引出可能发生的事，likelihood 本身就是“可能性”，意思不靠 of 产生（同 10 involvement in 的判法）",
 "S15 farewell … to":"to 属于 he tied … to（tie A to B），与 farewell 无关，本句不是 bid farewell to",
 "S17 slim … as":"as slim as 是 as … as 比较结构（和……一样渺茫），不是 slim 的固定搭配；中文“和……一样渺茫”与 slim 同组（T13）"},
 "口述":{"S6-2 觉得":"note 里“find + 宾语 + 形容词：觉得……怎么样”是句型说明本身，不是语音输入多出来的词"},
 "数字":{"S8-2 10,000":"one in 10,000 中文按习惯写“万分之一”（分数），读法 one in ten thousand","S13-2 10,000":"同 S8：about one in 10,000 → 约为万分之一"},
 "是的":{"S16-1 是**无法击败的**":"“是 + 无法击败的存在”是“是 + 定语 + 名词”（称A为B），不是“是……的”表语句式"}}
out={"no":"11","title_en":"Move 37","title_zh":"第37手","title_fx":{"hl":["37"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"结局","allow_clash":["turned the tide"],"高亮按实际开口":True}   # T28
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
