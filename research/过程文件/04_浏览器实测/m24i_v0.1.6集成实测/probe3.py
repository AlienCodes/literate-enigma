import sys
import time

from playwright.sync_api import sync_playwright

SEL = "() => [...document.querySelectorAll('button[role=tab]')].filter(e => e.getAttribute('aria-selected') === 'true').map(e => e.innerText)"


def run(seq):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        pg = b.new_page(viewport={"width": 1280, "height": 1000})
        pg.on("console", lambda m: print(f"  [console {time.time() % 1000:.1f}]", m.type, m.text[:200]) if ("TRIMCALL" in m.text) else None)
        pg.add_init_script("""Object.defineProperty(Object.prototype, 'trim', {configurable: true, writable: true,
            value: function () { try { console.log('TRIMCALL ' + typeof this + ' ' + JSON.stringify(this).slice(0, 300)
              + ' @ ' + new Error().stack.split('\\n').slice(2, 4).join(' | ')); } catch (e) { console.log('TRIMCALL ?'); }
              return String(this); }});""")
        pg.on("pageerror", lambda e: print("  [pageerror]", str(e)[:200], "\n", (getattr(e, "stack", "") or "")[:1500]))
        pg.goto("http://127.0.0.1:7876/", wait_until="networkidle")
        print(f"  [step {time.time() % 1000:.1f}] loaded")
        pg.wait_for_timeout(3000)
        log = []
        for step in seq:
            if step.startswith("tab:"):
                pg.get_by_role("tab", name=step[4:]).click()
                pg.wait_for_timeout(1200)
                log.append(f"{step} -> {pg.evaluate(SEL)}")
                print(f"  [step {time.time() % 1000:.1f}] {step}")
            elif step == "gen_err":
                pg.get_by_placeholder("大家好，今天我们来学习……").fill("…… ！！")
                pg.mouse.click(5, 5)
                print(f"  [step {time.time() % 1000:.1f}] click gen (err)")
                pg.get_by_role("button", name="生成", exact=True).click()
                time.sleep(4)
                log.append("gen_err done")
            elif step == "gen_ok":
                pg.get_by_placeholder("大家好，今天我们来学习……").fill("大家好，欢迎回来。")
                pg.mouse.click(5, 5)
                pg.get_by_role("button", name="生成", exact=True).click()
                time.sleep(6)
                log.append("gen_ok done")
            elif step.startswith("btn:"):
                pg.get_by_role("button", name=step[4:]).first.click()
                pg.wait_for_timeout(2500)
                log.append(f"{step} -> {pg.evaluate(SEL)}")
            elif step == "fullshot":
                pg.screenshot(path="<草稿目录>/integ_shots/_x.png", full_page=True)
                log.append("fullshot")
        print(" | ".join(log))
        b.close()


seqs = {
    "1": ["tab:③ 生成讲课音频", "tab:⑤ 鉴别"],
    "2": ["tab:🩺 环境检查", "tab:③ 生成讲课音频", "tab:⑤ 鉴别"],
    "3": ["tab:③ 生成讲课音频", "gen_err", "tab:⑤ 鉴别"],
    "4": ["tab:③ 生成讲课音频", "gen_ok", "tab:🩺 环境检查", "tab:③ 生成讲课音频", "gen_err", "tab:⑤ 鉴别"],
    "6": ["tab:③ 生成讲课音频", "gen_ok", "btn:④ 评估刚才生成的音频 →", "tab:⑤ 鉴别", "btn:🔄 重新检查显卡"],
    "7": ["tab:③ 生成讲课音频", "gen_err", "tab:⑤ 鉴别", "btn:🔄 重新检查显卡", "tab:⑤ 鉴别"],
    "5": ["tab:③ 生成讲课音频", "gen_ok", "fullshot", "tab:⑤ 鉴别"],
}
for k in (sys.argv[1:] or sorted(seqs)):
    print(k, end=": ")
    run(seqs[k])
