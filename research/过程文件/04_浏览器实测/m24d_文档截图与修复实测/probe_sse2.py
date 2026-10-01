"""Log raw SSE messages of the ③ generate event during the forced-error case (g)."""
import time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:7877/"
HOOK = """(() => { const ES = window.EventSource; window.EventSource = function (url, cfg) { const es = new ES(url, cfg);
  es.addEventListener('message', (ev) => { try { const d = JSON.parse(ev.data);
    {
      const data = d.output && d.output.data ? d.output.data : null;
      const sum = '' && data ? data.map((x, i) => i + ':' + (Array.isArray(x) ? 'L' + x.length + (x.length ? JSON.stringify(x).slice(0, 40) : '') : (x === null ? 'N' : typeof x === 'object' ? 'D' + Object.keys(x).join('/').slice(0, 30) : typeof x[0]))).join(' ') : '';
      console.log('SSE ' + (performance.now()/1000).toFixed(2) + ' es' + (es.__n || (es.__n = Math.random().toString(36).slice(2,5))) + ' ' + d.msg + ' ' + (d.event_id || '').slice(0, 6) + ' n=' + (data ? data.length : -1) + ' ' + sum);
    } } catch (e) {} }); return es; }; window.EventSource.prototype = ES.prototype; })();"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 1000}, locale="zh-CN")
    pg.add_init_script(HOOK)
    pg.on("console", lambda m: print(m.text[:900]) if m.text.startswith("SSE") or m.type == "error" and "font" not in m.text and "resource" not in m.text else None)
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(3500)
    v = pg.get_by_label("声音名称（新建请直接输入名字）")
    v.click(); v.fill("我的声音"); v.press("Enter"); pg.keyboard.press("Escape"); pg.mouse.click(5, 5)
    pg.wait_for_timeout(2500)
    pg.get_by_role("tab", name="③ 生成讲课音频").click(); pg.wait_for_timeout(1000)
    for k in range(2):
        print(f"===== g #{k}")
        pg.get_by_placeholder("大家好，今天我们来学习……").fill("…… ！！ ——"); pg.mouse.click(5, 5)
        pg.get_by_role("button", name="生成", exact=True).click()
        pg.wait_for_timeout(5000)
        print("box:", pg.evaluate("() => [...document.querySelectorAll('.vt-bar-box')].filter(e => e.offsetParent).map(e => e.innerText.slice(0, 60))")[:1])
    b.close()
