import json,re
N=None
S=[
(1,[[[("Name two addresses","随便说出两个地址，")]],
    [[("and a London cabbie","伦敦的出租车司机就能"),("will **rattle off**","**脱口说出**(rattle off)"),("the quickest route.","最快的路线。")],"（祈使句 + and：只要……就……）"]]),
(1,[[[("That **prowess**","这份**本领**(prowess)"),("is **hard-won**.","**来之不易**(hard-won)。")],"（hard-won：费尽辛苦才得来的）"]]),
(1,[[[("To earn a **licence**,","要拿到**执照**(licence)，")]],
    [[("**aspiring** drivers","**立志入行的**(aspiring)司机"),("must **conquer**","必须**攻克**(conquer)"),("\"the Knowledge\",","「知识大考」，")],"（The Knowledge：伦敦出租车执照考试的俗称）"],
    [[("an **arduous** **examination**","这是一场**艰巨的**(arduous)**考试**(examination)，")]],
    [[("on about 25,000 streets","考查约25,000条街道，"),("\n",""),("within six miles of Charing Cross.","范围是查令十字周边6英里内。")]]]),
(1,[[[("**Hopefuls**","**入行考生**(Hopefuls)"),("**typically**","**通常**(typically)"),("spend three to four years","要花三到四年")]],
    [[("**committing** this **labyrinth** to memory,","才能把这座**迷宫**(labyrinth)**记**(committing)在脑子里，")],"（commit sth to memory：把……牢牢记住）"],
    [[("and only about half **qualify**.","而最终**合格**(qualify)的只有大约一半。")]]]),
(2,[[[("A study published in PNAS in April 2000","2000年4月发表于《美国国家科学院院刊》（PNAS）的一项研究")]],
    [[("**scanned**","**扫描**(scanned)了"),("16 male cabbies","16名男性出租车司机"),("and 50 other men.","和50名其他男性（的大脑）。")]]]),
(2,[[[("The hippocampus","海马体"),("is a seahorse-shaped structure","是一个形似海马、")],"（海马体：大脑深处负责记忆的区域）"],
    [[("**vital** to memory and **navigation**.","对记忆和**导航**(navigation)**至关重要的**(vital)结构。")]]]),
(2,[[[("In the cabbies,","在出租车司机身上，")]],
    [[("its rear, or **posterior**, **portion**","海马体靠后的**部分**(portion)，即**后部的**(posterior)那部分，")]],
    [[("was larger than in the other men,","比其他男性的大，")]],
    [[("and its front, or **anterior**, portion","而靠前的部分，即**前部的**(anterior)那部分，"),("smaller.","则较小。")]]]),
(2,[[[("Longer service","从业时间越长，"),("went with a larger rear portion.","后部也越大。")],"（go with：与……相伴；此处指两者相关，不是因果）"]]),
(3,[[[("Yet","然而，"),("the link","这种关联"),("left the cause **uncertain**.","让原因依然是**不确定的**(uncertain)。")]]]),
(3,[[[("Perhaps","也许"),("an **innate** **flair** for **spatial** tasks","是**天生的**(innate)**空间**(spatial)任务**天赋**(flair)")]],
    [[("**lured** people","把人们**吸引**(lured)"),("to the **occupation**,","到这个**职业**(occupation)中来，")]],
    [[("or perhaps","也许"),("**stressful** driving","**紧张的**(stressful)驾驶"),("was the **culprit**.","才是**罪魁祸首**(culprit)。")]]]),
(3,[[[("A December 2006 study","2006年12月的一项研究"),("**dispelled** the second **notion**:","**打消**(dispelled)了第二种**想法**(notion)：")]],
    [[("cabbies had more rear grey matter,","出租车司机后部的灰质——")]],
    [[("the tissue **dense** with **nerve** cells,","即**密布**(dense)**神经**(nerve)细胞的组织——")],"（dense with：密布着……）"],
    [[("than bus drivers,","多于公交司机，"),("**confined** to **predetermined** routes,","他们**局限于**(confined)**预先确定的**(predetermined)线路，"),("\n",""),("of **equivalent** experience and stress.","经验和压力都**相当的**(equivalent)。")]]]),
(4,[[[("A December 2011 **longitudinal** study","2011年12月的一项**纵向的**(longitudinal)研究"),("**tackled** the first,","**着手解决**(tackled)第一种疑问，")],"（纵向研究：长期追踪同一批人）"],
    [[("scanning 79 **trainees** and 31 non-trainees","扫描了79名**学员**(trainees)和31名非学员，")]],
    [[("at **enrolment**","在**入学**(enrolment)时"),("and three to four years later.","以及三到四年后各扫描一次。")]]]),
(4,[[[("Their brains","他们的大脑"),("began alike.","起点相同。")]]]),
(4,[[[("Only the 39 who qualified","只有最终合格的39人"),("**exhibited**","**显示出**(exhibited)"),("an **expansion** of rear grey matter,","后部灰质的**增长**(expansion)，")]],
    [[("so the **sequence** suggests","因此这一**先后顺序**(sequence)提示，")]],
    [[("learning","学习"),("**preceded**","**先于**(preceded)"),("the **enlargement**.","**增大**(enlargement)发生。")]]]),
(5,[[[("The gain","这种收获"),("appeared to **entail**","似乎**必然带来**(entail)"),("a **trade-off**:","一种**此消彼长的取舍**(trade-off)：")]],
    [[("qualified drivers","合格司机"),("**trailed** the non-trainees","**落后于**(trailed)非学员——")]],
    [[("on one test of recalling an **intricate** figure.","在一项回忆**复杂的**(intricate)图形的测试上。")]]]),
(5,[[[("The **cohorts**","这些研究的**样本群体**(cohorts)"),("were small","规模小，"),("and **exclusively** male,","而且**仅仅**(exclusively)由男性组成，")]],
    [[("yet the studies **imply**","但这些研究**意味着**(imply)，")]],
    [[("the healthy adult brain","健康的成人大脑")]],
    [[("can **remodel** itself through **intensive** learning.","能够通过**高强度的**(intensive)学习**重塑**(remodel)自身。")]]]),
(5,[[[("Every street learned,","每记住一条街道，"),("it seems,","看来，")]],
    [[("**occupied** room once **claimed** by something else.","都**占据**(occupied)了一块原本被其他东西**占用**(claimed)的空间。")]]]),
]
out={"no":"04","title_en":"The Brain That Learned London","title_zh":"被街道重塑的大脑","title_fx":{"hl":["Brain","London"],"ghost":[]},"sentences":[]}
for p,chs in S:
    cs=[]
    for c in chs:
        al=[list(x) for x in c[0]]
        d={"en":" ".join(a for a,b in al if a!="\n"),"zh":"".join(b for a,b in al),"align":al}
        if len(c)>1: d["note"]=c[1]
        cs.append(d)
    out["sentences"].append({"para":p,"chunks":cs})
