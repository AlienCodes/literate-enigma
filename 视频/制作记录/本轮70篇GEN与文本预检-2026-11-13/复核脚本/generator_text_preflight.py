#!/usr/bin/env python3
"""Freeze current JSON as pure S/out GEN data; round-trip and text-check in a disposable mirror.

Does nothing when imported. Run only after root has merged current summaries/fonts.
Writes source only with --publish-generators, and then only genNN.py after an exact
JSON-value round-trip through the unmodified shared 核对.生成并核对 helper.
No audio/video/PDF production, checker changes, stamp changes, push, or dispatch.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import pprint
import re
import shutil
import subprocess
import sys
import tarfile

ROOT_DEFAULT = Path('/workspace/work/github-publication/target')
PAY_DEFAULT = Path('/workspace/work/video-audit70-20261113/payload')
CORE_FILES = ('视频/工具/初稿生成/核对.py', '视频/工具/踩坑核查.py',
              '视频/工具/check_all.py', '视频/工具/新管/印章.py')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_pointer(parts):
    return '' if not parts else '/' + '/'.join(str(p).replace('~', '~0').replace('/', '~1') for p in parts)


def differences(expected, actual, parts=()):
    """Every changed JSON leaf, with precise RFC6901 path and full values."""
    result = []
    if type(expected) is not type(actual):
        return [{'path': json_pointer(parts), 'reason': 'type_or_value',
                 'expected': expected, 'actual': actual}]
    if isinstance(expected, dict):
        for key in sorted(expected.keys() | actual.keys()):
            if key not in expected:
                result.append({'path': json_pointer(parts+(key,)), 'reason': 'unexpected_field', 'actual': actual[key]})
            elif key not in actual:
                result.append({'path': json_pointer(parts+(key,)), 'reason': 'missing_field', 'expected': expected[key]})
            else:
                result.extend(differences(expected[key], actual[key], parts+(key,)))
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            result.append({'path': json_pointer(parts), 'reason': 'list_length',
                           'expected_length': len(expected), 'actual_length': len(actual)})
        for index in range(max(len(expected), len(actual))):
            if index >= len(expected):
                result.append({'path': json_pointer(parts+(index,)), 'reason': 'unexpected_item', 'actual': actual[index]})
            elif index >= len(actual):
                result.append({'path': json_pointer(parts+(index,)), 'reason': 'missing_item', 'expected': expected[index]})
            else:
                result.extend(differences(expected[index], actual[index], parts+(index,)))
    elif expected != actual:
        result.append({'path': json_pointer(parts), 'reason': 'value', 'expected': expected, 'actual': actual})
    return result


def pure_generator(data):
    """Encode only values the unchanged helper can represent. Never repair derived fields."""
    issues = []
    S = []
    if not isinstance(data.get('sentences'), list) or not data['sentences']:
        return None, [{'path': '/sentences', 'reason': 'missing_or_empty_sentences'}]
    for si, sentence in enumerate(data['sentences']):
        prefix = ('sentences', si)
        for key in sentence.keys() - {'para', 'chunks'}:
            issues.append({'path': json_pointer(prefix+(key,)), 'reason': 'shared_helper_cannot_emit_sentence_field', 'expected': sentence[key]})
        if 'para' not in sentence or not isinstance(sentence.get('chunks'), list):
            issues.append({'path': json_pointer(prefix), 'reason': 'invalid_sentence_schema'})
            continue
        chunks = []
        for ci, chunk in enumerate(sentence['chunks']):
            cp = prefix+('chunks', ci)
            for key in chunk.keys() - {'en', 'zh', 'align', 'note'}:
                issues.append({'path': json_pointer(cp+(key,)), 'reason': 'shared_helper_cannot_emit_chunk_field', 'expected': chunk[key]})
            align = chunk.get('align')
            if not isinstance(align, list) or not all(isinstance(p,list) and len(p)==2 and all(isinstance(v,str) for v in p) for p in align):
                issues.append({'path': json_pointer(cp+('align',)), 'reason': 'invalid_align_schema', 'expected': align})
                continue
            # These are the exact original helper expressions, with no normalization.
            en = ' '.join(a for a,b in align if a != '\n')
            zh = ''.join(b for a,b in align)
            for field, derived in (('en', en), ('zh', zh)):
                if chunk.get(field) != derived:
                    issues.append({'path': json_pointer(cp+(field,)), 'reason': 'derived_from_align_differs_do_not_guess',
                                   'expected': chunk.get(field), 'shared_helper_would_emit': derived})
            entry = [[tuple(pair) for pair in align]]
            if 'note' in chunk:
                entry.append(chunk['note'])
            chunks.append(entry)
        S.append((sentence['para'], chunks))
    if issues:
        return None, issues
    out = copy.deepcopy(data)
    out['sentences'] = []
    pretty = lambda value: pprint.pformat(value, width=112, sort_dicts=False)
    text = ('#!/usr/bin/env python3\n'
            '# Pure data frozen from the current approved JSON; shared helper/checkers unchanged.\n'
            'import os\nimport sys\n\nS = '+pretty(S)+'\n\nout = '+pretty(out)+'\n\n'
            'sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n'
            'from 核对 import 生成并核对\n'
            '生成并核对(S, out)\n')
    return text, []


def snapshot_repository(baseline, mirror):
    """Copy exact HEAD blobs from local materialized files first; avoid cold archive fetches."""
    raw = subprocess.check_output(['git','ls-tree','-r','-z','HEAD'],cwd=baseline)
    backup = Path('/workspace/work/audit-repo')
    prefixes = ('视频/工具/','视频/脚本/','视频/对照文本/','视频/工作进度/','新版定稿/')
    counts = {'baseline_verified':0,'audit_repo_verified':0,'git_blob_fallback':0}
    for record in raw.split(b'\0'):
        if not record: continue
        metadata, filename = record.split(b'\t',1)
        mode, kind, oid = metadata.decode().split()
        rel = filename.decode()
        record_source = rel.startswith('视频/制作记录/') and ('旧简述清理' not in rel and '/待修改/' not in rel)
        wanted = rel.startswith(prefixes) or record_source or rel in ('CLAUDE.md','AGENTS.md','README.md') or (rel.startswith('视频/') and rel.count('/')==1 and rel.endswith('.md'))
        if not wanted or kind != 'blob': continue
        if record_source and Path(rel).suffix.lower() in ('.mp4','.wav','.mp3','.png','.jpg','.pdf','.zip'): continue
        data = None
        if mode != '120000':
            for root, label in ((baseline,'baseline_verified'),(backup,'audit_repo_verified')):
                candidate = root/rel
                if candidate.is_file():
                    value = candidate.read_bytes()
                    fingerprint = hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()
                    if fingerprint == oid:
                        data=value;counts[label]+=1;break
        if data is None:
            data=subprocess.check_output(['git','show','HEAD:'+rel],cwd=baseline)
            counts['git_blob_fallback']+=1
        target=mirror/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if mode == '120000':
            link=data.decode();resolved=(target.parent/link).resolve()
            if not resolved.is_relative_to(mirror.resolve()):
                raise RuntimeError('Snapshot symlink would leave isolated mirror: '+rel)
            target.symlink_to(link)
        else:
            target.write_bytes(data)
            if mode == '100755': target.chmod(0o755)
    (mirror.parent/'snapshot-sources.json').write_text(json.dumps(counts,indent=2)+'\n')
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=baseline,text=True).strip()


def overlay_current_data(source, mirror):
    copied = []
    groups = [('视频/脚本','**/*.json'), ('新版定稿','*.md'),
              ('视频/制作记录','*.md'), ('视频/制作记录','*.json'),
              ('视频/工具/初稿生成','gen[0-9][0-9].py')]
    for folder, pattern in groups:
        root = source/folder
        if not root.exists():
            continue
        for item in sorted(root.glob(pattern)):
            if item.is_file():
                rel = item.relative_to(source)
                target = mirror/rel
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(item,target)
                copied.append(str(rel))
    agreement = source/'视频/工具/用户同意记录.json'
    if agreement.is_file():
        shutil.copyfile(agreement,mirror/'视频/工具/用户同意记录.json')
        copied.append('视频/工具/用户同意记录.json')
    return copied


def current_file(baseline, payload, mirror, rel):
    for root in (payload, baseline, mirror):
        item = root/rel
        if item.is_file():
            return item
    raise FileNotFoundError(rel)


def article_markdown(baseline, payload, mirror, no):
    for root in (payload, baseline, mirror):
        matches = list((root/'新版定稿').glob(no+'-*.md'))
        if matches:
            if len(matches) != 1:
                raise RuntimeError(f'{root}: article{no} has multiple current manuscripts: {matches}')
            return matches[0]
    raise FileNotFoundError('新版定稿/'+no+'-*.md')


def pending_requirements(mirror, no, gate_text):
    path = mirror/f'视频/制作记录/{no}_待改清单.md'
    if not path.exists():
        return []
    result = []
    for line_number, line in enumerate(path.read_text().splitlines(),1):
        for kind, text in re.findall(r'(画面上要有|英文要有|画面上不要有)[：:]\s*`([^`]+)`',line):
            result.append({'path':f'视频/制作记录/{no}_待改清单.md','line':line_number,
                           'kind':kind,'text':text,
                           'reported_missing_by_original_gate':f'{kind}：{text[:40]}' in gate_text})
    return result


def execute(command, cwd, env, log):
    with log.open('w') as stream:
        result = subprocess.run(list(map(str,command)),cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT)
    return result.returncode, log.read_text(errors='replace')


def parse_ids(items):
    values=[]
    for item in items:
        for part in item.split(','):
            if part.lower() == 'all':
                values.extend(range(1,71))
            elif '-' in part:
                a,b=map(int,part.split('-',1));values.extend(range(a,b+1))
            else:
                values.append(int(part))
    assert values and all(1<=n<=70 for n in values)
    return sorted({f'{n:02}' for n in values})


def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--baseline',type=Path,default=ROOT_DEFAULT)
    ap.add_argument('--payload',type=Path,default=PAY_DEFAULT)
    ap.add_argument('--ids',nargs='+',required=True,help='After summary merge: e.g. 01,03,05 or all or01-70')
    ap.add_argument('--run-dir',type=Path)
    ap.add_argument('--python',default=sys.executable)
    ap.add_argument('--text-gates',action='store_true',help='Run original 踩坑核查.py NN 出片 in mirror, without audio/render production')
    ap.add_argument('--text-stage',choices=('出片','文本'),default='出片')
    ap.add_argument('--publish-generators',action='store_true',help='Write only successful exact GEN data back to payload')
    args=ap.parse_args()
    baseline=args.baseline.resolve();payload=args.payload.resolve();ids=parse_ids(args.ids)
    when=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run_dir=(args.run_dir or PAY_DEFAULT.parent/f'generator-text-preflight-{when}').resolve()
    run_dir.mkdir(parents=True,exist_ok=False)
    mirror=run_dir/'mirror';mirror.mkdir()
    logs=run_dir/'logs';logs.mkdir()
    prepared=run_dir/'generators';prepared.mkdir()
    report={'status':'running','ids':ids,'baseline':str(baseline),'payload':str(payload),
            'run_dir':str(run_dir),'scope':'JSON to pure S/out GEN + original text gates only',
            'mechanical_repair':'Original 修.py after GEN exact; original text gate recorded before/after; repaired JSON saved only for root review, never copied to payload',
            'shared_helper_or_checkers_changed':False,'production_json_changed':False,
            'audio_video_pdf_produced':False,'push_or_dispatch':False,
            'generator_publish_requested':args.publish_generators,'articles':[],
            'final_public_source_contract':'After official production, publish actual W/scripts/NN.json after L19/T38 auto fixes and synchronize MD/GEN from that final JSON; do not overwrite it with original request bytes.'}
    report_file=run_dir/'report.json'
    save=lambda:report_file.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    save()
    report['baseline_commit']=snapshot_repository(baseline,mirror)
    original_hashes={rel:digest(mirror/rel) for rel in CORE_FILES}
    report['baseline_current_data_overlaid']=overlay_current_data(baseline,mirror)
    report['payload_current_data_overlaid']=overlay_current_data(payload,mirror)
    work=mirror/'_text-preflight-work';work.mkdir();(work/'scripts').mkdir()
    for source in (mirror/'视频/脚本').glob('[0-9][0-9].json'):
        shutil.copyfile(source,work/'scripts'/source.name)
    fonts=work/'fonts';fonts.symlink_to(mirror/'视频/工具/fonts',target_is_directory=True)
    resource_fonts=mirror/'视频/资源/字体';resource_fonts.parent.mkdir(parents=True,exist_ok=True)
    if not resource_fonts.exists():resource_fonts.symlink_to(mirror/'视频/工具/fonts',target_is_directory=True)
    env={**os.environ,'XG_P':str(mirror),'XG_TOOLS':str(mirror/'视频/工具'),
         'XG_WORK':str(work),'PYTHONDONTWRITEBYTECODE':'1','VIDEO_S':'1'}
    env['PATH']=str(Path(args.python).absolute().parent)+os.pathsep+env.get('PATH','')
    for key in ('YAOWENBEN','AUDIO_ONLY','OLD_IV_VOID'):
        env.pop(key,None)
    for no in ids:
        row={'article':no,'generator_roundtrip_exact':False,'generator_published':False}
        report['articles'].append(row);save()
        try:
            rel=Path(f'视频/脚本/{no}.json')
            source=current_file(baseline,payload,mirror,rel)
            row['source_path']=str(source);row['source_sha256']=digest(source)
            expected=json.loads(source.read_text())
            if source.resolve() != (mirror/rel).resolve():
                shutil.copyfile(source,mirror/rel)
            md=article_markdown(baseline,payload,mirror,no)
            md_bytes=md.read_bytes()
            for old in (mirror/'新版定稿').glob(no+'-*.md'):
                old.unlink()
            target_md=mirror/'新版定稿'/md.name;target_md.write_bytes(md_bytes)
            row['manuscript_path']=str(md);row['manuscript_sha256']=hashlib.sha256(md_bytes).hexdigest()
            target_gen=mirror/f'视频/工具/初稿生成/gen{no}.py'
            row['old_generator_sha256']=digest(target_gen) if target_gen.exists() else None
            text,issues=pure_generator(expected);row['source_fields_needing_guessing']=issues
            if text is not None:
                candidate=prepared/f'gen{no}.py';candidate.write_text(text)
                shutil.copyfile(candidate,target_gen)
                # Clean generation proves all metadata is in out, not inherited from old work state.
                generated=work/f'scripts/{no}.json'
                if generated.exists():generated.unlink()
                code,stdout=execute([args.python,target_gen],work,env,logs/f'{no}-generator.log')
                row['generator_exit_code']=code;row['generator_stdout']=stdout
                if generated.exists():
                    got=json.loads(generated.read_text());row['roundtrip_differences']=differences(expected,got)
                    row['generator_roundtrip_exact']=not row['roundtrip_differences'] and code==0
                else:
                    row['roundtrip_differences']=[{'path':'/','reason':'original_helper_emitted_no_json'}]
                row['new_generator_sha256']=digest(candidate)
                if args.publish_generators and row['generator_roundtrip_exact']:
                    if digest(source)!=row['source_sha256']:
                        raise RuntimeError('Current input changed during preflight; no generator published.')
                    destination=payload/f'视频/工具/初稿生成/gen{no}.py'
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(candidate,destination);row['generator_published']=True
            # Original text gate always receives the exact current input, even when derived fields disagree.
            (work/f'scripts/{no}.json').write_bytes(source.read_bytes())
            row['allow_clash']=expected.get('allow_clash',[])
            if args.text_gates:
                code,stdout=execute([args.python,mirror/'视频/工具/踩坑核查.py',no,args.text_stage],work,env,logs/f'{no}-text-gate.log')
                row['text_gate_exit_code']=code
                row['text_hard_errors']=[line.strip()[1:].strip() for line in stdout.splitlines() if line.strip().startswith('✘')]
                row['text_pending_confirmations']=[line.strip()[1:].strip() for line in stdout.splitlines() if line.strip().startswith('？')]
                row['checker_selftest_failure']=('核查程序失灵' in stdout or '【失灵】' in stdout)
                row['text_gate_exception_tail']=stdout.splitlines()[-30:] if code and not row['text_hard_errors'] else []
                row['pending_checklist_requirements']=pending_requirements(mirror,no,stdout)
                row['raw_text_gate_log']=str(logs/f'{no}-text-gate.log')
                row['raw_text_gate_exit_code']=row['text_gate_exit_code']
                row['raw_text_hard_errors']=row['text_hard_errors']
                row['raw_text_pending_confirmations']=row['text_pending_confirmations']
                row['raw_checker_selftest_failure']=row['checker_selftest_failure']
                row['raw_text_gate_exception_tail']=row['text_gate_exception_tail']
                row['raw_pending_checklist_requirements']=row['pending_checklist_requirements']
                before_repair=json.loads((work/f'scripts/{no}.json').read_text())
                repair_code,repair_stdout=execute([args.python,mirror/'视频/工具/新管/修.py',no],work,env,logs/f'{no}-mechanical-repair.log')
                after_repair=json.loads((work/f'scripts/{no}.json').read_text())
                row['mechanical_repair_exit_code']=repair_code
                row['mechanical_repair_stdout']=repair_stdout
                row['mechanical_repair_errors']=[line for line in repair_stdout.splitlines() if line.startswith('错：')]
                row['mechanical_repair_differences']=differences(before_repair,after_repair)
                reviewed=run_dir/'auto-repaired-sources';reviewed.mkdir(exist_ok=True)
                reviewed_source=reviewed/f'{no}.json';shutil.copyfile(work/f'scripts/{no}.json',reviewed_source)
                row['auto_repaired_source_for_root_review']=str(reviewed_source)
                row['auto_repaired_source_sha256']=digest(reviewed_source)
                code,stdout=execute([args.python,mirror/'视频/工具/踩坑核查.py',no,args.text_stage],work,env,logs/f'{no}-text-gate-after-repair.log')
                row['text_gate_exit_code']=code
                row['text_hard_errors']=[line.strip()[1:].strip() for line in stdout.splitlines() if line.strip().startswith('✘')]
                row['text_pending_confirmations']=[line.strip()[1:].strip() for line in stdout.splitlines() if line.strip().startswith('？')]
                row['checker_selftest_failure']=('核查程序失灵' in stdout or '【失灵】' in stdout)
                row['text_gate_exception_tail']=stdout.splitlines()[-30:] if code and not row['text_hard_errors'] else []
                row['pending_checklist_requirements']=pending_requirements(mirror,no,stdout)
                row['text_gate_log']=str(logs/f'{no}-text-gate-after-repair.log')
            row['input_json_still_unchanged']=digest(source)==row['source_sha256']
        except Exception as exc:
            row['error']=str(exc)
        save()
        print(no+': GEN '+('exact' if row['generator_roundtrip_exact'] else 'needs data review')+
              ('; text exit '+str(row.get('text_gate_exit_code')) if args.text_gates else ''),flush=True)
    report['core_hashes_before']=original_hashes
    report['core_hashes_after']={rel:digest(mirror/rel) for rel in CORE_FILES}
    report['core_unchanged']=report['core_hashes_before']==report['core_hashes_after']
    report['status']='passed' if report['core_unchanged'] and all(
        row['generator_roundtrip_exact'] and not row.get('error') and row.get('input_json_still_unchanged')
        and (not args.text_gates or row.get('text_gate_exit_code')==0) for row in report['articles']) else 'needs_data_review'
    report['exact_generators']=[row['article'] for row in report['articles'] if row['generator_roundtrip_exact']]
    report['published_generators']=[row['article'] for row in report['articles'] if row['generator_published']]
    save();print(report_file,flush=True)
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
