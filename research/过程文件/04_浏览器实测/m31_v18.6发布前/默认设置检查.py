import sys
from playwright.sync_api import sync_playwright
url=sys.argv[1]; out=sys.argv[2]; res=[]
def ok(name, cond, info=""):
    res.append(("PASS" if cond else "FAIL")+" "+name+(" — "+str(info)[:150] if info else ""))
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/opt/pw-browsers/chromium"); pg=b.new_page(viewport={"width":1400,"height":1000}, locale="en-US")
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(url); pg.wait_for_timeout(4000)
    ok("标签页标题", pg.title()=="声音分身 VoiceTwin v18", pg.title())
    body=pg.inner_text("body")
    ok("网页标题 v18", "声音分身 VoiceTwin v18" in body)
    pg.get_by_role("tab", name="③ 生成讲课音频").click(); pg.wait_for_timeout(1500)
    checked=pg.locator("input[type=radio]:checked").evaluate_all("els=>els.map(e=>e.parentElement.innerText)")
    ok("质量默认「一模一样」", any(t.strip().startswith("一模一样") for t in checked), checked)
    ok("文件名提示写模型名（v2ProPlus）", "第3课_10月05日09点30分_v2ProPlus.wav" in pg.inner_text("body"))
    pg.get_by_role("tab", name="② 训练模型").click(); pg.wait_for_timeout(1500)
    checked=pg.locator("input[type=radio]:checked").evaluate_all("els=>els.map(e=>e.parentElement.innerText)")
    ok("训练方式默认「一模一样」", any("一模一样" in t for t in checked), checked)
    pg.screenshot(path=out.replace(".txt","_train.png"), full_page=False)
    ok("网页脚本没有报错", not errs, errs)
    b.close()
open(out,"w",encoding="utf-8").write("\n".join(res)+f"\n{sum(r.startswith('PASS') for r in res)} / {len(res)} 通过\n")
print("\n".join(res))
