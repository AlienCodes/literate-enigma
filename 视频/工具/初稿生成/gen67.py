import json,re,glob,os
# 第67篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-08 重点词中文沿用文章定稿（铁律）；中英尽量对齐；不用破折号（T36）；三项并列加牛津逗号（T18）。
S=[
(1,[[[("Marcel Ravidat, 18,","18岁的马塞尔·拉维达")],
     "（18：插入语，补充说明年龄）"],
    [[("was on a **woodland** **stroll** near Montignac with Robot, his **canine** companion,","带着他的**犬类**(canine)伙伴罗伯特在蒙蒂尼亚克附近的**林地**(woodland)里**散步**(stroll)，")],
     "（his canine companion：同位语，补充说明 Robot）"],
    [[("when it began","这时罗伯特开始"),("**sniffing** at a **hollow** left by a **toppled** tree.","在一棵**倒伏**(toppled)的树留下的**坑洞**(hollow)边**嗅来嗅去**(sniffing)。")],
     "（it 指 Robot；\nleft by a toppled tree：过去分词短语作后置定语，修饰 hollow）"]]),
(1,[[[("On 12 September 1940","1940年9月12日，"),("he came back with three other boys","他带着另外三个男孩回到这里，")]],
    [[("for an **adventurous** **excursion**,","来了一次**富于冒险**(adventurous)的**出游**(excursion)，")],
     "（for：表示目的）"],
    [[("and the four **explorers**","四个**探险者**(explorers)"),("climbed down into the **darkness**.","爬进了**黑暗**(darkness)之中。")]]]),
(2,[[[("In later **retellings**,","在后来的**复述**(retellings)中，")]],
    [[("Ravidat","拉维达"),("**embroidered** his **anecdote** with a **dramatic** twist.","给这段**轶事**(anecdote)**添油加醋**(embroidered)，加入了一个**戏剧性**(dramatic)的转折。")],
     "（embroider A with B：用 B 给 A 添油加醋）"]]),
(2,[[[("Robot, he said,","他说，罗伯特"),("had fallen into the cave.","掉进了洞里。")],
     "（he said：插入语；\nhad fallen：过去完成时，掉洞在讲述之前）"]]),
(2,[[[("That **fanciful**","这个**离奇**(fanciful)的"),("**mishap**","**意外**(mishap)"),("is a **fabrication**.","纯属**编造**(fabrication)。")]]]),
(2,[[[("The animal","那只狗"),("only nosed about the hole,","只是在洞口嗅了嗅，")],
     "（nose about：到处嗅）"],
    [[("and the **pivotal** **initiative**","**关键**(pivotal)的**主动行动**(initiative)"),("was the boys' own.","完全出自几个男孩。")],
     "（the boys' own：男孩们自己的，own 后省略了 initiative）"]]),
(2,[[[("**Ironically**,","**讽刺的是**(Ironically)，"),("the invented fall","虚构的那一跤"),("made the dog the hero of the story.","让狗成了故事的主角。")],
     "（make A B：使 A 成为 B）"]]),
(3,[[[("Some 680 painted figures","约680个彩绘形象"),("and 1,500 **engravings**","和1,500幅**雕刻图案**(engravings)"),("cover the rock.","布满岩壁。")],
     "（some：大约，用在数字前）"]]),
(3,[[[("The **artwork**","这些**艺术作品**(artwork)"),("is usually dated to between 17,000 and 22,000 years ago;","通常被认为距今1.7万至2.2万年；")],
     "（be dated to：年代被断定为）"],
    [[("its **creators**,","它们的**创作者**(creators)"),("our distant **ancestors**,","是我们遥远的**祖先**(ancestors)，"),("lived in **antiquity**.","生活在**远古**(antiquity)时代。")],
     "（our distant ancestors：同位语，补充说明 creators）"]]),
(3,[[[("Horses, **bulls**, and stags","马、**公牛**(bulls)和雄鹿"),("are among the animals **depicted** in **pigments** on the **murals**.","都是**壁画**(murals)上用**颜料**(pigments)**描绘**(depicted)的动物。")],
     "（be among：是……之一；\ndepicted in pigments on the murals：过去分词短语作后置定语，修饰 animals）"]]),
(3,[[[("The paintings'","这些画作的"),("**fragility**","**脆弱**(fragility)"),("soon became clear.","很快就显现出来。")]]]),
(4,[[[("Lascaux opened to the public on 14 July 1948,","1948年7月14日，拉斯科向公众开放，")]],
    [[("and **tourism**","**旅游业**(tourism)"),("brought","带来了"),("an **influx** of about 1,200 visitors a day.","每天约1,200名游客的**涌入**(influx)。")],
     "（an influx of A：A 的涌入）"]]),
(4,[[[("The **throng**","**人群**(throng)"),("**exhaled** carbon **dioxide**","**呼出**(exhaled)**二氧化碳**(dioxide)，")]],
    [[("and added heat, **humidity**, and **contaminants**,","带来热量、**湿气**(humidity)和**污染物**(contaminants)，")]],
    [[("and the **deterioration** of the paintings","壁画的**退化**(deterioration)"),("became plain to see.","变得肉眼可见。")],
     "（plain to see：显而易见）"]]),
(4,[[[("In 1963","1963年，"),("the site closed to the public,","洞穴对公众关闭，")]],
    [[("followed by **restoration**","随后进行了**修复**(restoration)，"),("and daily **inspection**.","并开始每日**检查**(inspection)。")],
     "（followed by…：过去分词短语，表示随后发生的事）"]]),
(5,[[[("Lascaux joined UNESCO's World Heritage List in 1979,","1979年，拉斯科被列入联合国教科文组织《世界遗产名录》；")]],
    [[("and Lascaux II, a **meticulously** made **partial** **facsimile**, opened in 1983.","1983年，**精心**(meticulously)制作的**局部**(partial)**复制品**(facsimile)拉斯科二号开放。")],
     "（a meticulously made partial facsimile：同位语，\n补充说明 Lascaux II）"]]),
(5,[[[("A white **fungus** **invaded** the walls in a 2001 **outbreak**,","2001年，一种白色**真菌**(fungus)**爆发**(outbreak)，**侵入**(invaded)洞壁；")],
     "（in a 2001 outbreak：在2001年的一次爆发中）"],
    [[("and black **stains** spread after chemical treatment.","化学处理后，黑色**污斑**(stains)蔓延开来。")]]]),
(5,[[[("Lascaux IV opened in December 2016.","2016年12月，拉斯科四号开放。")]]]),
(5,[[[("**Admirers** now","如今**仰慕者**(Admirers)"),("meet the bulls only in a **recreation**,","只能在**复原品**(recreation)中见到那些公牛，")],
     "（only in…：只在……中）"],
    [[("the originals","原洞"),("being **inaccessible** to them.","对他们来说**无法进入**(inaccessible)。")],
     "（the originals being…：独立主格，补充说明原因）\n"
     "（简述：1940年，18岁的马塞尔·拉维达带狗罗伯特在蒙蒂尼亚克附近散步，狗在倒伏的树留下的坑洞边嗅来嗅去；9月12日，他和另外三个男孩爬进了洞里。\n"
     "拉维达后来说狗掉进了洞里，这是编造，关键的行动出自男孩们。\n"
     "洞里约有680个彩绘形象和1,500幅雕刻，通常认为距今1.7万至2.2万年。\n"
     "拉斯科1948年开放后，每天约1,200名游客带来二氧化碳、热量和湿气，壁画退化，1963年洞穴关闭。\n"
     "1979年拉斯科列入世界遗产，1983年复制品拉斯科二号开放，2001年洞壁爆发白色真菌，2016年拉斯科四号开放，如今游客只能看复制品。）"]]),
]
G={}
DZ={}
CONF={"合组":G,"对齐":DZ}
out={"no":"67","title_en":"The Cave Found by a Dog","title_zh":"几个少年和一只狗发现的洞穴","title_fx":{"hl":["Cave","Dog"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Marcel Ravidat":"马塞尔·拉维达","Ravidat":"拉维达","Montignac":"蒙蒂尼亚克","Robot":"罗伯特","Lascaux":"拉斯科","UNESCO":"联合国教科文组织","World Heritage List":"世界遗产名录","Lascaux II":"拉斯科二号","Lascaux IV":"拉斯科四号"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
