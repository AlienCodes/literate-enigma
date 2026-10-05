import sys,os
sys.path.insert(0,os.path.abspath('logo/C_graffiti')); sys.path.insert(0,'.')
import title_logo as T
which=sys.argv[2]
args={'01':('01','The Robber Who Thought Lemon Juice Made Him Invisible','以为柠檬汁能隐身的劫匪',['Lemon','Juice'],['Invisible']),
'02':('02','The Truth About One Marshmallow','一颗棉花糖的真相',['Marshmallow'],[]),
'03':('03','The Doctor Who Drank Bacteria to Win an Argument','喝下细菌的医生',['Drank','Bacteria'],['Argument'])}[which]
T.frame_title2(*args,sys.argv[1])
