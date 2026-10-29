import json, os
def 看门停用():
    """新管开关：<工具>/管道.json 写 {"看门": "停用"} 时，8 套看门机制（证据、闲置、用上核查、门变异、放行口子、规则执行核查、演练、丝滑）不再当门"""
    try: return json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '管道.json'))).get('看门') == '停用'
    except Exception: return False