json.dump(out,open("04.json","w"),ensure_ascii=False,indent=1)
# validate
import glob
art=open(glob.glob("/home/user/postgraduate-vocabulary/新版定稿/04-*.md")[0]).read()
eng=art.split("## 英文")[1].split("## 中文")[0].strip().split("\n\n")
norm=lambda s:re.sub(r"\s|\*\*","",s)
for i,pp in enumerate(eng,1):
    got="".join(c["en"] for s in out["sentences"] if s["para"]==i for c in s["chunks"])
    print(i,norm(got)==norm(pp)) 
    if norm(got)!=norm(pp): print(norm(got));print(norm(pp))
abold=set(re.findall(r"\*\*(.+?)\*\*","\n".join(eng)));sb=set()
for s in out["sentences"]:
  for c in s["chunks"]:
    assert c["zh"]=="".join(b for a,b in c["align"])
    for w in re.findall(r"\*\*(.+?)\*\*",c["en"]):
        sb.add(w); assert "("+w+")" in c["zh"],w
    for w in re.findall(r"\*\*[^*]+\*\*\(([^)]+)\)",c["zh"]): assert "**"+w+"**" in c["en"],w
print("bold set equal",abold==sb, abold^sb)
for s in out["sentences"]:
  print("--",s["para"])
  for c in s["chunks"]:
    print(" EN:",c["en"]);print(" ",c["align"]);
    if "note" in c: print("  note:",c["note"])
