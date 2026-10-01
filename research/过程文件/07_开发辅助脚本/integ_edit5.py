from pathlib import Path

W = Path('<仓库>/.claude/worktrees/wf_08725f86-d54-11')


def patch(rel, pairs):
    p = W / rel
    s = p.read_text(encoding='utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (rel, old[:80], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, encoding='utf-8')


patch('voicetwin/cli.py', [
    ('''def _cli_progress(kind: str, cfg: Any, title: str, backend: Optional[str] = None, select: bool = True) -> Any:
    """给命令行的长任务做一个进度回调：返回的对象可以当 progress(frac, msg) 用，并有 finish(ok)。"""''',
     '''def _cli_progress(kind: str, cfg: Any, title: str, backend: Optional[str] = None, select: bool = True,
                  **stage_kw: Any) -> Any:
    """给命令行的长任务做一个进度回调：返回的对象可以当 progress(frac, msg) 用，并有 finish(ok)。

    stage_kw 传给 wf.task_stages：生成时 quality=（「完美」档多一步），素材准备时 overrides=（会不会查错字）。"""'''),
    ('''        try:
            stages = task_stages(kind, cfg, backend, select=select) if kind == "train" else task_stages(kind, cfg, backend)
        except Exception:
            stages = None''',
     '''        try:
            stages = task_stages(kind, cfg, backend, select=select, **stage_kw)
        except TypeError:  # 老版本的 task_stages 不认识这些参数
            try:
                stages = task_stages(kind, cfg, backend)
            except Exception:
                stages = None
        except Exception:
            stages = None'''),
    ('''            progress = _cli_progress("prepare", cfg, "准备素材")''',
     '''            progress = _cli_progress("prepare", cfg, "准备素材", overrides=overrides)'''),
    ('''            opts = {"sovits_epochs": args.sovits_epochs, "gpt_epochs": args.gpt_epochs, "batch_size": args.batch_size,
                    "epochs": args.epochs}''',
     '''            opts = {"sovits_epochs": args.sovits_epochs, "gpt_epochs": args.gpt_epochs, "batch_size": args.batch_size,
                    "epochs": args.epochs, "if_dpo": {"on": True, "off": False}.get(str(args.dpo or "auto"))}'''),
    ('''            progress = _cli_progress("narrate", cfg, "生成音频", args.backend)''',
     '''            progress = _cli_progress("narrate", cfg, "生成音频", args.backend, quality=args.quality)'''),
    ('''    p.add_argument("--epochs", type=int, help="Qwen3-TTS：微调轮数")''',
     '''    p.add_argument("--epochs", type=int, help="Qwen3-TTS：微调轮数")
    p.add_argument("--dpo", choices=["auto", "on", "off"], default="auto",
                   help="GPT-SoVITS 的 DPO（实验功能）：auto = 显存 ≥22GB 且素材干净时才开（默认）")'''),
    ('''    print(f"\\n✅ 音频：{res.audio_path}（{res.duration:.1f} 秒）")''',
     '''    print(f"\\n✅ 音频：{res.audio_path}（{res.duration:.1f} 秒）")
    overall = getattr(res, "overall_pct", None)
    if isinstance(overall, (int, float)):
        print(f"   整篇像你本人 {float(overall):.1f}%（100% = 和你自己的真实录音一样像；声纹模型自动打分，最终以耳朵为准）")'''),
])

patch('voicetwin/default_config.yaml', [
    ('''      sovits_epochs: auto     # auto: 素材 <30 分钟用 8 轮，更多用 12 轮
      gpt_epochs: auto        # auto: 15 轮
      batch_size: auto        # auto: 按显存自动计算
      sovits_save_every: 4
      gpt_save_every: 5''',
     '''      # 下面都写 auto 就行：电脑按显卡（显存）和素材多少自动决定，训练开始时会打印一行「训练计划：……」说明为什么。
      # 想自己指定时填数字（网页「② 训练模型」→「高级设置」、命令行 --sovits-epochs 等也可以临时改）。
      sovits_epochs: auto     # auto: 素材 <30 分钟用 8 轮，更多用 12 轮（练太多反而会变差，训练完会自动挑最像的那一轮）
      gpt_epochs: auto        # auto: 15 轮
      batch_size: auto        # auto: 按显存自动计算（显存一半左右，最多 12；显存不够时会自动减半再试一次）
      sovits_save_every: auto # auto: 每个模型存 5 个左右，训练完从中自动挑最像你的（老版本的 4 / 5 也当作 auto）
      gpt_save_every: auto
      if_dpo: auto            # DPO（GPT-SoVITS 的实验功能）：auto = 显存 ≥22GB、素材干净、错字很少时才开；
                              # true 强制开（语气训练慢 2～4 倍，显存不够会出错），false 强制关'''),
])

for rel in ('pyproject.toml', 'voicetwin/__init__.py'):
    p = W / rel
    s = p.read_text(encoding='utf-8')
    assert '0.1.3' in s, rel
    p.write_text(s.replace('0.1.3', '0.1.6', 1), encoding='utf-8')
print("ok")
