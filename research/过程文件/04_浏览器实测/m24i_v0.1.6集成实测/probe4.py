"""Find which event sends a list to a Markdown component (gradio 4.24 frontend crashes on message.trim())."""
import json
import time
import urllib.request

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:7876/"
cfg = json.load(urllib.request.urlopen(URL + "config"))
types = {c["id"]: c["type"] for c in cfg["components"]}
labels = {c["id"]: (c.get("props", {}).get("label") or c.get("props", {}).get("value") or "") for c in cfg["components"]}
deps = cfg["dependencies"]
print("markdown ids:", [i for i, t in types.items() if t == "markdown"][:60])
bad = []
EV = {}
SEEN = []


def check_msg(msg):
    if msg.get("msg") not in ("process_generating", "process_completed"):
        return
    out = (msg.get("output") or {})
    data = out.get("data")
    if "fn_index" not in msg and msg.get("event_id") in EV:
        msg["fn_index"] = EV[msg["event_id"]]
    if not isinstance(data, list):
        return
    dep = None
    if isinstance(msg.get("fn_index"), int) and msg["fn_index"] < len(deps):
        dep = deps[msg["fn_index"]]
    if dep is None:
        return
    for cid, val in zip(dep["outputs"], data):
        v = val.get("value") if isinstance(val, dict) and val.get("__type__") == "update" else val
        if types.get(cid) == "markdown" and v is not None and not isinstance(v, str):
            bad.append((msg["fn_index"], cid, str(labels.get(cid))[:30], repr(v)[:80]))


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 1000})
    bodies = []

    def on_resp(r):
        if "/queue/data" in r.url:
            try:
                bodies.append(r.text())
            except Exception as exc:  # noqa
                bodies.append("")

    pg.on("response", on_resp)

    def on_join(r):
        if "/queue/join" in r.url:
            try:
                fn = json.loads(r.request.post_data or "{}").get("fn_index")
                EV[r.json().get("event_id")] = fn
                SEEN.append(fn)
            except Exception as exc:  # noqa
                pass

    pg.on("response", on_join)
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(3000)
    pg.get_by_role("tab", name="③ 生成讲课音频").click()
    pg.wait_for_timeout(800)
    pg.get_by_placeholder("大家好，今天我们来学习……").fill("…… ！！")
    pg.mouse.click(5, 5)
    pg.get_by_role("button", name="生成", exact=True).click()
    time.sleep(5)
    b.close()

for body in bodies:
    for line in body.splitlines():
        if line.startswith("data:"):
            try:
                check_msg(json.loads(line[5:]))
            except Exception:
                pass
print("bodies:", len(bodies), [len(x) for x in bodies])
for body in bodies:
    for line in body.splitlines()[:3]:
        print("  ", line[:300])
print("joined fns:", [(f, [types.get(o) for o in deps[f]["outputs"]][:4]) for f in SEEN if isinstance(f, int)])
print("BAD:", bad)
