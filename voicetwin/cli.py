"""命令行入口：voicetwin <命令> …  （运行 voicetwin -h 查看全部命令）"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List, Optional

from voicetwin import __version__
from voicetwin.config import load_config, update_config_file, write_example_config

EPILOG = """
常用流程（把「我的声音」换成你喜欢的名字）：
  1. voicetwin doctor                                   检查环境
  2. voicetwin prepare -v 我的声音 -i D:/讲课视频        从视频/录音准备素材（自动识别文字）
  3. （可选）用 Excel 打开 workspace/我的声音/transcripts.csv 校对文字，然后 voicetwin review -v 我的声音
  4. voicetwin train -v 我的声音                         训练（GPT-SoVITS），完成后自动挑选最像的模型
  5. voicetwin narrate -v 我的声音 第1课讲稿.md          生成讲课音频 + 字幕
  或者一条命令全自动：voicetwin auto -v 我的声音 -i D:/讲课视频
  网页界面：voicetwin webui
"""


def _parse_redo(value: str) -> List[int]:
    out: List[int] = []
    for part in (value or "").replace("，", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def _print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="voicetwin", description=f"VoiceTwin 声音分身 v{__version__}：复刻你的音色、语气和节奏（中文+英文）",
                                 epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-c", "--config", help="配置文件路径（默认使用当前目录的 config.yaml）")
    ap.add_argument("--verbose", action="store_true", help="输出更详细的日志")
    # --verbose 放在子命令前后都可以（例如 voicetwin narrate ... --verbose）
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--verbose", action="store_true", default=argparse.SUPPRESS, help="输出更详细的日志和完整错误信息")
    sub = ap.add_subparsers(dest="command", metavar="<命令>")
    _add = sub.add_parser
    sub.add_parser = lambda *a, **kw: _add(*a, parents=[common], **kw)  # type: ignore[method-assign]

    def voice_arg(p: argparse.ArgumentParser) -> None:
        p.add_argument("-v", "--voice", required=True, help="声音名称，例如：我的声音")

    def backend_arg(p: argparse.ArgumentParser) -> None:
        p.add_argument("-b", "--backend", choices=["gptsovits", "qwen3tts", "indextts", "dummy"],
                       help="合成引擎（默认看 config.yaml 的 backend）")

    p = sub.add_parser("init-config", help="在当前目录生成可编辑的 config.yaml")
    p.add_argument("--gptsovits-root", help="GPT-SoVITS（或整合包）所在目录")
    p.add_argument("--workspace", help="数据存放目录（默认 ./workspace）")
    p.add_argument("--backend", choices=["gptsovits", "qwen3tts", "indextts"], help="默认引擎")
    p.add_argument("--force", action="store_true", help="重新生成 config.yaml（旧文件备份为 config.yaml.bak）")
    sub.add_parser("doctor", help="检查运行环境、显卡和各引擎是否就绪")
    sub.add_parser("list", help="列出已有的声音")

    p = sub.add_parser("prepare", help="从视频/录音准备训练素材（提取、清理、切片、识别、过滤）")
    voice_arg(p)
    p.add_argument("-i", "--input", nargs="+", required=True, help="视频/音频文件或文件夹（可多个）")
    p.add_argument("--asr", choices=["faster-whisper", "funasr", "none"], help="识别引擎")
    p.add_argument("--asr-model", help="识别模型，如 large-v3 / paraformer-zh")
    p.add_argument("--language", choices=["auto", "zh", "en"], help="素材语言（默认逐段自动判断）")
    p.add_argument("--denoise", choices=["auto", "on", "off"], help="降噪")
    p.add_argument("--separate-vocals", action="store_true", help="去除背景音乐（需要 demucs）")
    p.add_argument("--segmentation", choices=["auto", "srt", "energy"], help="切分方式")

    p = sub.add_parser("review", help="读回 transcripts.csv 里的人工校对结果")
    voice_arg(p)

    p = sub.add_parser("analyze", help="重新分析说话风格（语速、停顿、音高、响度）")
    voice_arg(p)

    p = sub.add_parser("train", help="用你的素材微调模型，完成后自动挑选最佳模型并校准语速")
    voice_arg(p)
    backend_arg(p)
    p.add_argument("--sovits-epochs", type=int, help="GPT-SoVITS：SoVITS 训练轮数（默认自动）")
    p.add_argument("--gpt-epochs", type=int, help="GPT-SoVITS：GPT 训练轮数（默认自动）")
    p.add_argument("--batch-size", type=int, help="批大小（默认按显存自动）")
    p.add_argument("--epochs", type=int, help="Qwen3-TTS：微调轮数")
    p.add_argument("--no-select", action="store_true", help="训练后不自动挑选模型")

    p = sub.add_parser("select", help="用验证集自动挑选最像你的模型，并校准语速")
    voice_arg(p)
    backend_arg(p)
    p.add_argument("--items", type=int, default=12, help="用多少条验证句（默认 12）")
    p.add_argument("--asr", dest="asr", action="store_true", default=None, help="同时用识别模型检查错字")
    p.add_argument("--no-asr", dest="asr", action="store_false")

    for name, helptext in (("say", "合成一句话/一段话"), ("narrate", "把讲稿（txt/md/srt/docx）合成为完整讲课音频")):
        p = sub.add_parser(name, help=helptext)
        voice_arg(p)
        backend_arg(p)
        p.add_argument("text" if name == "say" else "script", help="要说的文字" if name == "say" else "讲稿文件路径")
        p.add_argument("-o", "--output", help="输出文件（.wav 或 .mp3），默认保存到 workspace/声音名/outputs/")
        p.add_argument("-q", "--quality", choices=["fast", "balanced", "best"], help="质量档位")
        p.add_argument("-n", "--candidates", type=int, help="每句生成几个候选（覆盖质量档位）")
        p.add_argument("--speed", type=float, help="语速倍数（默认 1.0 = 和你本人一样）")
        p.add_argument("--ref", default="", help="指定参考音频 id（见 references.json）")
        p.add_argument("--asr-check", dest="asr_check", action="store_true", default=None, help="用识别模型检查漏字")
        if name == "narrate":
            p.add_argument("--redo", default="", help="重新生成指定的句子，如 3,5,8-10")
            p.add_argument("--no-srt", action="store_true", help="不输出字幕")

    p = sub.add_parser("evaluate", help="评估一段音频有多像你")
    voice_arg(p)
    p.add_argument("audio", help="音频文件")
    p.add_argument("--text", default="", help="音频对应的文字（提供后会检查错字）")

    p = sub.add_parser("auto", help="全自动：准备素材 → 训练 → 挑最佳模型 → 生成试听")
    voice_arg(p)
    backend_arg(p)
    p.add_argument("-i", "--input", nargs="+", required=True, help="视频/音频文件或文件夹")
    p.add_argument("--skip-train", action="store_true", help="不训练，只用零样本克隆")

    p = sub.add_parser("mux", help="把生成的讲解音频放进视频（替换原音轨）")
    p.add_argument("--video", required=True)
    p.add_argument("--audio", required=True)
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--keep-original", action="store_true", help="保留原音轨并混音")

    p = sub.add_parser("download-models", help="下载 GPT-SoVITS 缺失的预训练模型")
    p.add_argument("--source", choices=["auto", "hf", "hf-mirror"], default="auto", help="下载源（国内推荐 hf-mirror）")

    p = sub.add_parser("clear-cache", help="清空某个声音的句子缓存")
    voice_arg(p)

    p = sub.add_parser("webui", help="启动网页界面")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7860)
    p.add_argument("--share", action="store_true", help="生成公网分享链接（注意隐私）")
    return ap


def main(argv: Optional[List[str]] = None) -> None:
    ap = build_parser()
    args = ap.parse_args(argv)
    if not args.command:
        ap.print_help()
        return
    if args.command == "init-config":
        repl = {}
        if args.gptsovits_root:
            repl["backends.gptsovits.root"] = str(Path(args.gptsovits_root).expanduser().resolve()).replace("\\", "/")
        if args.workspace:
            repl["workspace"] = args.workspace
        if args.backend:
            repl["backend"] = args.backend
        path = Path.cwd() / "config.yaml"
        if path.exists() and not args.force:
            if repl:
                done = {}
                for key, value in repl.items():
                    try:
                        update_config_file(path, {key: value})
                        done[key] = value
                    except KeyError:
                        print(f"⚠️ {path} 里没有 {key} 这一项，已跳过（可手动添加）")
                if done:
                    print(f"已更新 {path}：" + "，".join(f"{k} = {v}" for k, v in done.items()) + "（其余设置保持不变）")
            else:
                print(f"{path} 已存在，保持不变（加 --force 可重新生成，旧文件会备份为 config.yaml.bak）。")
            return
        write_example_config(path, repl, overwrite=args.force)
        print(f"已生成 {path}，按需修改即可。")
        return
    import logging

    from voicetwin.utils.log import setup_logging

    setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    cfg = load_config(args.config)
    from voicetwin import workflows as wf

    try:
        if args.command == "doctor":
            for row in wf.doctor(cfg):
                print(f"{row['status']} {row['item']}：{row['detail']}")
        elif args.command == "list":
            voices = wf.list_voices(cfg)
            if not voices:
                print("还没有任何声音。先运行：voicetwin prepare -v 我的声音 -i 你的视频文件夹")
            for v in voices:
                print(f"- {v['voice']}：{v['minutes']} 分钟素材，{v['clips']} 条片段；已训练：{', '.join(v['trained']) or '无'}")
        elif args.command == "prepare":
            overrides: dict = {}
            asr: dict = {}
            if args.asr:
                asr["engine"] = args.asr
            if args.asr_model:
                asr["model"] = args.asr_model
            if args.language:
                asr["language"] = args.language
            if asr:
                overrides["asr"] = asr
            if args.denoise:
                overrides["denoise"] = args.denoise
            if args.separate_vocals:
                overrides["separate_vocals"] = True
            if args.segmentation:
                overrides["segmentation"] = args.segmentation
            summary = wf.run_prepare(cfg, args.voice, args.input, overrides=overrides)
            _print_summary(summary)
        elif args.command == "review":
            summary = wf.apply_review(cfg, args.voice)
            print(f"已同步修改：{summary['changed']}")
            _print_summary(summary)
        elif args.command == "analyze":
            wf.run_analyze(cfg, args.voice)
        elif args.command == "train":
            opts = {"sovits_epochs": args.sovits_epochs, "gpt_epochs": args.gpt_epochs, "batch_size": args.batch_size,
                    "epochs": args.epochs}
            info = wf.run_train(cfg, args.voice, args.backend, select=not args.no_select, **opts)
            print(f"训练完成（用时 {info.get('train_minutes')} 分钟）。默认模型：{(info.get('selected') or {}).get('id')}")
        elif args.command == "select":
            info = wf.run_select(cfg, args.voice, args.backend, items=args.items, use_asr=args.asr)
            _print_json({"best": info["selection"]["best"], "speed": info["speed"]})
        elif args.command in ("say", "narrate"):
            source = args.text if args.command == "say" else args.script
            if args.command == "narrate" and not Path(source).exists():
                raise FileNotFoundError(f"找不到讲稿文件：{source}")
            res = wf.run_narrate(cfg, args.voice, source, out=args.output, backend_name=args.backend,
                                 quality=args.quality, candidates=args.candidates, speed=args.speed, reference=args.ref,
                                 redo=_parse_redo(getattr(args, "redo", "")),
                                 subtitles=False if getattr(args, "no_srt", False) or args.command == "say" else None,
                                 asr_check=args.asr_check)
            print(f"\n✅ 音频：{res.audio_path}（{res.duration:.1f} 秒）")
            if res.srt_path:
                print(f"   字幕：{res.srt_path}")
            print(f"   报告：{res.report_path}")
            for w in res.warnings[:20]:
                print(f"   ⚠️ {w}")
        elif args.command == "evaluate":
            from voicetwin.synth.select import evaluate_file

            project = wf.open_project(cfg, args.voice, must_exist=True)
            _print_json(evaluate_file(cfg, project, Path(args.audio), args.text))
        elif args.command == "auto":
            result = wf.run_auto(cfg, args.voice, args.input, args.backend, skip_train=args.skip_train)
            _print_summary(result["prepare"])
            print(f"\n✅ 全部完成！试听：{result['demo']}")
        elif args.command == "mux":
            from voicetwin.utils.ffmpeg import mux_audio_into_video

            out = mux_audio_into_video(Path(args.video), Path(args.audio), Path(args.output), args.keep_original)
            print(f"✅ 已生成 {out}")
        elif args.command == "download-models":
            from voicetwin.backends.gptsovits import GPTSoVITSBackend
            from voicetwin.project import Project

            backend = GPTSoVITSBackend(cfg, Project(cfg, "__download__"))
            files = backend.download_pretrained(args.source)
            import shutil

            shutil.rmtree(backend.project.root, ignore_errors=True)
            print(f"✅ 已下载 {len(files)} 个文件" if files else "✅ 预训练模型已齐全")
        elif args.command == "clear-cache":
            from voicetwin.synth.engine import clear_cache

            n = clear_cache(wf.open_project(cfg, args.voice, must_exist=True))
            print(f"已清除 {n} 条缓存")
        elif args.command == "webui":
            from voicetwin.webui.app import launch

            launch(cfg, host=args.host, port=args.port, share=args.share)
    except KeyboardInterrupt:
        print("\n已取消。")
        sys.exit(130)
    except Exception as exc:
        if args.verbose:
            raise
        print(f"\n❌ {exc}\n（加 --verbose 查看详细错误信息）", file=sys.stderr)
        sys.exit(1)


def _print_summary(s: dict) -> None:
    print(f"\n素材：保留 {s['clips_kept']}/{s['clips_total']} 条，共 {s['minutes_kept']} 分钟 {s.get('minutes_by_lang', {})}")
    if s.get("dropped"):
        print("丢弃原因：" + "，".join(f"{k} {v} 条" for k, v in s["dropped"].items()))
    for w in s.get("warnings", []):
        print(f"⚠️ {w}")
    if s.get("transcripts_csv"):
        print(f"校对表：{s['transcripts_csv']}（修改后运行 voicetwin review -v {s['voice']}）")


if __name__ == "__main__":
    main()
