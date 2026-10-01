from pathlib import Path

p = Path(__file__).with_name('integ_check.py')
s = p.read_text(encoding='utf-8')
old = '''    # back to top: library now has the voice'''
new = '''    # ------------------------------------------------------------------ (j) extra: 完美 tier → two versions
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
              var_md.inner_text()[:200].replace("\\n", " / ") if var_md.count() else "")
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

    # back to top: library now has the voice'''
assert s.count(old) == 1
s = s.replace(old, new)
p.write_text(s, encoding='utf-8')
print("ok")
