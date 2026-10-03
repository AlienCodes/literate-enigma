"""Real browser (gradio 4.24): is 「📄 上传更多母本」 usable while 「📝 一键全部文字校正」 is locked?
Usage: python3 browser_check.py <url> <phase>   phase = locked | unlocked"""
import sys
import time

from playwright.sync_api import sync_playwright

URL, PHASE = (sys.argv + ["", ""])[1:3]
SHOT = sys.argv[3] if len(sys.argv) > 3 else None


def state(page):
    return page.evaluate("""() => {
      const box = document.querySelector('#vt-tr-files');
      const btn = document.querySelector('#vt-tr-btn');
      const info = Array.from(document.querySelectorAll('.vt-tr-info')).map(e => e.innerText).join(' ');
      return {
        box_exists: !!box,
        file_inputs: box ? box.querySelectorAll('input[type=file]').length : -1,
        box_text: box ? box.innerText.replace(/\\s+/g, ' ').slice(0, 200) : '',
        btn_disabled: btn ? (btn.disabled || btn.hasAttribute('disabled')) : null,
        info: info.slice(0, 300),
      };
    }""")


if __name__ == "__main__":
  with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL)
        page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
        time.sleep(4)  # app.load → textfix_state
        s = state(page)
        print(PHASE, "state:", s)
        if SHOT:
            page.locator("#vt-tr-files").scroll_into_view_if_needed()
            page.screenshot(path=SHOT)
        print("page errors:", errors)
        browser.close()
