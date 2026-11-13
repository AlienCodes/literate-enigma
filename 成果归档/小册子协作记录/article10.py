from group_01_12 import *
zh=[
'1911年8月21日星期一，卢浮宫照例闭馆，《蒙娜丽莎》就在这天被人悄悄从墙上取走。直到第二天，一位前来画素描的画家发现，裸露的灰泥墙上有一块显眼的空缺，画作失踪才被察觉。管理人员随后将博物馆关闭了一周。',
'博物馆重新开放后，好奇的参观者排起队来，盯着原本悬挂那幅杰作的空位看。1911年9月7日，诗人纪尧姆·阿波利奈尔被拘押，羁押时间约为一周；巴勃罗·毕加索也受到讯问。两人最终都洗清了参与这起盗窃案的嫌疑。',
'闯入者是意大利人文森佐·佩鲁贾，他曾在卢浮宫短期担任玻璃工。他星期天便藏进储藏室，随后身穿工作罩衫，把画塞在衣服下面，大步走了出去，没有受到任何阻拦。此后两年多，画作一直藏在他巴黎住处一只带有夹层底的箱子里。',
'1913年12月，佩鲁贾联系了佛罗伦萨艺术品商人阿尔弗雷多·杰里。乌菲齐美术馆馆长在佩鲁贾下榻的旅馆鉴定了画作的真伪；佩鲁贾于1913年12月11日被捕。他以爱国为由，声称想把画送回祖国，误以为它曾被拿破仑掠走。事实上，列奥纳多·达·芬奇是应国王弗朗索瓦一世的邀请，带着这幅画来到法国的。',
'画作在意大利展出后，于1914年1月4日重新回到卢浮宫。1914年6月，法庭判处佩鲁贾一年零15天监禁，但他实际被关押了约七个月。许多历史学家认为，这起盗窃案让一幅原本只是众多备受推崇的珍品之一的画，跃升为世界上最著名的画作。若真如此，它的名声便始于一面空墙。'
]
rows='''
customarily|customarily|adv.|照例；按照惯例
discreetly|discreetly|adv.|不引人注意地；悄悄地
plucked|pluck|v.|摘下；取走
disappearance|disappearance|n.|失踪；消失
unnoticed|unnoticed|adj.|未被察觉的
sketch|sketch|v.|画素描；速写
conspicuous|conspicuous|adj.|显眼的；引人注意的
gap|gap|n.|空缺；缺口
plaster|plaster|n.|灰泥；墙面抹灰
Custodians|custodian|n.|管理人员；看管者
shuttered|shutter|v.|关闭
reopened|reopen|v.|重新开放
curious|curious|adj.|好奇的
onlookers|onlooker|n.|围观者
stare at|stare at|phr. v.|盯着看；凝视
vacant|vacant|adj.|空着的
masterpiece|masterpiece|n.|杰作
in custody|in custody|phr.|被拘押；在羁押中
interrogated|interrogate|v.|讯问；审问
involvement|involvement|n.|参与；牵涉
burglary|burglary|n.|入室盗窃；盗窃案
intruder|intruder|n.|闯入者
temporarily|temporarily|adv.|暂时地；短期地
lurked|lurk|v.|潜伏；躲藏
strode|stride|v.|大步走
unchallenged|unchallenged|adj.|未受盘问或阻拦的
tucked|tuck|v.|塞入；藏入
beneath|beneath|prep.|在……下面
stashed|stash|v.|藏匿
trunk|trunk|n.|大箱子；旅行箱
lodgings|lodgings|n.|租住处
contacted|contact|v.|联系；联络
dealer|dealer|n.|商人；交易商
authenticated|authenticate|v.|鉴定真伪；证实为真
apprehended|apprehend|v.|逮捕
patriotism|patriotism|n.|爱国主义；爱国之情
repatriated|repatriate|v.|送回祖国；归还原属国
mistakenly|mistakenly|adv.|错误地
looted|loot|v.|掠夺；劫掠
accompanied|accompany|v.|陪同；此处指带着同行
at the invitation of|at the invitation of|phr.|应……的邀请
showings|showing|n.|展出；展示
reinstated|reinstate|v.|使恢复原位；放回原处
tribunal|tribunal|n.|法庭
imposed|impose|v.|施加；判处（刑罚）
penalty|penalty|n.|刑罚；处罚
imprisoned|imprison|v.|监禁；关押
heist|heist|n.|盗窃大案
elevated|elevate|v.|提高；提升地位
esteemed|esteemed|adj.|受尊重的；备受推崇的
gem|gem|n.|珍品；瑰宝
to|to|prep.|与elevate连用，表示提升到
renowned|renowned|adj.|著名的；享有盛誉的
fame|fame|n.|名声；声誉
bare|bare|adj.|空的；裸露的
'''
core=['discreetly','disappearance','unnoticed','conspicuous','vacant','masterpiece','in custody','interrogated','involvement','burglary','unchallenged','stashed','authenticated','apprehended','patriotism','repatriated','looted','reinstated','tribunal','imposed','heist','renowned']
prompt=json.loads((ROOT/'illustrations/10.json').read_text())['prompt']
build('10',zh,rows,core,['conspicuous','involvement','patriotism','renowned'],'一幅失踪的画，如何引来更多目光？','',prompt,{'unnoticed':'went unnoticed until the next day','conspicuous':'a conspicuous gap of bare plaster.','in custody':'held in custody for about a week','involvement':'cleared of involvement','unchallenged':'strode out unchallenged','stashed':'stashed in a false-bottomed trunk','authenticated':'authenticated the painting','repatriated':'wanted it repatriated','looted':'believing Napoleon had looted it.','imposed':'imposed a penalty','heist':'the heist elevated','renowned':"the world\'s most renowned painting."})
print('10 content and illustration ready')
