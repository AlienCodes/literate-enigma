#!/usr/bin/env python3
"""05: repair evidence in the restored canonical cache; export only final video and QC summary."""
import copy,hashlib,importlib.util,inspect,json,os,re,shutil,subprocess,traceback
from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/"article05-delivery";OUT.mkdir(exist_ok=True)
M=Path(os.environ["RUNNER_TEMP"])/"completion-machine";W=M/"video";T=ROOT/"视频/工具"
LOG=M/"article05-local-logs";LOG.mkdir(exist_ok=True)
E={**os.environ,"XG_P":str(ROOT),"XG_TOOLS":str(T),"XG_WORK":str(W),"VIDEO_ROOT":str(M),"XG_NOPUSH":"1"}
E.pop("OLD_IV_VOID",None)
status={"article":"05","passed":False,"stage":"start","checks_unchanged":True}
def save(): (OUT/"05-status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n")
def run(args,cwd=W,env=E,log="run.log"):
    status["stage"]=log;save()
    with (LOG/log).open("w") as f:
        p=subprocess.run(list(map(str,args)),cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
    txt=(LOG/log).read_text(errors="replace")
    status.setdefault("check_summaries",{})[log]=[s.strip()[:650] for s in txt.splitlines() if s.startswith(("✔","✘","第05篇","①","②","③","④","⑤","⑥","【","配音指纹")) or " BAD " in s][-55:]
    save()
    if p.returncode:raise RuntimeError(f"{log}: exit {p.returncode}")
def md5(p):return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]
try:
    assert (W/"work_05/a.wav").exists(),"The original 05 machine cache was not restored."
    # Fonts required by canonical checks; the work cache already includes all models.
    target=ROOT/"视频/资源/字体"
    if not target.exists():
        target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(T/"fonts",target_is_directory=True)
    alias=Path("/home/user/postgraduate-vocabulary")
    if not alias.exists():
        subprocess.run(["sudo","mkdir","-p",str(alias.parent)],check=True)
        subprocess.run(["sudo","ln","-s",str(ROOT),str(alias)],check=True)
    current=W/"scripts/05.json";d=json.loads(current.read_text());startfp=md5(W/"work_05/a.wav")
    status["audio_input_md5"]=startfp;save()
    assert startfp=="1e25fbe69f6f",("Unexpected restored audio",startfp)
    # Reproduce the exact historical waveform before migrating its evidence.
    before=M/"preboost-reproduction";bw=before/"video";bw.mkdir(parents=True,exist_ok=True)
    if not (before/"tts").exists():(before/"tts").symlink_to(M/"tts",target_is_directory=True)
    for p in W.iterdir():
        if p.is_file() and p.suffix in (".py",".json",".txt"):shutil.copy2(p,bw/p.name)
    if not (bw/"fonts").exists():(bw/"fonts").symlink_to(W/"fonts",target_is_directory=True)
    shutil.copytree(W/"scripts",bw/"scripts",dirs_exist_ok=True)
    # The work-local pronunciation/context JSON files are part of the producer.
    # First reproduce the UNCHANGED full script as a strict positive control.
    (bw/"scripts/05.json").write_text(json.dumps(d,ensure_ascii=False,indent=1)+"\n")
    run(["python3","make_video.py","scripts/05.json","05-current-control.mp4"],cwd=bw,
        env={**E,"AUDIO_ONLY":"1","XG_WORK":str(bw)},log="reproduce-current-control.log")
    controlfp=md5(bw/"work_05/a.wav");status["reproduced_current_control_md5"]=controlfp;save()
    assert controlfp==startfp,"The original current voice did not reproduce; stop before migrating any evidence."
    original=copy.deepcopy(d);assert original.get("除阻加强")=={"S16":{"句末":[7.435,7.48,3.5]}}
    original.pop("除阻加强")
    (bw/"scripts/05.json").write_text(json.dumps(original,ensure_ascii=False,indent=1)+"\n")
    run(["python3","make_video.py","scripts/05.json","05-beforeboost.mp4"],cwd=bw,env={**E,"AUDIO_ONLY":"1","XG_WORK":str(bw)},log="reproduce-preboost.log")
    oldfp=md5(bw/"work_05/a.wav");status["reproduced_historical_waveform_md5"]=oldfp;save()
    assert oldfp=="ac01d01fcee3","Historical waveform did not reproduce exactly. Old evidence must not be relabelled."
    run(["python3",T/"确认平移.py","05",bw/"work_05/a.wav","--写入"],log="evidence-migration.log")
    d=json.loads(current.read_text());cf=d.setdefault("核对确认",{})
    assert md5(W/"work_05/a.wav")==startfp
    cf.setdefault("非人声",{}).update({
      "60.51–60.77s":{"配音指纹":startfp,"依据":"2026-11-12 核对当前 dossier_05.json id7 与原始声音逐2.5ms数值：S7 w 4.535–4.800s 位于 eighty-five 的 /v/ 词尾。4.535–4.695持续衰减且没有5ms低于-55dB的分界；4.705–4.775转为重心4.3–5.3kHz、150Hz以下-22至-38dB的清化擦音，4.800才降到-59.6dB。词尾摩擦完整保留，不作呼吸删除。主会话独立复核相同实际波形后认可此判定。"},
      "116.30–116.39s":{"配音指纹":startfp,"依据":"2026-11-12 核对当前 dossier_05.json id11 与原始声音逐2.5ms数值：S15 w 7.360–7.455s 在 police 的 /i:/ 到 /s/ 过渡内部；7.32元音-19.8dB后连续衰减至过渡-35至-48dB，7.45起摩擦连续增强，7.47重心5.3kHz，7.50为-22.1dB、5.9kHz。此段与后面的/s/连为一体，无静音边界，不删词内过渡。主会话独立复核相同实际波形后认可此判定。"}
    })
    cf.setdefault("删除段",{})["S15 raw 5.9500-6.1612"]={
      "类型":"紧贴词头的非人声","配音指纹":startfp,
      "依据":"2026-11-12 对当前原始合成与成片逐样本复核、逐5ms测量：S15 substitution 与 and 之间 raw 5.9500–6.16125s。前侧最低-59.6dB；被删除部分最响-43.0dB，主要是频谱重心2.2–2.7kHz、低频弱、周期大多<0.35的换气声，末端夹低频噗声。raw6.16125在过零点保留下一词；6.17开始的起音随后在6.18增强到约-22.6dB，是完整保留的and起音。post15ms最低-53.7dB的报警来自保留侧已经开始的词，不是被删去的词头；独立复核onset_cut_ms=0。只确认该已实际核实的非人声段，不改音频、不放宽任何门槛。"
    }
    points=[
      ["发现","杰弗里斯发现DNA标记的排列因人而异，提出DNA指纹，为辨认个人提供了新办法。"],
      ["洗冤","两名少女遇害后，DNA检验推翻了一名少年的认罪供词，并确认两案出自同一凶手。"],
      ["筛查","警方向五千多名男子采样，却无一吻合；真凶让同事冒名采样，躲过了筛查。"],
      ["破案","有人听见同事谈及顶替而举报；警方由此找到皮奇福克，再用DNA确认其涉案。"],
      ["结局","他认罪并获终身监禁，成为首位凭DNA证据被判谋杀罪者；这项技术先洗冤，后助定罪。"]
    ]
    c=d["sentences"][-1]["chunks"][-1];note=(c.get("note") or "").split("（简述：",1)[0].rstrip()
    c["note"]=(note+"\n" if note else "")+"（简述："+''.join("▸"+a+"："+b for a,b in points)+"）"
    current.write_text(json.dumps(d,ensure_ascii=False,indent=1)+"\n")
    run(["bash",T/"新管/做.sh","05","--不推"],log="canonical-draft.log")
    run(["bash",T/"新管/定稿.sh","05"],log="canonical-final4K.log")
    for group in ("做_05","定稿_05"):
        for name in ("出片前.log","出片后.log"):
            p=W/group/name
            if p.exists():
                lines=p.read_text(errors="replace").splitlines()
                status.setdefault("canonical_checks",{})[group+"/"+name]=[s.strip()[:650] for s in lines if s.startswith(("✔","✘","【")) or " BAD " in s]
    info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(W/"05.mp4")]))
    v=next(s for s in info["streams"] if s["codec_type"]=="video");assert(v["width"],v["height"])==(3840,2160)
    canonical_video=W/"05.mp4"
    canonical_sha=hashlib.sha256(canonical_video.read_bytes()).hexdigest()
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    assert md5(W/"work_05/a.wav")==startfp,"Voice changed unexpectedly during canonical production."
    status.update({"canonical_pipeline_passed":True,"canonical_video_sha256":canonical_sha,
                   "canonical_source_commit":commit,"stage":"exact-summary-transition"})
    save()
    # Reuse the same tested timing, old-card removal, freeze and verification
    # algorithm as the other 69 articles. Only its explicit source loader differs.
    module_file=ROOT/".github/video-batch/run.py"
    spec=importlib.util.spec_from_file_location("article05_exact_summary",module_file)
    batch=importlib.util.module_from_spec(spec);spec.loader.exec_module(batch)
    batch.OUT=M/"05-exact-summary";batch.OUT.mkdir(exist_ok=True)
    batch.BASE=commit
    batch.LOCAL05_SOURCE=str(canonical_video)
    batch.LOCAL05_SCRIPT=json.loads(current.read_text())
    body=inspect.getsource(batch.end_card)
    lo=body.index("    paths = tree_paths()")
    hi=body.index("    info = probe(source)")
    assert lo<hi and body.count("    paths = tree_paths()")==1
    loader=("    originals = ['new-canonical-4K:05']\n"
            "    source = OUT / f'{no}-original.mp4'\n"
            "    source.write_bytes(Path(LOCAL05_SOURCE).read_bytes())\n"
            "    data = copy.deepcopy(LOCAL05_SCRIPT)\n"
            "    changed = add_summary(data, no)\n")
    body=body[:lo]+loader+body[hi:]
    exec(compile(body,str(module_file)+"#05-explicit-canonical-source","exec"),batch.__dict__)
    with (LOG/"exact-summary.log").open("w") as log:
        from contextlib import redirect_stdout,redirect_stderr
        with redirect_stdout(log),redirect_stderr(log):batch.end_card("05")
    processed=list(batch.OUT.glob("*.mp4"));assert len(processed)==1,processed
    timing=json.loads((batch.OUT/"05-verification.json").read_text())
    timing.update({"source_kind":"new-canonical-4K","source":"canonical05 after original draft/final checks",
                   "source_commit":commit,"canonical_source_video_sha256":canonical_sha,
                   "canonical_pipeline_passed":True})
    assert timing["end_page_frames"]==60 and timing["end_page_seconds"]==2
    assert timing["original_audio_identical"] and timing["original_audio_packet_timings_identical"]
    final=OUT/"05-4K-读完即转简述2秒.mp4";shutil.copy2(processed[0],final)
    (OUT/"05-summary-verification.json").write_text(json.dumps(timing,ensure_ascii=False,indent=2)+"\n")
    status.update({"passed":True,"stage":"exact-transition-4K-passed","source_kind":"new-canonical-4K",
                   "resolution":[3840,2160],"audio_final_md5":md5(W/"work_05/a.wav"),
                   "voice_unchanged":True,"video_sha256":hashlib.sha256(final.read_bytes()).hexdigest(),
                   "video_frames":timing["output_frames"],"summary_seconds":2,
                   "summary_start_seconds":timing["summary_start_seconds"],
                   "delay_after_voice_seconds":timing["delay_after_voice_seconds"]})
    save();print(json.dumps(status,ensure_ascii=False),flush=True)
except Exception as exc:
    status["error"]=str(exc);status["passed"]=False
    for group in ("做_05","定稿_05"):
        for name in ("出片前.log","出片后.log"):
            p=W/group/name
            if p.exists():
                lines=p.read_text(errors="replace").splitlines()
                status.setdefault("canonical_checks",{})[group+"/"+name]=[s.strip()[:650] for s in lines if s.startswith(("✔","✘","【")) or " BAD " in s]
    save();print(json.dumps(status,ensure_ascii=False),flush=True);raise
