"""Real-browser smoke test of the integrated VoiceTwin web UI (gradio 4.24) on port 7876.

Writes screenshots to scratchpad/integ_shots/ and prints one CHECK line per verification.
"""
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:7890/"
OUT = "<草稿目录>/integ_shots"
os.makedirs(OUT, exist_ok=True)
RESULTS = []
ONLY = set(sys.argv[1:])  # optional: run only some steps, e.g. "a b"


def check(name, ok, info=""):
    RESULTS.append((name, bool(ok)))
    print(f"[{time.time() % 1000:.1f}] CHECK {'PASS' if ok else 'FAIL'} {name} {info}".rstrip(), flush=True)


def shot(page, name, locator=None, pad=12, full=False):
    path = os.path.join(OUT, name)
    if locator is None:
        page.screenshot(path=path, full_page=full)
    else:
        locator.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        box = locator.bounding_box()
        if box is None:
            page.screenshot(path=path)
        else:
            vp = page.viewport_size
            sy = page.evaluate("window.scrollY")  # bounding_box 相对视口；full_page 截图的 clip 相对整页
            clip = {"x": max(0, box["x"] - pad), "y": max(0, box["y"] + sy - pad),
                    "width": min(vp["width"], box["width"] + 2 * pad), "height": box["height"] + 2 * pad}
            page.screenshot(path=path, clip=clip, full_page=True)
    print("saved", path, flush=True)
    return path


def union(page, locators, pad=12):
    boxes = [lc.bounding_box() for lc in locators]
    boxes = [b for b in boxes if b]
    x0 = min(b["x"] for b in boxes) - pad
    y0 = min(b["y"] for b in boxes) - pad
    x1 = max(b["x"] + b["width"] for b in boxes) + pad
    y1 = max(b["y"] + b["height"] for b in boxes) + pad
    return {"x": max(0, x0), "y": max(0, y0), "width": min(1280, x1) - max(0, x0), "height": y1 - max(0, y0)}


def shot_union(page, name, locators, pad=12):
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    clip = union(page, locators, pad)
    path = os.path.join(OUT, name)
    page.screenshot(path=path, clip=clip, full_page=True)
    print("saved", path, flush=True)


def visible_bar(page):
    return page.locator(".vt-prog:visible").first


def bar_state(page):
    bar = visible_bar(page)
    if not bar.count():
        return None, None, None
    try:
        return bar.get_attribute("data-status"), bar.get_attribute("data-level"), int(bar.get_attribute("data-pct") or 0)
    except Exception:
        return None, None, None


def run_id(page):
    bar = visible_bar(page)
    try:
        return bar.get_attribute("data-run") if bar.count() else None
    except Exception:
        return None


def wait_bar(page, statuses, timeout_s, mid_shot=None, mid_min_pct=1, old_run="__none__"):
    """Wait until the visible bar (of a run other than `old_run`) reaches one of `statuses`."""
    t0 = time.time()
    took_mid = False
    seen_running = False
    while time.time() - t0 < timeout_s:
        st, level, pct = bar_state(page)
        if old_run != "__none__" and run_id(page) == old_run:
            time.sleep(0.3)
            continue
        if st == "running":
            seen_running = True
            if mid_shot and not took_mid and pct is not None and pct >= mid_min_pct:
                shot(page, mid_shot, visible_bar(page))
                took_mid = True
                print(f"  mid-run: status={st} level={level} pct={pct}", flush=True)
        if st in statuses:
            return st, level, pct, seen_running, took_mid
        time.sleep(0.4)
    return None, None, None, seen_running, took_mid


def wait_text(page, text, timeout_s):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if page.get_by_text(text, exact=False).count() > 0:
            return True
        time.sleep(0.5)
    return False


def bar_color(page):
    return page.evaluate("""() => {
        const bar = [...document.querySelectorAll('.vt-prog')].find(e => e.offsetParent !== null);
        if (!bar) return null;
        const fill = bar.querySelector('.vt-fill');
        return fill ? getComputedStyle(fill).backgroundColor + ' | ' + getComputedStyle(fill).backgroundImage.slice(0, 60) : null;
    }""")


def real_table(page, text):
    # gradio 4.24 的 Dataframe 里有一张隐藏的「量宽度」表（第一张），真正显示数据的是第二张
    return page.locator("table").filter(has_text=text).nth(1)


