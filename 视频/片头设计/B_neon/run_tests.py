import sys,os
sys.path.insert(0,'.'); sys.path.insert(0,'logo/B_neon')
import title_logo as T
D='logo/B_neon/'
if T.S==1:
    T.frame_title2('01','The Robber Who Thought Lemon Juice Made Him Invisible','以为柠檬汁能隐身的劫匪',['Lemon','Juice'],['Invisible'],D+'t01.png')
    T.frame_title2('02','The Truth About One Marshmallow','一颗棉花糖的真相',['Marshmallow'],[],D+'t02.png')
    T.frame_title2('03','The Doctor Who Drank Bacteria to Win an Argument','喝下细菌的医生',['Drank','Bacteria'],['Argument'],D+'t03.png')
else:
    T.frame_title2('03','The Doctor Who Drank Bacteria to Win an Argument','喝下细菌的医生',['Drank','Bacteria'],['Argument'],D+'t03_4k.png')
