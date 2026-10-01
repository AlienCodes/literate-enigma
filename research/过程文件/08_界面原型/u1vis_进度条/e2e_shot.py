import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

port = int(sys.argv[1])
out = sys.argv[2]
url = f"http://127.0.0.1:{port}/"
for _ in range(90):
    try:
        urllib.request.urlopen(url, timeout=2)
        break
    except Exception:
        time.sleep(1)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    page = b.new_page(viewport={"width": 800, "height": 700})
    page.goto(url)
    page.wait_for_selector("button")
    page.get_by_role("button", name="开始准备素材").click()
    page.wait_for_selector(".vt-prog.vt-running")
    time.sleep(2.0)
    print("running title:", page.evaluate("document.title"))
    print("btn:", page.locator("button.primary").inner_text(), page.locator("button.primary").is_disabled())
    page.screenshot(path=f"{out}_running.png", full_page=True)
    # 刷新网页（断开 SSE），任务应该继续
    page.reload()
    page.wait_for_selector("button")
    time.sleep(1.5)
    print("banner after reload:", page.locator(".prose").first.inner_text()[:200])
    page.get_by_role("button", name="开始准备素材").click()
    page.wait_for_selector(".vt-prog")
    time.sleep(1.0)
    print("after re-click pct:", page.locator(".vt-prog").get_attribute("data-pct"))
    page.screenshot(path=f"{out}_attached.png", full_page=True)
    page.wait_for_selector(".vt-prog.vt-done", timeout=30000)
    time.sleep(1.0)
    print("done title:", page.evaluate("document.title"))
    print("btn:", page.locator("button.primary").inner_text(), page.locator("button.primary").is_disabled())
    page.locator("text=详细过程").click()
    time.sleep(0.5)
    print("log head:", page.locator("textarea").input_value()[:160].replace("\n", " / "))
    page.screenshot(path=f"{out}_done.png", full_page=True)
    b.close()
