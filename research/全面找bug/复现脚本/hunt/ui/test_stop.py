"""Real browser: long 「生成」 with the dummy engine; stop button: one click -> confirm text; >5 s -> back;
two clicks -> stops; buttons come back. Then: reload mid-task, click 生成 again with an empty script -> re-attach."""
import sys, time, re
def vis_stops(page):
    return [b.inner_text() + ('' if b.is_enabled() else '(disabled)') for b in page.locator('button').all() if '停止' in (b.inner_text() or '') and b.is_visible()]
from playwright.sync_api import sync_playwright
from pwlib import *
URL = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else "stop"
import random
TAG = str(random.randint(1000, 9999))
SCRIPT = "\n".join(f"这是第{i}句测试的讲稿{TAG}，我们来看看生成要多久。" for i in range(1, 201))
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=CHROME)
    page = br.new_page(viewport={"width": 1366, "height": 900})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(2)
    page.get_by_role("tab", name="③ 生成讲课音频").click()
    time.sleep(1)
    page.get_by_label("讲稿", exact=True).fill(SCRIPT)
    gen = page.locator("button", has_text="生成").filter(has_text="生成").first
    gen = page.get_by_role("button", name="生成", exact=True)
    gen.click()
    t0 = time.time()
    stop = page.get_by_role("button", name="⏹ 停止")
    for _ in range(40):
        if stop.count() and stop.first.is_visible():
            break
        time.sleep(0.25)
    print(f"stop visible after {time.time()-t0:.1f}s:", stop.count() and stop.first.is_visible())
    bar = lambda: text_of(page, ".vt-bar-box")[-80:].replace("\n", " ")
    if mode == "stop":
        time.sleep(2)
        stop.first.click()
        time.sleep(0.8)
        sb = page.locator("button.stop, button[class*='stop']").filter(has_text="停止")
        print("after 1 click:", vis_stops(page))
        time.sleep(6.5)
        print("after 6.5 s:", vis_stops(page))
        b = page.get_by_role("button", name=re.compile("停止")).first
        b.click(); time.sleep(0.7)
        print("click 1 again:", vis_stops(page))
        page.get_by_role("button", name=re.compile("停止")).first.click(); time.sleep(1)
        print("click 2:", vis_stops(page))
        t1 = time.time()
        while time.time() - t1 < 120:
            if "已停止" in text_of(page, "body"):
                break
            time.sleep(0.5)
        time.sleep(2)
        print(f"stopped after {time.time()-t1:.1f}s; gen button enabled:", gen.is_enabled(), "| text:", gen.inner_text())
        print("stop visible:", [x.is_visible() for x in page.locator("button", has_text="停止").all()])
        print("speed_try enabled:", page.get_by_role("button", name="▶ 试听语速").is_enabled())
    else:
        time.sleep(3)
        print("bar before reload:", bar())
        page.reload()
        page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
        time.sleep(2)
        print("banner:", text_of(page, "body").split("\n")[0:0], [l for l in text_of(page, "body").split("\n") if "后台正在" in l][:1])
        page.get_by_role("tab", name="③ 生成讲课音频").click()
        time.sleep(1)
        gen = page.get_by_role("button", name="生成", exact=True)
        gen.click()
        time.sleep(3)
        print("after re-click bar:", bar())
        print("stop visible:", [x.is_visible() for x in page.locator("button", has_text="停止").all()])
        t1 = time.time()
        while time.time() - t1 < 400:
            body = text_of(page, "body")
            if "生成好了" in body or "没有完成" in body or "已停止" in body or "生成完成" in body:
                break
            if not page.get_by_role("button", name="生成", exact=True).count():
                pass
            time.sleep(1)
        time.sleep(3)
        print(f"finished after {time.time()-t1:.0f}s; gen enabled:", page.get_by_role("button", name="生成", exact=True).is_enabled())
        print("gen_md:", [l for l in text_of(page, ".vt-md").split("\n") if l.strip()][:4])
        print("redo box:", page.get_by_label("只重新生成第几句（例如 3,5,8-10；留空 = 全部）").input_value())
    print("page errors:", errs)
    page.screenshot(path=f"shot_stop_{mode}.png")
    br.close()
