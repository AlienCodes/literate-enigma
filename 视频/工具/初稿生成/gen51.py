import json,re,glob,os
# 第51篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-05 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；不用破折号（T36）；形容词的“的”进粗体（T38）。
S=[
(1,[[[("OK,","OK，"),("often said to be the planet's most frequently spoken word,","常被说成是全世界说得最多的词，"),("began as a newspaper **gag**.","起初只是报纸上的一个**噱头**(gag)。")],
     "（often said to be…：过去分词短语作插入语，补充说明 OK；\nbegin as…：起初是……）"]]),
(1,[[[("From 1838","从1838年起，"),("**abbreviations**","**缩写**(abbreviations)"),("were all the **vogue** in Boston's papers,","在波士顿各报**风靡**(vogue)一时，")],
     "（be all the vogue：风靡一时，非常流行）"],
    [[("and the **craze**","这股**热潮**(craze)"),("turned **comic**","变得**滑稽**(comic)起来，"),("through **deliberate** **misspellings**:","靠的是**故意的**(deliberate)**错拼**(misspellings)：")],
     "（turn＋形容词：变得……；\nthrough…：借助……）"],
    [[("O.W. for 'oll wright',","用 O.W. 代表 'oll wright'，"),("K.Y. for 'know yuse'.","用 K.Y. 代表 'know yuse'。")],
     "（'oll wright'：故意拼错的 all right；\n'know yuse'：故意拼错的 no use）"]]),
(1,[[[("The **humour**","其中的**幽默**(humour)"),("lay in","来自"),("the **persona** of an **uneducated** bumpkin.","一个**没受过教育的**(uneducated)乡巴佬**人设**(persona)。")],
     "（lie in…：在于……；\nthe persona of…：of 结构，……的人设）"]]),
(2,[[[("On 23 March 1839","1839年3月23日，"),("a Boston Morning Post **satire**","《波士顿晨邮报》的一篇**讽刺文章**(satire)")]],
    [[("took a **swipe** at","**挖苦**(swipe)了"),("a **contemporary**, the Providence Journal,","它的**同行**(contemporary)《普罗维登斯日报》，")],
     "（take a swipe at…：抨击，挖苦；\nthe Providence Journal：同位语，补充说明 a contemporary）"],
    [[("over a **mock** society","话题是一个**恶搞的**(mock)社团，"),("**parodying** an **ordinance** against ringing dinner bells.","它**戏仿**(parodying)一项禁止敲开饭铃的**法令**(ordinance)。")],
     "（over…：就……，关于……；\nparodying…：现在分词短语作后置定语，修饰 society）"]]),
(2,[[[("It carried","文中出现了"),("the first known 'o.k.',","已知最早的 'o.k.'，"),("**glossed** as 'all correct'.","并**注明**(glossed)意为 'all correct'。")],
     "（glossed as…：过去分词短语作后置定语，修饰 'o.k.'，\n被注释为……）"]]),
(2,[[[("The letters","这两个字母"),("stood for","代表的是"),("a **knowingly** **illiterate** 'oll korrect'.","**有意**(knowingly)写成**文盲**(illiterate)拼法的 'oll korrect'。")],
     "（stand for：代表；\n'oll korrect'：故意拼错的 all correct）"]]),
(2,[[[("The **presumed** writer","一般**推定的**(presumed)作者"),("was","是"),("the editor, Charles Gordon Greene.","该报编辑查尔斯·戈登·格林。")],
     "（Charles Gordon Greene：同位语，补充说明 the editor）"]]),
(3,[[[("**Partisan** politics","**党派**(Partisan)政治"),("**propagated** the letters nationwide.","把这两个字母**传遍**(propagated)全国。")],
     "（propagate…nationwide：把……传遍全国）"]]),
(3,[[[("In 1840","1840年，"),("Martin Van Buren, the **incumbent** president,","**在任**(incumbent)总统马丁·范布伦"),("sought **re-election**.","寻求**连任**(re-election)。")],
     "（the incumbent president：同位语，补充说明 Martin Van Buren）"]]),
(3,[[[("His New York **backers**,","他在纽约的**拥护者**(backers)"),("punning on his nickname 'Old Kinderhook',","拿他的绰号 'Old Kinderhook' 玩双关，"),("after his **birthplace**,","这个绰号得名于他的**出生地**(birthplace)，")],
     "（punning on…：现在分词短语作状语，拿……玩双关；\nafter his birthplace：以他的出生地金德胡克命名）"],
    [[("formed the Democratic O.K. Club,","他们成立了民主党 O.K. 俱乐部，"),("making the letters","让这两个字母"),("a **double-meaning** **slogan**.","成了一句**一语双关的**(double-meaning)**口号**(slogan)。")],
     "（making…：现在分词短语作状语，表示结果；\nmake A B：让 A 成为 B）"]]),
(3,[[[("That November","那年11月，"),("William Henry Harrison","威廉·亨利·哈里森"),("**unseated** him,","把他**赶下台**(unseated)，"),("234 **electoral** votes to 60.","**选举人**(electoral)票为234张对60张。")],
     "（234 electoral votes to 60：选举人票234张对60张）"]]),
(4,[[[("On 30 March 1840","1840年3月30日，"),("the New York Morning Herald","《纽约先驱晨报》"),("printed a **fabricated** **smear**:","登出一则**捏造的**(fabricated)**抹黑**(smear)消息：")]],
    [[("the former president Andrew Jackson,","前总统安德鲁·杰克逊，"),("a **supposedly** **inept** speller,","**据说**(supposedly)拼写**笨拙**(inept)，"),("had marked **paperwork** O.K.,","曾在**公文**(paperwork)上批 O.K.，"),("for 'Ole Kurrek'.","代表 'Ole Kurrek'。")],
     "（a supposedly inept speller：同位语，补充说明 Andrew Jackson；\nmark A B：在 A 上批注 B；\n'Ole Kurrek'：故意拼错的 all correct）"]]),
(4,[[[("Jackson","其实杰克逊"),("spelled **reasonably** well","拼写得**还算**(reasonably)不错，"),("and never marked documents O.K.","也从没在文件上批过 O.K.。")]]]),
(4,[[[("Within about twenty years,","大约二十年内，"),("people","人们"),("did so **in earnest**.","就**当真**(in earnest)这样批了。")],
     "（do so：这样做，指在文件上批 O.K.）"]]),
(4,[[[("The **bogus** **notation**","这个**子虚乌有的**(bogus)**批注**(notation)"),("was merely **premature**.","不过是出现得**过早**(premature)。")]]]),
(5,[[[("Rival stories","与之竞争的说法"),("offered **exotic** **pedigrees**:","给出了种种**异域的**(exotic)**来历**(pedigrees)，"),("Choctaw 'okeh'","比如乔克托语的 'okeh'"),("and Greek 'ola kala'.","和希腊语的 'ola kala'。")]]]),
(5,[[[("**Authoritative** dictionaries","**权威**(Authoritative)词典"),("favoured Choctaw as late as 1961.","直到1961年还倾向于乔克托语一说。")],
     "（as late as…：直到……还）"]]),
(5,[[[("In 1963–64","1963至1964年，"),("the linguist Allen Walker Read","语言学家艾伦·沃克·里德")]],
    [[("**excavated** the **neglected** Boston **provenance** from **archival** newspapers","从**档案**(archival)报纸中**发掘**(excavated)出长期被**忽视的**(neglected)波士顿**起源**(provenance)，")],
     "（excavate A from B：从 B 中发掘出 A）"],
    [[("in six **influential** American Speech articles.","这些发现发表在《美国语言》杂志的六篇**影响深远的**(influential)文章里。")],
     "（in six … articles：in 结构作状语，指成果发表在六篇文章中）"]]),
(5,[[[("Most dictionaries now","如今大多数词典都"),("**embrace**","**采纳**(embrace)了"),("his **derivation**,","他的**词源**(derivation)解释，"),("a pedigree of bad spelling and dinner-bell satire.","那是一段由错误拼写和开饭铃讽刺文构成的来历。")],
     "（a pedigree of…：同位语，补充说明 derivation）\n"
     "（简述：1838年起，波士顿各报流行故意拼错的滑稽缩写。\n"
     "1839年《波士顿晨邮报》的一篇讽刺文章首次用了 o.k.，代表故意拼错的 all correct。\n"
     "1840年范布伦竞选连任，支持者借他的绰号 Old Kinderhook 成立 O.K. 俱乐部，让这两个字母传遍全国。\n"
     "同年一则捏造的消息说杰克逊在公文上批 O.K.，约二十年内人们真的这样批了。\n"
     "乔克托语、希腊语等来源说法曾经流行，里德从档案报纸中考证出波士顿起源，如今多数词典都采纳了他的说法。）"]]),
]
CONF={}
out={"no":"51","title_en":"The Joke That Became OK","title_zh":"OK 原本是个玩笑","title_fx":{"hl":["Joke","OK"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Boston":"波士顿","Boston Morning Post":"《波士顿晨邮报》","Providence Journal":"《普罗维登斯日报》","Charles Gordon Greene":"查尔斯·戈登·格林","Martin Van Buren":"马丁·范布伦","New York":"纽约","Democratic O.K. Club":"民主党 O.K. 俱乐部","William Henry Harrison":"威廉·亨利·哈里森","New York Morning Herald":"《纽约先驱晨报》","Andrew Jackson":"安德鲁·杰克逊","Jackson":"杰克逊","Choctaw":"乔克托语","Greek":"希腊语","Allen Walker Read":"艾伦·沃克·里德","American Speech":"《美国语言》"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
