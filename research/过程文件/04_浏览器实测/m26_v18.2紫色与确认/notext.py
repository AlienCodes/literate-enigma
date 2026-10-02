"""老师 v18.1 遇到的情况：片段切好了、文字没识别出来。浏览器里删除不能报错，要变紫色；表格写「还没有识别出文字」；上方说再点开始准备素材。"""
import json
import sys
import time
from pathlib import Path

B = Path(__file__).resolve().parent
src = (B / "check.py").read_text(encoding="utf-8"); src = src[:src.index("def main():")]
exec(compile(src, "h", "exec"))
recs = manifest()
for r in recs:
    r.update(text="", lang="", keep=True)
    r.pop("asr_done", None)
    r.pop("suspect", None)
MANIFEST.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n", encoding="utf-8")
ids = [r["id"] for r in recs]
with sync_playwright() as p:
    br = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = br.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(sys.argv[1])
    page.wait_for_function("() => document.querySelectorAll('#vt-clips tbody.tbody tr td').length > 20", timeout=60000)
    time.sleep(1.5)
    r = row(page, ids[1])
    check("没有文字的片段：写着「还没有识别出文字」", r and "还没有识别出文字" in r[4]["text"], r and r[4]["text"])
    cnt = page.locator(".vt-md").filter(has_text="用来训练的句子").first.inner_text()
    check("上方说明：再点一次「开始准备素材」", "开始准备素材" in cnt and "还没有识别出文字" in cnt, cnt[:160])
    cell(page, ids[0], 7).locator(".vt-menu-btn").click()
    page.locator(".vt-menu button", has_text="删除这一行").click()
    page.locator(".vt-menu button", has_text="确定删除").click()
    r = wait_row(page, ids[0], lambda r: "vt-mark-del" in r[7]["html"], "del", timeout=30)
    msg = page.locator(".vt-clip-msg").first.inner_text()
    check("删除不报错、这一行变紫色", r is not None and r[4]["bg"] == "rgb(233, 213, 255)" and "还没有可用的素材" not in msg, msg[:100])
    page.locator("#vt-clips").scroll_into_view_if_needed()
    page.screenshot(path=str(SHOTS / "11_notext_delete.png"))
    check("网页没有脚本错误", not errors, "; ".join(errors[:3]))
    br.close()
bad = [x for x in RESULTS if not x[1]]
print(f"{len(RESULTS) - len(bad)} / {len(RESULTS)} 项通过")
