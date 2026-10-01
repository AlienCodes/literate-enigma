from pathlib import Path

W = Path('<仓库>/.claude/worktrees/wf_08725f86-d54-11')


def patch(rel, pairs):
    p = W / rel
    s = p.read_text(encoding='utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (rel, old[:80], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, encoding='utf-8')


patch('voicetwin/webui/app.py', [
    ('''PCT_HELP = "「像你本人」的百分比：100% = 和你自己的真实录音一样像。低于 85% 的会被自动淘汰或标红。"''',
     '''PCT_HELP = ("「像你本人」的百分比：100% = 和你自己的真实录音一样像。"
            "有可靠的声纹模型时，低于 85% 的会被自动淘汰或标红。")
MFCC_NOTE = ("⚠️ 这次没有可靠的声纹模型（只有简易的 MFCC），百分比只能粗略参考，也不会按 85% 自动淘汰。"
             "GPT-SoVITS 整合包里自带的声纹模型能用时会自动用上。")'''),
    ('''def _train_done_md(info: Dict[str, Any], plan: str = "") -> str:''',
     '''def _train_done_md(info: Dict[str, Any], plan: str = "", show_plan: bool = True) -> str:
    """训练完成的说明。show_plan=False：训练页上方已经单独显示了训练方案，这里不再重复。"""'''),
    ('''    plan_md = _plan_md(plan or _plan_text(info))''',
     '''    plan_md = _plan_md(plan or _plan_text(info)) if show_plan else ""'''),
    ('''                md = _train_done_md(info, plan)''', '''                md = _train_done_md(info, plan, show_plan=False)'''),
    # generation summary: honest note when similarity filter is off (MFCC only)
    ('''    mean = _mean_pct(res)
    sims = [x for x in (_num(s.get("speaker_sim")) for s in segs) if x is not None]
    if mean is not None:
        md.append(f"整体听起来：像你本人 **{mean:.1f}%**（每句的平均）")''',
     '''    mean = _mean_pct(res)
    sims = [x for x in (_num(s.get("speaker_sim")) for s in segs) if x is not None]
    if mean is not None:
        md.append(f"整体听起来：像你本人 **{mean:.1f}%**（每句的平均）")
        if _report_field(res, "similarity_filter") is False:
            md.append(MFCC_NOTE)'''),
    ('''def _variants(res: Any) -> List[Dict[str, Any]]:''',
     '''def _report_field(res: Any, key: str) -> Any:
    """读这次生成报告（*.report.json）里的一个字段；读不到时返回 None。"""
    path = getattr(res, "report_path", None)
    try:
        if path and Path(str(path)).exists():
            return json.loads(Path(str(path)).read_text(encoding="utf-8")).get(key)
    except Exception:
        pass
    return None


def _variants(res: Any) -> List[Dict[str, Any]]:'''),
    # verify: readable names + MFCC note
    ('''def _verify_rows(result: Dict[str, Any]) -> Tuple[List[List[Any]], str]:
    """机器鉴别结果 → 按综合 % 从高到低排名的表格（#、文件、各模型 %、综合 %、排名、是否 ≥85%）+ 总结。"""''',
     '''def _verify_rows(result: Dict[str, Any], labels: Optional[Dict[str, str]] = None) -> Tuple[List[List[Any]], str]:
    """机器鉴别结果 → 按综合 % 从高到低排名的表格（#、文件、各模型 %、综合 %、排名、是否 ≥85%）+ 总结。

    labels：{文件的绝对路径: 给老师看的名字}，例如单句音频显示成「第 2 句：今天我们……」而不是一串字母数字。"""
    labels = labels or {}'''),
    ('''        name = r.get("file") or Path(str(r.get("path") or "")).name
        table.append([i, Path(str(name)).name, "；".join(parts) or "—", _pct_text(pct), int(r.get("rank") or i), mark])''',
     '''        name = labels.get(str(r.get("path") or "")) or Path(str(r.get("file") or r.get("path") or "")).name
        table.append([i, name, "；".join(parts) or "—", _pct_text(pct), int(r.get("rank") or i), mark])'''),
    ('''    if result.get("calibrated") is False:
        lines.append("⚠️ 你的真实录音太少，百分比只能粗略参考。")''',
     '''    if result.get("calibrated") is False:
        lines.append("⚠️ 你的真实录音太少，百分比只能粗略参考。")
    elif info.get("reliable") is False:
        lines.append(MFCC_NOTE.replace("，也不会按 85% 自动淘汰", ""))'''),
    ('''def _report_audio_files(report: Dict[str, Any], project: Any = None, max_clips: int = 20) -> List[str]:''',
     '''def _report_labels(report: Dict[str, Any], project: Any = None) -> Dict[str, str]:
    """一次生成里每个音频文件 → 给老师看的名字（「版本 A：未去杂音」「第 3 句：……」）。"""
    out: Dict[str, str] = {}
    for i, v in enumerate(report.get("variants") or []):
        if isinstance(v, dict) and v.get("path"):
            out[str(v["path"])] = f"版本 {_variant_letter(v, i)}：{v.get('name') or ''}（{Path(str(v['path'])).name}）"
    if report.get("audio") and str(report["audio"]) not in out:
        out[str(report["audio"])] = f"整篇：{Path(str(report['audio'])).name}"
    if project is not None:
        for k, seg in enumerate(report.get("segments") or [], 1):
            clip = seg.get("clip") if isinstance(seg, dict) else None
            if clip:
                try:
                    text = str(seg.get("text") or "")
                    out[str(project.abspath(str(clip)))] = (f"第 {_seg_no(seg, k)} 句：{text[:16]}"
                                                            + ("…" if len(text) > 16 else ""))
                except Exception:
                    pass
    return out


def _report_audio_files(report: Dict[str, Any], project: Any = None, max_clips: int = 20) -> List[str]:'''),
    ('''        attach = self._attaching("verify", v)
        gen = _paths_of(generated)
        if not gen and not attach:
            st = state if isinstance(state, dict) else {}
            if st.get("voice") == v and st.get("report") and Path(st["report"]).exists():
                try:
                    gen = _report_audio_files(json.loads(Path(st["report"]).read_text(encoding="utf-8")), project)
                except Exception:
                    gen = []
            if not gen:
                gen = _report_audio_files(_latest_report(project), project)''',
     '''        attach = self._attaching("verify", v)
        gen = _paths_of(generated)
        labels: Dict[str, str] = {}
        if not gen and not attach:
            st = state if isinstance(state, dict) else {}
            report: Dict[str, Any] = {}
            if st.get("voice") == v and st.get("report") and Path(st["report"]).exists():
                try:
                    report = json.loads(Path(st["report"]).read_text(encoding="utf-8"))
                except Exception:
                    report = {}
            gen = _report_audio_files(report, project) if report else []
            if not gen:
                report = _latest_report(project)
                gen = _report_audio_files(report, project)
            labels = _report_labels(report, project)'''),
    ('''                table, md = _verify_rows(st.get("value") or {})''',
     '''                table, md = _verify_rows(st.get("value") or {}, labels)'''),
])
print("ok")
