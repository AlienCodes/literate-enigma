"""Inject logging into gradio's client diff applier (je) and Blocks value setter, then run the forced-error generate twice."""
import re
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:7877/"


def patch_index(route):
    resp = route.fetch()
    body = resp.text()
    body = body.replace("function je(S,k){",
        "function je(S,k){try{console.log('JE '+S.slice(0,6)+' hasJ='+(!!J[S])+' d7='+JSON.stringify(k.data[7]).slice(0,80))}catch(e){}")
    body = body.replace("(y?.stage===\"complete\"||y?.stage===\"error\")&&(I[R]&&delete I[R],R in J&&delete J[R])",
        "((y?.stage===\"complete\"||y?.stage===\"error\")&&console.log('DEL '+String(R).slice(0,6)+' type='+m+' stage='+(y&&y.stage)),(y?.stage===\"complete\"||y?.stage===\"error\")&&(I[R]&&delete I[R],R in J&&delete J[R]))")
    body = body.replace("const{type:m,status:y,data:G}=le(q,W[a]);",
        "const{type:m,status:y,data:G}=le(q,W[a]);try{console.log('MSG '+String(R).slice(0,6)+' raw='+(q&&q.msg)+' '+m+' '+(y&&y.stage)+' d7='+(G&&G.data?JSON.stringify(G.data[7]).slice(0,60):'-'))}catch(e){}")
    route.fulfill(response=resp, body=body)


def patch_blocks(route):
    resp = route.fetch()
    body = resp.text()
    body = body.replace("async function Z(y,G){const U=f[G].outputs,",
        "async function Z(y,G){try{if(y&&y.length===18)console.log('Z fn='+G+' v7='+JSON.stringify(y[7]).slice(0,80))}catch(e){};const U=f[G].outputs,")
    route.fulfill(response=resp, body=body)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = b.new_context(viewport={"width": 1280, "height": 1000}, locale="zh-CN")
    ctx.route(re.compile(r".*/assets/index-c4af12f4\.js$"), patch_index)
    ctx.route(re.compile(r".*/assets/Blocks-5950680d\.js$"), patch_blocks)
    pg = ctx.new_page()
    pg.on("console", lambda m: print(m.text[:300]) if m.text[:3] in ("JE ", "DEL", "MSG", "Z f") else None)
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(3500)
    v = pg.get_by_label("声音名称（新建请直接输入名字）")
    v.click(); v.fill("我的声音"); v.press("Enter"); pg.keyboard.press("Escape"); pg.mouse.click(5, 5)
    pg.wait_for_timeout(2500)
    pg.get_by_role("tab", name="③ 生成讲课音频").click(); pg.wait_for_timeout(1000)
    for k in range(4):
        print(f"===== g #{k}")
        pg.get_by_placeholder("大家好，今天我们来学习……").fill("…… ！！ ——"); pg.mouse.click(5, 5)
        pg.get_by_role("button", name="生成", exact=True).click()
        pg.wait_for_timeout(5000)
    b.close()
