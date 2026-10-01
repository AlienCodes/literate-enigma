from pathlib import Path

p = Path('<仓库>/.claude/worktrees/wf_08725f86-d54-11/voicetwin/webui/app.py')
s = p.read_text(encoding='utf-8')


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:80], s.count(old))
    s = s.replace(old, new)


rep('''        fn = getattr(wf, "choose_variant", None)
        if callable(fn):
            fn(self.cfg, v, st.get("report", ""), str(name))
        elif st.get("audio"):
            shutil.copyfile(str(chosen["path"]), st["audio"])
            try:
                rp = Path(st.get("report", ""))
                data = json.loads(rp.read_text(encoding="utf-8"))
                data["final"] = str(name)
                rp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            except Exception:
                pass
        i = vs.index(chosen)
        title = _variant_title(chosen, i)
        return (_upd(value=str(chosen["path"]), label=f"结果（{title}）"),
                f"✅ 已改用{_md_text(title.split('（')[0])}：`{str(st.get('audio', '')).replace('`', '')}` 现在就是这个版本。")''',
    '''        res = wf.choose_variant(self.cfg, v, st.get("report", ""), str(name)) or {}
        final = str(res.get("audio") or st.get("audio") or "")
        i = vs.index(chosen)
        title = _variant_title(chosen, i)
        # 播放器放版本自己的文件：最终文件名没变，浏览器可能还在用旧的缓存
        return (_upd(value=str(chosen["path"]), label=f"结果（{title}）"),
                f"✅ 已改用{_md_text(title.split('（')[0])}：`{final.replace('`', '')}` 现在就是这个版本。")''')
rep('''    def train_plan_preview(self, voice: Any, backend: Any = None) -> str:
        """训练前就显示电脑会怎么自动选参数（U3/U4 提供 wf.training_plan 时显示具体数字）。"""
        v = _voice_name(voice)
        fn = getattr(wf, "training_plan", None)
        if v and callable(fn):
            try:
                plan = fn(self.cfg, v, backend or self.default_train)
                text = plan if isinstance(plan, str) else _plan_text({"plan": plan})
                if text:
                    return "🧠 **电脑会自动这样训练**：" + _md_text(text) + "（想自己改，可以打开下面的「高级设置」）"
            except Exception as exc:
                log.debug(f"training_plan 出错：{exc}")
        return PLAN_DEFAULT''',
    '''    def train_plan_preview(self, voice: Any, backend: Any = None, s_ep: Any = 0, g_ep: Any = 0, bs: Any = 0,
                           dpo: Any = "auto") -> str:
        """训练前就显示电脑会怎么自动选参数（wf.training_plan：看显卡和素材，只读文件和 nvidia-smi，很快）。"""
        v = _voice_name(voice)
        if v:
            try:
                text = wf.training_plan(self.cfg, v, str(backend or self.default_train),
                                        **self._train_opts(s_ep, g_ep, 0, bs, dpo))
                if text:
                    return ("🧠 **电脑会自动这样训练**：" + _md_text(_strip_plan(text))
                            + "（想自己改，可以打开下面的「高级设置」）")
            except Exception as exc:
                log.debug(f"training_plan 出错：{exc}")
        return PLAN_DEFAULT''')
rep('''    def do_train(self, voice: Any, backend: Any, s_ep: Any, g_ep: Any, q_ep: Any, bs: Any) -> Iterator[Tuple[Any, ...]]:
        opts = {"sovits_epochs": _int(s_ep) or None, "gpt_epochs": _int(g_ep) or None, "epochs": _int(q_ep) or None,
                "batch_size": _int(bs) or None}
        yield from self._train_common("train", voice, backend, opts)''',
    '''    @staticmethod
    def _train_opts(s_ep: Any, g_ep: Any, q_ep: Any, bs: Any, dpo: Any = "auto") -> Dict[str, Any]:
        """高级设置 → 训练选项（0 / 空 = 自动，交给引擎按显卡和素材决定）。"""
        opts: Dict[str, Any] = {"sovits_epochs": _int(s_ep) or None, "gpt_epochs": _int(g_ep) or None,
                                "epochs": _int(q_ep) or None, "batch_size": _int(bs) or None}
        d = str(dpo or "auto").strip().lower()
        opts["if_dpo"] = True if d == "on" else (False if d == "off" else None)
        return opts

    def do_train(self, voice: Any, backend: Any, s_ep: Any, g_ep: Any, q_ep: Any, bs: Any,
                 dpo: Any = "auto") -> Iterator[Tuple[Any, ...]]:
        yield from self._train_common("train", voice, backend, self._train_opts(s_ep, g_ep, q_ep, bs, dpo))''')
p.write_text(s, encoding='utf-8')
print("ok")
