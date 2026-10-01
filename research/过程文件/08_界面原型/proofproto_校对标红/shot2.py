import json, os, glob
from playwright.sync_api import sync_playwright
P = os.path.dirname(os.path.abspath(__file__))
exe = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))
res = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe[-1] if exe else None, args=["--no-proxy-server"])
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.goto("http://127.0.0.1:7880/", wait_until="networkidle")
    pg.wait_for_timeout(2500)

    def td(e, r, c):   # first tr:has(td) is gradio's hidden column-width measuring row -> data rows start at 1
        return pg.locator(f"#{e} tbody tr:has(td)").nth(r + 1).locator("td").nth(c)

    for e in ["df_mdraw", "df_raw"]:
        pg.locator("#" + e).scroll_into_view_if_needed(); pg.wait_for_timeout(800)
        pg.locator("#" + e).screenshot(path=os.path.join(P, f"{e}.png"))
        res[e + "_r3c3"] = td(e, 3, 3).inner_html().replace("\n", " ")[:400]
        res[e + "_r4c3"] = td(e, 4, 3).inner_html().replace("\n", " ")[:400]
    res["xss_counter_total"] = pg.evaluate("window.__xss || 0")

    for e in ["df_md", "df_html"]:
        pg.locator("#" + e).scroll_into_view_if_needed(); pg.wait_for_timeout(500)
        c = td(e, 0, 3)
        c.click(force=True); pg.wait_for_timeout(300)
        c.dblclick(force=True); pg.wait_for_timeout(700)
        inp = c.locator("input")
        res[e + "_edit_input_value"] = inp.input_value() if inp.count() else None
        pg.locator("#" + e).screenshot(path=os.path.join(P, f"{e}_editing.png"))
        pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
        # also confirm the plain text column (col 2) is editable in the same table
    pg.locator("#df_sty_i").scroll_into_view_if_needed(); pg.wait_for_timeout(500)
    res["sty_i_r0c2_style"] = td("df_sty_i", 0, 2).get_attribute("style")
    pg.locator("#df_sty_n").scroll_into_view_if_needed(); pg.wait_for_timeout(500)
    res["sty_n_r0c2_style"] = td("df_sty_n", 0, 2).get_attribute("style")
    b.close()
print(json.dumps(res, ensure_ascii=False, indent=1))
