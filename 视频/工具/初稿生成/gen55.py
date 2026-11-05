import json,re,glob,os
# 第55篇初稿（逐词对照）：S = [(段, [chunk, ...])]，chunk = ([(英文组, 中文组), ...], 可选 note)
# 2026-11-05 重点词中文沿用文章定稿（铁律），只按《翻译风格》调格式；短语型用法整体标（T22）；不用破折号（T36）；形容词的“的”进粗体。
S=[
(1,[[[("Nearly 1,900 years after its **completion**, in about AD 125–128,","万神殿约于公元125至128年**竣工**(completion)，近1,900年后的今天，")],
     "（its completion：its 指 the Pantheon；\nin about AD 125–128：插入语，补充竣工的年代）"],
    [[("the Pantheon's **dome**","它的**穹顶**(dome)"),("still **crowns**","依然**高踞**(crowns)于"),("the **vast** **chamber** below.","下方**宏大的**(vast)**殿堂**(chamber)之上。")],
     "（crown：位于……顶部，高踞……之上；\nbelow：副词作后置定语，修饰 chamber）"]]),
(1,[[[("About 43 metres in **diameter**,","穹顶**直径**(diameter)约43米，"),("it remains","至今仍是"),("the world's largest","世界上最大的"),("unreinforced concrete dome.","无钢筋混凝土穹顶。")],
     "（About 43 metres in diameter：形容词短语作状语，说明穹顶的大小；\nunreinforced：没有用钢筋加固的）"]]),
(1,[[[("It is","它是"),("an **astonishing** **feat** of **architecture**,","**建筑**(architecture)史上**令人惊叹的**(astonishing)**壮举**(feat)，"),("and a **stubborn** **puzzle**.","也是一道**久解不开的**(stubborn)**谜题**(puzzle)。")],
     "（a feat of architecture：建筑上的壮举）"]]),
(2,[[[("Modern concrete","现代混凝土"),("is usually reinforced with **embedded** steel bars,","通常靠**嵌入**(embedded)其中的钢筋加固，")],
     "（be reinforced with…：用……加固）"],
    [[("which","而钢筋"),("are **prone** to **corrosion**.","**容易**(prone)发生**锈蚀**(corrosion)。")],
     "（which…：非限制性定语从句，修饰 steel bars；\nbe prone to…：容易……）"]]),
(2,[[[("As the steel **rusts**,","钢筋**生锈**(rusts)时"),("it **swells**","会**膨胀**(swells)，"),("and **fractures** the concrete around it,","把周围的混凝土**撑裂**(fractures)；")],
     "（As…：时间状语从句，当……时；\naround it：后置定语，修饰 concrete，it 指 the steel）"],
    [[("and many structures","许多建筑的"),("are designed for a **lifespan** of around 50 years.","设计**使用寿命**(lifespan)约为50年。")],
     "（be designed for…：按……设计）"]]),
(2,[[[("Roman concrete","罗马混凝土"),("is not stronger than its modern **counterpart**;","并不比现代的**同类材料**(counterpart)更坚固，")],
     "（its modern counterpart：现代的同类材料，即现代混凝土）"],
    [[("its **merit**","它的**长处**(merit)"),("lies in **durability**.","在于**耐久性**(durability)。")],
     "（lie in…：在于……）"]]),
(3,[[[("Yet","然而，"),("the ancient material","这种古代材料"),("seemed to have","似乎有个"),("a **shortcoming**.","**缺点**(shortcoming)。")]]]),
(3,[[[("It","它的内部"),("is **dotted** with","**散布**(dotted)着"),("white **chunks** of lime,","白色的石灰**小块**(chunks)，")],
     "（be dotted with…：散布着……，布满……）"],
    [[("known as lime clasts.","称为石灰团块。")],
     "（known as…：过去分词短语作后置定语，修饰 chunks）"]]),
(3,[[[("Experts long","长期以来，专家"),("**ascribed** these **lumps** **to**","**把**(ascribed to)这些**块状物**(lumps)**归因于**(ascribed to)"),("**sloppy** mixing","搅拌**马虎**(sloppy)"),("or **inferior** raw **ingredients**,","或原料**成分**(ingredients)**低劣**(inferior)。")],
     "（ascribe A to B：把 A 归因于 B）"],
    [[("a **defect** that, they assumed, a more **conscientious** builder would have avoided.","他们认为，换一个更**认真负责的**(conscientious)工匠，就不会出这种**瑕疵**(defect)。")],
     "（a defect that…：同位语，补充说明前面说的情况；\nthey assumed：插入语，他们认为；\nwould have avoided：虚拟语气，本可以避免）"]]),
(4,[[[("A study published in Science Advances in January 2023","2023年1月发表于《科学进展》（Science Advances）的一项研究"),("offered","提出了"),("a different **interpretation**.","不同的**解释**(interpretation)。")],
     "（published in…：过去分词短语作后置定语，修饰 study）"]]),
(4,[[[("The clasts, it suggested,","该研究认为，这些团块"),("were a **by-product** of \"hot mixing\" with quicklime,","是用生石灰“热混合”留下的**副产品**(by-product)；")],
     "（it suggested：插入语，it 指这项研究；\na by-product of…：……的副产品）"],
    [[("a **reactive** lime that heats up in water.","生石灰是一种遇水会发热、**活性强的**(reactive)石灰。")],
     "（a reactive lime…：同位语，补充说明 quicklime；\nthat heats up in water：定语从句，修饰 lime）"]]),
(4,[[[("When water","水"),("**seeps** into a crack,","**渗入**(seeps)裂缝时，")],
     "（When…：时间状语从句）"],
    [[("the clasts","团块"),("**dissolve**","会**溶解**(dissolve)，"),("and their **calcium**","其中的**钙**(calcium)"),("recrystallises as calcium carbonate,","重新结晶为碳酸钙，"),("**plugging** the gap.","**堵住**(plugging)缝隙。")],
     "（recrystallise as…：重新结晶为……；\nplugging the gap：现在分词短语作状语，表示结果）"]]),
(4,[[[("In tests,","试验中，"),("water **ceased** to **trickle** through cracked hot-mixed samples within weeks,","几周之内，水就**不再**(ceased)从开裂的热混合样本中**细细流过**(trickle)；")],
     "（cease to do：不再做……；\nwithin weeks：几周之内）"],
    [[("but kept flowing through samples without quicklime.","而在不含生石灰的样本中，水却一直流个不停。")],
     "（keep doing：一直做……；\nwithout quicklime：介词短语作后置定语，修饰 samples）"]]),
(5,[[[("The **implications**","这项发现的**意义**(implications)"),("**extend** beyond **archaeology**.","**超出**(extend)了**考古学**(archaeology)的范围。")],
     "（extend beyond…：超出……的范围）"]]),
(5,[[[("Cement **manufacture**","水泥**生产**(manufacture)"),("accounts for about 8 per cent of global carbon dioxide **emissions**,","约占全球二氧化碳**排放**(emissions)的8%，")],
     "（account for…：（在数量上）占……）"],
    [[("the think-tank Chatham House","智库查塔姆研究所（Chatham House）"),("reported in June 2018.","2018年6月报告称。")]]]),
(5,[[[("Concrete that mends its cracks","能自行修补裂缝的混凝土"),("could last longer,","可能更经久耐用，")],
     "（that mends its cracks：定语从句，修饰 Concrete）"],
    [[("making **demolition** and rebuilding rarer","**拆除**(demolition)与重建因而减少，"),("and **trimming** emissions.","排放也随之**削减**(trimming)。")],
     "（making… and trimming…：两个现在分词短语作状语，表示结果；\nmake A rarer：使 A 更少见）"]]),
(5,[[[("The white lumps","这些白色块状物"),("once **scorned** as signs of **clumsy** workmanship","曾被**轻视**(scorned)为手艺**拙劣的**(clumsy)痕迹，")],
     "（once scorned as…：过去分词短语作后置定语，修饰 lumps；\nscorn A as B：把 A 轻视为 B）"],
    [[("have **prompted**","如今却**促使**(prompted)人们"),("a **rethink** of construction.","**重新思考**(rethink)建造之道。")],
     "（a rethink of…：对……的重新思考）\n"
     "（简述：万神殿穹顶建成近1,900年依然屹立，是世界上最大的无钢筋混凝土穹顶。\n"
     "现代混凝土里的钢筋会生锈膨胀、撑裂混凝土，许多建筑设计寿命约50年；\n"
     "罗马混凝土并不更坚固，长处在于耐久。它里面的白色石灰团块，\n"
     "过去被专家当作搅拌马虎或原料低劣的瑕疵。2023年《科学进展》的研究认为，\n"
     "团块是生石灰热混合的副产品：水渗入裂缝时团块溶解，钙重新结晶为碳酸钙，堵住缝隙。\n"
     "水泥生产约占全球二氧化碳排放的8%，能自行修补裂缝的混凝土可能减少拆建和排放，\n"
     "这些曾被轻视的团块因此促使人们重新思考建造之道。）"]]),
]
G={}
CONF={"合组":G}
out={"no":"55","title_en":"The Secret of Rome's Undying Concrete","title_zh":"罗马混凝土的千年之谜","title_fx":{"hl":["Secret","Undying"],"ghost":[]},"sentences":[],"核对确认":CONF,"结尾解说":"简述",
     "高亮按实际开口":True,"高亮开口门槛":40,
     "术语":{"Pantheon":"万神殿","Roman":"罗马","Science Advances":"《科学进展》","Chatham House":"查塔姆研究所","AD":"公元"}}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 核对 import 生成并核对
生成并核对(S, out)