def table_first_col(page, table_locator):
    cells = table_locator.locator("tbody tr td:first-child")
    out = []
    for i in range(min(cells.count(), 50)):
        out.append(cells.nth(i).inner_text().strip())
    return out


def all_runs(page):
    return set(page.evaluate("() => [...document.querySelectorAll('.vt-prog')].map(e => e.dataset.run)"))


def wait_new_done(page, old_runs, timeout_s):
    """Wait until any visible bar of a run not in old_runs reaches done/error/stopped; return its status."""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        states = page.evaluate("""() => [...document.querySelectorAll('.vt-prog')].filter(e => e.offsetParent !== null)
            .map(e => [e.dataset.status, e.dataset.run, e.dataset.pct])""")
        for st, run, pct in states:
            if run not in old_runs and st in ("done", "error", "stopped"):
                return st, int(pct or 0)
        time.sleep(0.4)
    return None, None


def step(key):
    return not ONLY or key in ONLY


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 1000}, device_scale_factor=2)
    pg.on("pageerror", lambda e: print(f"  [pageerror {time.time() % 1000:.1f}]", str(e)[:200], flush=True))
    if os.environ.get("TRIM_HOOK"):
        pg.on("console", lambda m: print(f"  [console {time.time() % 1000:.1f}]", m.text[:300], flush=True)
              if ("TRIMCALL" in m.text or "SSEMSG" in m.text) else None)
        pg.add_init_script("""(() => { const ES = window.EventSource; window.EventSource = function (u, o) { const es = new ES(u, o);
            es.addEventListener('message', (ev) => { try { const d = JSON.parse(ev.data);
              if (d.msg === 'process_generating' || d.msg === 'process_completed' || d.msg === 'process_starts')
                console.log('SSEMSG ' + d.msg + ' ' + d.event_id.slice(0, 6) + ' n=' + (d.output && d.output.data ? d.output.data.length : -1) + ' ' + (d.output && d.output.data ? d.output.data.map((x, i) => i + ':' + JSON.stringify(x).slice(0, 60)).join(' || ') : '')); } catch (e) {} });
            return es; }; window.EventSource.prototype = ES.prototype; })();""")
        pg.add_init_script("""Object.defineProperty(Array.prototype, 'trim', {configurable: true, writable: true,
            value: function () { console.log('TRIMCALL ' + JSON.stringify(this).slice(0, 200)); return ''; }});""")
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(3500)

    # ------------------------------------------------------------------ (a) header
    if step("a"):
        header = pg.locator(".vt-header").first
        check("a.version_in_header", "声音分身 VoiceTwin v0.1.6" in header.inner_text(), header.inner_text()[:60])
        badge = pg.locator(".vt-gpu").first
        wait_text(pg, "显卡", 20)
        cls = badge.get_attribute("class") if badge.count() else ""
        check("a.gpu_badge_error_in_sandbox", badge.count() and "vt-gpu-error" in (cls or ""),
              (badge.inner_text()[:80] if badge.count() else "no badge"))
        lib = pg.get_by_text("我的声音库（共", exact=False).first
        check("a.voice_library_header", lib.count() > 0, lib.inner_text() if lib.count() else "")
        shot(pg, "a_header_gpu_library.png", None)

    # ------------------------------------------------------------------ (b) prepare
    if step("b"):
        v = pg.get_by_label("声音名称（新建请直接输入名字）")
        v.click()
        v.fill("我的声音")
        v.press("Enter")
        pg.keyboard.press("Escape")
        pg.get_by_placeholder("例如 D:\\讲课视频").fill("D:\\讲课素材")
        pg.mouse.click(5, 5)
        pg.wait_for_timeout(500)
        pg.get_by_role("button", name="开始准备素材").click()
        st, level, pct, seen, mid = wait_bar(pg, ("done", "error", "stopped"), 900, mid_shot="b1_prepare_running.png")
        check("b.prepare_bar_seen_running", seen and mid)
        check("b.prepare_done", st == "done", f"status={st} level={level} pct={pct}")
        pg.wait_for_timeout(2500)
        bar = visible_bar(pg)
        check("b.done_bar_text", "全部完成" in bar.inner_text(), bar.inner_text()[:80])
        print("  done bar color:", bar_color(pg))
        shot(pg, "b2_prepare_done.png", bar)
        md = pg.get_by_text("素材准备好了", exact=False).first
        check("b.summary_md", md.count() > 0)
        count = pg.locator(".vt-md").filter(has_text="📊").first
        ctext = re.sub(r"\s+", " ", count.inner_text()) if count.count() else ""
        check("b.count_line", bool(re.search(r"一共 \d+ 条片段", ctext)), ctext[:120])
        clips = real_table(pg, "可能有错（红色）")
        check("b.suspect_column", clips.count() > 0)
        firsts = table_first_col(pg, clips)
        check("b.table_numbered_from_1", firsts[:3] == ["1", "2", "3"], str(firsts[:5]))
        if count.count():
            count.scroll_into_view_if_needed()
            pg.wait_for_timeout(400)
            box = count.bounding_box()
            sy = pg.evaluate("window.scrollY")
            pg.screenshot(path=os.path.join(OUT, "b3_count_and_table.png"),
                          clip={"x": 0, "y": max(0, box["y"] + sy - 20), "width": 1280, "height": 900}, full_page=True)
            print("saved b3_count_and_table.png")
        # summary (numbered references / drop reasons)
        if md.count():
            shot(pg, "b4_prepare_summary.png", pg.locator(".vt-md").filter(has_text="素材准备好了").first)

    # ------------------------------------------------------------------ (c) proofcheck
    if step("c"):
        import subprocess
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "inject_typos.py")], check=True)
        pg.get_by_role("button", name="🔄 重新载入").click()
        pg.wait_for_timeout(2500)
        btn = pg.get_by_role("button", name="🔍 自动查找可能的错字")
        check("c.proof_button_visible", btn.count() > 0 and btn.is_visible())
        old = all_runs(pg)
        btn.click()
        st, pct = wait_new_done(pg, old, 600)
        check("c.proofcheck_done", st == "done", f"status={st} pct={pct}")
        pg.wait_for_timeout(2000)
        res = pg.get_by_text("检查完了", exact=False).first
        check("c.proofcheck_message", res.count() > 0, res.inner_text()[:120] if res.count() else "")
        shot_union(pg, "c_proofcheck_done.png",
                   [visible_bar(pg), pg.locator(".vt-md").filter(has_text="检查完了").first])
        count = pg.locator(".vt-md").filter(has_text="📊").first
        print("  count after proofcheck:", re.sub(r"\s+", " ", count.inner_text())[:160] if count.count() else "")
        red = pg.locator("table span[style*='#dc2626']")
        print("  red spans in table:", red.count())
        check("c.red_marks_present", red.count() > 0, f"{red.count()} red spans")
        if red.count():
            pg.get_by_label("只看可能有错的").check()
            pg.wait_for_timeout(2500)
            tbl = real_table(pg, "可能有错（红色）")
            n_rows = tbl.locator("tbody tr").count()
            check("c.filter_only_suspects", 0 < n_rows < 20, f"{n_rows} rows after filter")
            shot_union(pg, "c2_red_marked_rows.png", [pg.locator(".vt-md").filter(has_text="📊").first, tbl])
            tbl.locator("tbody tr").first.locator("td").nth(5).click()
            pg.wait_for_timeout(2500)
            diff = pg.locator(".vt-diff").first
            check("c.diff_panel", diff.count() > 0 and diff.is_visible(), diff.inner_text()[:120] if diff.count() else "")
            if diff.count():
                shot(pg, "c3_diff_panel.png", diff)

    # ------------------------------------------------------------------ (d) training
    if step("d"):
        pg.get_by_role("tab", name="② 训练模型").click()
        pg.wait_for_timeout(2000)
        plan = pg.get_by_text("电脑会自动这样训练", exact=False).first
        check("d.plan_preview", plan.count() > 0, plan.inner_text()[:140] if plan.count() else "")
        pg.get_by_role("button", name="开始训练").click()
        st, level, pct, seen, mid = wait_bar(pg, ("done", "error", "stopped"), 1500, mid_shot="d1_train_running.png",
                                             mid_min_pct=10)
        check("d.train_bar_seen_running", seen and mid)
        check("d.train_done", st == "done", f"status={st} level={level} pct={pct}")
        pg.wait_for_timeout(2500)
        shot_union(pg, "d2_train_done.png", [visible_bar(pg), pg.locator(".vt-md").filter(has_text="训练完成").first,
                                             pg.locator(".vt-md").filter(has_text="训练方案").first])
        done_md = pg.get_by_text("训练完成", exact=False).first
        check("d.train_done_md", done_md.count() > 0)

    # ------------------------------------------------------------------ (e) generation
    if step("e"):
        pg.get_by_role("tab", name="③ 生成讲课音频").click()
        pg.wait_for_timeout(1200)
        pg.get_by_placeholder("大家好，今天我们来学习……").fill(
            "大家好，欢迎回来。今天我们来学习生成器表达式。那么它和列表推导式有什么区别呢？我们一起来看一个例子。")
        pg.mouse.click(5, 5)
        checked = pg.evaluate("""() => [...document.querySelectorAll('input[type=radio]:checked')]
            .filter(e => e.offsetParent !== null)
            .map(e => e.closest('label') ? e.closest('label').innerText.trim() : e.value)""")
        print("  checked radios on 3:", checked)
        check("e.default_quality_balanced_without_gpu", any(c.startswith("均衡") for c in checked), str(checked))
        shot(pg, "e0_generate_tab.png", None, full=True)
        pg.get_by_role("button", name="生成", exact=True).click()
        st, level, pct, seen, mid = wait_bar(pg, ("done", "error", "stopped"), 900, mid_shot="e1_generate_running.png")
        check("e.generate_bar_seen_running", seen)
        check("e.generate_done", st == "done", f"status={st} pct={pct}")
        pg.wait_for_timeout(2500)
        shot_union(pg, "e2_generate_done.png", [visible_bar(pg), pg.locator(".vt-md").filter(has_text="生成好了").first])
        gen_table = real_table(pg, "像你本人（%）")
        firsts = table_first_col(pg, gen_table)
        check("e.result_table_1_based", firsts[:2] == ["1", "2"], str(firsts))
        gen_table.scroll_into_view_if_needed()
        shot(pg, "e3_result_table.png", gen_table)

    # ------------------------------------------------------------------ (f) environment check
    if step("f"):
        pg.get_by_role("tab", name="🩺 环境检查").click()
        ok = wait_text(pg, "共 ", 120) and wait_text(pg, "项需要处理", 60) or wait_text(pg, "一切正常", 5)
        pg.wait_for_timeout(1500)
        doc = pg.locator("table").filter(has_text="说明").filter(has_text="项目").nth(1)
        firsts = table_first_col(pg, doc)
        check("f.doctor_table_numbered", firsts[:3] == ["1", "2", "3"], str(firsts[:6]))
        total = pg.get_by_text(re.compile(r"^共 \d+ 项$")).first
        check("f.doctor_total", total.count() > 0, total.inner_text() if total.count() else "")
        shot(pg, "f_doctor.png", None)

    # ------------------------------------------------------------------ (g) forced error → red bar
    if step("g"):
        pg.get_by_role("tab", name="③ 生成讲课音频").click()
        pg.wait_for_timeout(1000)
        pg.get_by_placeholder("大家好，今天我们来学习……").fill("…… ！！ ——")
        pg.mouse.click(5, 5)
        old = run_id(pg)
        pg.get_by_role("button", name="生成", exact=True).click()
        st, level, pct, seen, mid = wait_bar(pg, ("error", "done", "stopped"), 300, old_run=old)
        check("g.error_bar", st == "error", f"status={st} level={level}")
        pg.wait_for_timeout(1500)
        print("  error bar color:", bar_color(pg))
        bar = visible_bar(pg)
        btext = bar.inner_text()
        check("g.error_bar_has_advice", "怎么办" in btext, btext[:160].replace("\n", " / "))
        err_md = pg.locator(".vt-md").filter(has_text="生成没有完成").first
        check("g.friendly_md", err_md.count() > 0, err_md.inner_text()[:120] if err_md.count() else "")
        shot_union(pg, "g_error_red_bar.png", [bar] + ([err_md] if err_md.count() else []))

    # ------------------------------------------------------------------ (h) extra: machine verification (⑤)
    if step("h"):
        tab5 = pg.get_by_role("tab", name="⑤ 鉴别")
        print("  tab5 box before click:", tab5.bounding_box(), "scrollY", pg.evaluate("window.scrollY"))
        tab5.click()
        pg.wait_for_timeout(800)
        sel = pg.evaluate("() => [...document.querySelectorAll('button[role=tab]')].filter(e => e.getAttribute('aria-selected') === 'true').map(e => e.innerText)")
        print("  selected after 1st click:", sel)
        if "⑤ 鉴别" not in "".join(sel):
            tab5.click()
            pg.wait_for_timeout(800)
            sel = pg.evaluate("() => [...document.querySelectorAll('button[role=tab]')].filter(e => e.getAttribute('aria-selected') === 'true').map(e => e.innerText)")
            print("  selected after 2nd click:", sel)
        info = pg.evaluate("""() => ({tabs: [...document.querySelectorAll('button[role=tab]')].map(e => e.innerText.trim()
                + (e.getAttribute('aria-selected') === 'true' ? ' *' : '')),
            btns: [...document.querySelectorAll('button')].filter(e => e.offsetParent !== null)
                .map(e => e.innerText.trim().slice(0, 20)).filter(t => t.length < 20)})""")
        print("  before verify:", info)
        old = all_runs(pg)
        pg.get_by_role("button", name="开始鉴别").click()
        st, pct = wait_new_done(pg, old, 600)
        check("h.verify_done", st == "done", f"status={st}")
        pg.wait_for_timeout(1500)
        vt = real_table(pg, "综合 %")
        firsts = table_first_col(pg, vt)
        check("h.verify_table_numbered", firsts[:2] == ["1", "2"], str(firsts[:5]))
        shot_union(pg, "h_verify.png", [visible_bar(pg), pg.locator(".vt-md").filter(has_text="鉴别完成").first, vt])

    # ------------------------------------------------------------------ (j) extra: 完美 tier → two versions
    if step("j"):
        pg.get_by_role("tab", name="③ 生成讲课音频").click()
        pg.wait_for_timeout(1000)
        pg.get_by_placeholder("大家好，今天我们来学习……").fill("同学们好，今天讲一个新的例子。请大家先想一想。")
        pg.mouse.click(5, 5)
        pg.locator("label", has_text="完美：每句最多试 20 次").first.click()
        pg.wait_for_timeout(500)
        old = run_id(pg)
        pg.get_by_role("button", name="生成", exact=True).click()
        st, level, pct, seen, mid = wait_bar(pg, ("done", "error", "stopped"), 1500, mid_shot="j1_perfect_running.png",
                                             old_run=old)
        check("j.perfect_done", st == "done", f"status={st} pct={pct}")
        pg.wait_for_timeout(2500)
        var_md = pg.locator(".vt-md").filter(has_text="这次做了两个版本").first
        check("j.two_versions_md", var_md.count() > 0 and "⭐ 推荐" in var_md.inner_text(),
              var_md.inner_text()[:200].replace("\n", " / ") if var_md.count() else "")
        labels = pg.evaluate("""() => [...document.querySelectorAll('label')].filter(e => e.offsetParent !== null)
            .map(e => e.innerText.trim()).filter(t => t.startsWith('版本 '))""")
        print("  version labels:", labels)
        check("j.version_players", any("未去杂音" in x for x in labels) and any(x.startswith("版本 B") for x in labels))
        box = pg.locator(".vt-md").filter(has_text="这次做了两个版本").first
        sy_target = box.element_handle().evaluate_handle("e => e.closest('.form, .gr-group, .block') || e").as_element()
        shot(pg, "j2_two_versions.png", pg.locator("div").filter(has=box).filter(has_text="最终使用哪个版本").last)
        pg.locator("label", has_text="版本 B").last.click()
        ok = wait_text(pg, "已改用版本 B", 60)
        check("j.choose_variant_b", ok)
        pg.wait_for_timeout(1000)
        shot(pg, "j3_chose_b.png", pg.locator("div").filter(has=box).filter(has_text="最终使用哪个版本").last)

    # back to top: library now has the voice
    if step("a") or step("b"):
        pg.evaluate("window.scrollTo(0, 0)")
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(3500)
        lib = pg.get_by_text("我的声音库（共", exact=False).first
        check("a.voice_library_after_prepare", "共 1 个" in (lib.inner_text() if lib.count() else ""),
              lib.inner_text() if lib.count() else "")
        lib_table = real_table(pg, "最后修改时间")
        firsts = table_first_col(pg, lib_table)
        check("a.library_numbered", firsts[:1] == ["1"], str(firsts))
        shot(pg, "a2_header_after_tasks.png", None)
    b.close()

failed = [n for n, ok in RESULTS if not ok]
print(f"SUMMARY {len(RESULTS) - len(failed)}/{len(RESULTS)} passed; failed: {failed}")
