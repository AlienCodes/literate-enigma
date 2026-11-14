#!/usr/bin/env python3
"""DRAFT: local validation/staging; explicit archive command publishes frozen reviewed files.
Never fetches media history. No network mutation occurs at import, validate, or stage.
"""
import argparse, base64, copy, datetime, hashlib, json, os, re, shutil, subprocess, sys
import urllib.error, urllib.parse, urllib.request
from fractions import Fraction
import tempfile, zipfile
from release_contract import pdf_reference, exact_assets, official_job_declaration, artifact_contents, tail_contract, book_illustrations, canonical_audio_contract, reviewed_canonical_audio_copy, post_quality_missing_art_recovery, ASSET_POLICY
from pathlib import Path, PurePosixPath

PRIMARY = ('alienalgorithm/postgraduate-vocabulary', 'main')
BACKUP = ('AlienCodes/literate-enigma', 'codex/all-deliverables-20261113')
PROGRAM_DIR = '成果归档/视频重制发布程序'
WORKFLOW = '.github/workflows/publish-video-revisions.yml'
MAX_BLOB = 100 * 1024 * 1024
HEX64 = re.compile(r'^[0-9a-f]{64}$')
HEX40 = re.compile(r'^[0-9a-f]{40}$')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def relpath(value):
    require(isinstance(value, str) and '\\' not in value, f'Invalid repository path: {value!r}')
    p = PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts and '.' not in p.parts, f'Unsafe path: {value}')
    require(not value.lower().endswith('.pdf'), f'PDF changes excluded: {value}')
    return value


def checked_file(spec, root=None):
    p = Path(spec['path'])
    if root is not None:
        p = Path(root) / relpath(spec['path'])
    require(p.is_file() and not p.is_symlink(), f'Missing actual regular file: {p}')
    require(HEX64.fullmatch(spec['sha256']) is not None, f'Missing SHA-256: {p}')
    require(digest(p) == spec['sha256'], f'SHA-256 mismatch: {p}')
    if 'bytes' in spec:
        require(p.stat().st_size == spec['bytes'], f'Byte count mismatch: {p}')
    return p


def command(args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def probe(path):
    d = json.loads(command(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v:0',
                            '-show_entries', 'stream=width,height,avg_frame_rate,nb_read_packets,nb_frames:format=duration',
                            '-of', 'json', str(path)]))
    require(len(d['streams']) == 1, f'No unique video stream: {path}')
    v = d['streams'][0]
    require((v['width'], v['height']) == (3840, 2160), f'Actual output is not 3840x2160: {path}')
    require(v['avg_frame_rate'] in ('30/1', '60/2'), f'Expected official 30fps output: {path}')
    frames = int(v.get('nb_frames') or v['nb_read_packets'])
    require(frames == int(v['nb_read_packets']), f'Frame/packet counts disagree: {path}')
    return {'width': v['width'], 'height': v['height'], 'frames': frames,
            'fps': v['avg_frame_rate'], 'duration_seconds': float(d['format']['duration'])}


def actual_aac(path):
    """Hash copied ADTS plus exact rational timestamp/payload/priming projection. Never rebase PTS."""
    raw = json.loads(command(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
        '-show_streams', '-show_packets', '-show_data_hash', 'sha256', '-of', 'json', str(path)]))
    require(len(raw.get('streams', [])) == 1, f'No unique actual audio stream: {path}')
    stream = raw['streams'][0]; require(stream['codec_name'] == 'aac', f'Expected copied AAC: {path}')
    timebase = Fraction(stream['time_base']); packets = []
    for pkt in raw['packets']:
        timing = []
        for key in ('pts', 'dts', 'duration'):
            require(key in pkt, f'Cannot prove exact packet {key}: {path}')
            value = int(pkt[key]) * timebase
            timing.append([value.numerator, value.denominator])
        side = [{k: s[k] for k in sorted(s) if k != 'side_data_size'} for s in pkt.get('side_data_list', [])]
        require(pkt.get('data_hash'), f'No actual packet payload hash: {path}')
        packets.append({'timing_rationals': timing, 'size': int(pkt['size']), 'payload_sha256': pkt['data_hash'], 'side_data': side})
    codec = {k: stream.get(k) for k in ('codec_name', 'profile', 'sample_rate', 'channels', 'channel_layout')}
    projection = {'codec': codec, 'packets': packets}
    encoded = json.dumps(projection, sort_keys=True, separators=(',', ':')).encode()
    with tempfile.TemporaryDirectory(prefix='actual-aac-') as td:
        adts = Path(td) / 'audio.aac'
        command(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-vn', '-c:a', 'copy', '-f', 'adts', str(adts)])
        return {'aac_adts_sha256': digest(adts), 'packet_projection_sha256': hashlib.sha256(encoded).hexdigest(),
                'packet_count': len(packets), 'projection': projection}


def visible_tokens(text, chinese=False):
    """Ignore wrapping/bold, while retaining display glosses and English word boundaries."""
    if chinese:
        # Only remove identifiers attached to a bold translated focus; keep ordinary (NASA) / prose.
        text = re.sub(r'\*\*([^*]+)\*\*\([^)]+\)', r'\1', text)
    text = text.replace('**', '').replace('▹', '')
    text = text.replace('{{一行}}', '').replace('{{=}}', '')
    text = re.sub(r'\{\{([^{}|]+)\|[^{}]+\}\}', r'\1', text)  # KEEP visible gloss text
    text = re.sub(r'(?m)^\s*@[A-Za-z][A-Za-z0-9 \'/-]*\|', '', text)  # repeated color-continuation key only
    return re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*|[^\s]", text)


def changed_json_paths(before, after, path=''):
    if type(before) != type(after): return [path]
    if isinstance(before, dict):
        result = []
        for key in sorted(set(before) | set(after)):
            child = path + '/' + str(key).replace('~', '~0').replace('/', '~1')
            result.extend([child] if key not in before or key not in after else changed_json_paths(before[key], after[key], child))
        return result
    if isinstance(before, list):
        if len(before) != len(after): return [path]
        return [value for i, (a, b) in enumerate(zip(before, after)) for value in changed_json_paths(a, b, path + '/' + str(i))]
    return [] if before == after else [path]


def source_invariants(request, final, n):
    require(len(request['sentences']) == len(final['sentences']), f'Sentence grouping changed: {n}')
    for si, (a, b) in enumerate(zip(request['sentences'], final['sentences'])):
        require(a['para'] == b['para'] and len(a['chunks']) == len(b['chunks']), f'Paragraph/chunk grouping changed: {n}/S{si+1}')
        for ci, (x, y) in enumerate(zip(a['chunks'], b['chunks'])):
            where = f'{n}/S{si+1}/C{ci+1}'
            require(visible_tokens(x['en']) == visible_tokens(y['en']), 'Visible English changed: ' + where)
            require(visible_tokens(x['zh'], True) == visible_tokens(y['zh'], True), 'Visible Chinese changed: ' + where)
            require(visible_tokens(x.get('note', ''), True) == visible_tokens(y.get('note', ''), True), 'Note/summary content changed: ' + where)
            for key in ('en', 'zh'):
                # T38 permits trailing 的 to join an adjective's bold range, no changed meaning.
                fx = re.findall(r'\*\*([^*]+)\*\*\(([^)]+)\)', x[key]) if key == 'zh' else re.findall(r'\*\*([^*]+)\*\*', x[key])
                fy = re.findall(r'\*\*([^*]+)\*\*\(([^)]+)\)', y[key]) if key == 'zh' else re.findall(r'\*\*([^*]+)\*\*', y[key])
                if key == 'zh':
                    fx = [(z.removesuffix('的'), word) for z, word in fx]; fy = [(z.removesuffix('的'), word) for z, word in fy]
                require(fx == fy, 'Focus pair/scope changed outside T38: ' + where)
            ax = [g for g in x.get('align', []) if g[0] != '\n']; ay = [g for g in y.get('align', []) if g[0] != '\n']
            require(len(ax) == len(ay), 'Non-layout alignment grouping changed: ' + where)
            for (e1, z1), (e2, z2) in zip(ax, ay):
                require(visible_tokens(e1) == visible_tokens(e2) and visible_tokens(z1, True) == visible_tokens(z2, True), 'Alignment content changed: ' + where)
    # The unchanged official maker consumes a pending line-wrap consent by
    # appending the exact quote to history. Verify that move without treating
    # other control metadata as freely editable or discarding the old quote.
    history_keys={'换行变更已获同意','换行变更记录'}
    if any(request.get(k)!=final.get(k)for k in history_keys):
        consent=request.get('换行变更已获同意');before=request.get('换行变更记录',[]);after=final.get('换行变更记录',[])
        require(isinstance(consent,dict)and consent and '换行变更已获同意'not in final and len(after)==len(before)+1 and after[:-1]==before and {k:v for k,v in after[-1].items()if k!='日期'}==consent and re.fullmatch(r'\d{4}-\d{2}-\d{2}',after[-1].get('日期','')),'Original wrap authorization/history lost or changed')
    req_meta={k:v for k,v in request.items()if k not in {'sentences','核对确认'}|history_keys}
    fin_meta={k:v for k,v in final.items()if k not in {'sentences','核对确认'}|history_keys}
    interval_fingerprint_updates=[]
    # A45 hashes are observed raw-synthesis validity records written by the
    # original maker. They do not specify gain, cuts, timing, or spoken text.
    # The genuine native artifact retains both sources; original audio gates
    # and the actual AAC comparison remain mandatory in validate_article.
    if req_meta.get('区间声音指纹')!=fin_meta.get('区间声音指纹'):
        def valid_raw_fingerprints(value):
            return value is None or (isinstance(value,dict) and all(
                isinstance(k,str) and re.fullmatch(r'S[1-9]\d*',k) and int(k[1:])<=len(final['sentences'])
                and isinstance(v,str) and re.fullmatch(r'[0-9a-f]{12}',v)
                for k,v in value.items()))
        old_fps=req_meta.get('区间声音指纹');new_fps=fin_meta.get('区间声音指纹')
        require(valid_raw_fingerprints(old_fps) and isinstance(new_fps,dict) and valid_raw_fingerprints(new_fps),
                'Malformed original A45 observation: '+str(n))
        req_meta=copy.deepcopy(req_meta);fin_meta=copy.deepcopy(fin_meta)
        req_meta.pop('区间声音指纹',None);fin_meta.pop('区间声音指纹',None)
        interval_fingerprint_updates.append({'path':'/区间声音指纹','before':old_fps,'after':new_fps,
            'basis':'Original maker A45 observed raw-synthesis validity hashes, not physical audio controls. Both immutable source versions and actual native QC remain in the artifact; original full sound gates and actual approved AAC/absolute timing validation remain mandatory.'})
    rationale_updates=[]
    # The original locator truncates its old appended historical explanation
    # when regenerating the exact same template for the exact same settings.
    # Preserve that history in this explicit ledger and the immutable request;
    # compare every effective field, including the splice samples, deeply.
    ending_key='S'+str(len(final['sentences']))
    before_ending=req_meta.get('结尾句',{}).get(ending_key,{})
    after_ending=fin_meta.get('结尾句',{}).get(ending_key,{})
    old_text=before_ending.get('依据');new_text=after_ending.get('依据')
    if old_text!=new_text and isinstance(old_text,str) and isinstance(new_text,str):
        official_prefix='全篇结尾句按 07 定下的标准'
        if (new_text.startswith(official_prefix) and '接点由 结尾句接点.py 自动找' in new_text
                and '所在帧和两侧各 5 ms 都低于 -55 dB' in new_text and old_text.startswith(new_text)):
            old_effective={k:v for k,v in before_ending.items()if k!='依据'}
            new_effective={k:v for k,v in after_ending.items()if k!='依据'}
            require(old_effective==new_effective,'Effective ending audio controls changed: '+str(n)+'/'+ending_key)
            req_meta=copy.deepcopy(req_meta);fin_meta=copy.deepcopy(fin_meta)
            req_meta['结尾句'][ending_key].pop('依据');fin_meta['结尾句'][ending_key].pop('依据')
            sha=lambda value:hashlib.sha256(value.encode()).hexdigest()
            rationale_updates.append({'path':'/结尾句/'+ending_key+'/依据','before':old_text,'after':new_text,
                'before_sha256':sha(old_text),'after_sha256':sha(new_text),
                'effective_controls_identical':True,'effective_controls':old_effective,
                'official_regenerator':'结尾句接点.py',
                'basis':'Original official locator regenerated the same rationale prefix for deeply identical effective settings. Exact original appended history is retained here and in the immutable requested source. No actual gain/cut/speed/pitch/splice control change is permitted by this classification.'})
    require(req_meta==fin_meta,f'Audio/render/title metadata changed outside actual QC records: {n}')
    return {'visible_body_notes_summary_and_focus_unchanged': True, 'layout_only_newlines_and_T38_bold_allowed': True,
            'audio_render_title_metadata_unchanged':not(rationale_updates or interval_fingerprint_updates),
            'effective_audio_render_title_controls_unchanged':True,
            'official_regenerated_nonaudio_rationale_updates':rationale_updates,
            'observed_original_QC_interval_fingerprint_updates':interval_fingerprint_updates}


def mapping(config):
    catalog = load(config['catalog_path']); order = load(config['order_map_path'])
    videos = catalog['videos']; rows = order['rows']
    require(len(videos) == 70 and len(rows) == 70, 'Both existing catalogs must contain all 70 entries')
    by_old = {r['id']: r for r in videos}; by_order = {r['source_id']: r for r in rows}
    all_ids = {f'{i:02d}' for i in range(1, 71)}
    require(set(by_old) == set(by_order) == all_ids, 'Original-id mapping must be a bijection over 01–70')
    require({r['new_id'] for r in rows} == all_ids, 'Reordered ids must also be a bijection')
    for n, r in by_order.items():
        require(by_old[n]['path'] == r['source_video'], f'Catalog canonical path conflict: {n}')
        relpath(r['source_video']); relpath('顺序重排版/' + r['video'])
        require(r['source_video'].startswith('最终版4K视频/') and r['source_video'].endswith('.mp4'), n)
        require(r['video'].startswith('视频/') and r['video'].endswith('.mp4'), n)
    return catalog, order, by_old, by_order


def approved_illustration_pixels(spec, preparation, book_row, composition, crop):
    """Recreate the reviewed composition from the actual approved original, then compare RGB."""
    from PIL import Image, ImageOps, ImageFilter, __version__ as pillow_version
    require(pillow_version==preparation['Pillow']=='12.3.0','Use the same pinned Pillow12.3.0 rasterizer as the actual approved compositions')
    native=checked_file(spec['native_source']);prepared=checked_file(spec)
    require(spec['native_source']['sha256']==book_row['sha256'] and native.stat().st_size==book_row['bytes'],'Actual original illustration differs from its book entry')
    for row in (composition,crop):
        require(row['source_id']==book_row['source_id'] and row['new_id']==book_row['new_id'] and row['source_image_sha256']==book_row['sha256'],'Composition review belongs to another book illustration')
    require(crop['actually_visually_reviewed']is True and crop['review_state']=='approved_composition' and composition['final_4k_composition_actually_visually_reviewed_via_contact']is True,'Actual reviewed composition required')
    require(preparation['source_id']==book_row['source_id'] and preparation['new_id']==book_row['new_id'] and preparation['native_image_sha256']==book_row['sha256'],'Preparation source/order identity differs')
    require(preparation['derived_in_this_process_from_exact_approved_native_image']is True and preparation['generated_or_substituted_artwork']is False and preparation['added_text_or_graphics']is False,'Actual approved native artwork derivation required')
    require(preparation['mode']==composition['mode']==crop['mode'] and preparation['native_source_crop_box']==composition['source_crop_box']==crop['source_crop_box'],'Unreviewed crop/composition changed')
    require(preparation['prepared_png_sha256']==spec['sha256'] and preparation['native_pixel_dimensions']==book_row['native_pixel_dimensions'] and preparation['prepared_pixel_dimensions']==[3840,2160],'Actual prepared/native pixels or file SHA differs')
    with Image.open(native)as raw:
        require(list(raw.size)==book_row['native_pixel_dimensions'],'Native book illustration dimensions differ')
        image=raw.convert('RGB')
    size=(3840,2160);mode=preparation['mode'];box=preparation['native_source_crop_box']
    if mode=='cover':
        require(isinstance(box,list)and len(box)==4 and all(isinstance(v,int)for v in box)and 0<=box[0]<box[2]<=image.width and 0<=box[1]<box[3]<=image.height and Fraction(box[2]-box[0],box[3]-box[1])==Fraction(*size),'Invalid exact reviewed crop')
        expected=image.crop(tuple(box)).resize(size,Image.Resampling.LANCZOS)
    else:
        require(mode=='contain_blur'and box in(None,[0,0,image.width,image.height])and preparation['same_image_background_gaussian_blur_radius']==64,'Unknown illustration preparation')
        expected=ImageOps.fit(image,size,method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(64))
        foreground=ImageOps.contain(image,size,method=Image.Resampling.LANCZOS)
        expected.paste(foreground,((size[0]-foreground.width)//2,(size[1]-foreground.height)//2))
    expected_sha=hashlib.sha256(expected.tobytes()).hexdigest()
    with Image.open(prepared)as actual:
        require(actual.size==size and hashlib.sha256(actual.convert('RGB').tobytes()).hexdigest()==expected_sha,'Actual prepared4K image pixels do not derive from the approved original/crop')
    require(expected_sha==composition['composed_4k_rgb_sha256']==preparation['prepared_rgb_sha256'],'Actual recomposed image differs from approved70 RGB proof')
    return expected_sha


def actual_illustrated_tail_report(qc,run,evidence,status_sha,layout_row,book_row):
    fingerprint=qc['illustration']['frame_comparison']['report_sha256']
    raw=load(checked_file(next(e for e in evidence if e['sha256']==fingerprint)))
    native_input=run['artifact_native_final_sha256']if run['canonical_selection']=='native_pre_card'else run['artifact_mp4_sha256']
    require(raw['passed']is True and raw['production_delivery_eligible']is True and raw['source_kind']=='new-canonical-4K'and raw['kind']=='approved-book-illustration60-then-approved-summary60','Actual production illustration/card report required')
    require(raw['article']==qc['article']==book_row['source_id']and raw['book_new_id']==book_row['new_id']and raw['input_video_sha256']==native_input and raw['upstream_status_sha256']==status_sha and raw['video_sha256']==qc['video_sha256'],'Actual tail report belongs to different media/native source')
    require(raw['body_reencoded_frames']==raw['audio_reencoded_or_added_packets']==0 and raw['body_coded_pictures_identical']is True and raw['body_packet_timings_identical']is True and raw['aac_packet_payload_and_absolute_timings_identical']is True,'Actual tail processing changed body pictures or audio')
    require(raw['body_frames']==raw['illustration_start_frame']==qc['speech_end']['end_frame']and raw['summary_start_frame']==qc['summary']['start_frame']and raw['output_frames']==qc['actual_probe']['frames'],'Actual tail frame counts/timeline differ')
    require(raw['illustration_frames_checked']==raw['summary_frames_checked']==raw['illustration_frames']==raw['summary_frames']==60 and raw['illustration_max_thumbnail_mean_absolute_error']<2 and raw['summary_max_thumbnail_mean_absolute_error']<2,'Actual full120 tail-frame pixel comparisons failed')
    require(0<=raw['delay_after_voice_seconds']<1/30+1e-9 and abs(raw['illustration_start_seconds']-raw['source_voice_endpoint_seconds']-raw['delay_after_voice_seconds'])<1e-9,'Tail does not start at the actual voice endpoint rounded to the next frame')
    require(raw['illustration_preparation']==qc['illustration']['preparation']and raw['approved_illustration_sha256']==book_row['sha256'],'Actual preparation/native image identity differs')
    require(layout_row['source_id']==qc['article']and layout_row['new_id']==book_row['new_id']and raw['approved_summary_rgb_sha256']==layout_row['summary_rgb_sha256']and qc['summary']['font_px']==layout_row['summary_font_4k_px']and qc['summary']['approved_request_text_sha256']==layout_row['approved_summary_text_sha256'],'Actual card differs from current approved article/layout/text')
    binding=raw['source_script_layout_binding']
    require(binding['actual_request_source_sha256']==qc['source_sha256']['request']['json'] and binding['approved_full_source_sha256']==layout_row['source_json_sha256']and binding['approved_ordered_layout_sha256']==layout_row['source_layout_structural_sha256'],'Actual approved layout and exact render request differ')
    return raw


def validate(config, probe_media=True):
    require(config['schema_version'] == 3, 'Use V3 pinned-book-PDF/all70/two-card tail contract')
    pdf_reference(config['published_pdf'])
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]+', config['revision']) is not None, 'Unsafe revision')
    require(config['release']['tag'] == config['revision'], 'Use a new immutable revision/tag')
    require(config['asset_branch'].startswith('codex/video-assets-'), 'Use a dedicated orphan assets branch')
    require(config['asset_branch'] not in ('main', 'master', BACKUP[1]), 'Unsafe assets branch')
    for role in ('primary', 'backup'):
        require(HEX40.fullmatch(config['expected_heads'][role]) is not None, f'Pin {role} branch HEAD')
    require(HEX40.fullmatch(config['backup_master_expected']) is not None, 'Pin full backup master SHA')
    require(config['backup_master_expected'].startswith('6355a0'), 'Unexpected protected backup master baseline')
    for name in ('catalog_repo_path', 'order_map_repo_path', 'finalization_manifest_repo_path'): relpath(config[name])
    requested = config['requested_ids']
    require(set(requested) == {f'{i:02d}' for i in range(1, 71)} and len(requested) == 70, 'This revision requires all 70 actual newly rendered videos')
    require(config['release']['asset_policy'] == ASSET_POLICY and config['release']['expected_asset_count'] == 71 and not config.get('unchanged_videos'), 'Release must contain exactly one pinned PDF and all70 new ordered MP4s')
    changed_audio = set(config['audio_changed_articles'])
    require(len(changed_audio) == len(config['audio_changed_articles']) and {'10', '12', '51'} <= changed_audio <= set(requested), 'Dynamic audio_changed_articles must include actual repairs10/12/51 and only requested IDs')
    require(set(requested) == {r['id'] for r in config['articles']} and len(requested) == len(config['articles']),
            'Every requested article must have exactly one actual passed output; no missing/extra rows')
    catalog, order, old, reorder = mapping(config)
    book_map_path=checked_file(config['book_illustrations'])
    require(config['book_illustrations']['sha256']==config['published_pdf']['illustrations_manifest']['sha256'] and book_map_path.stat().st_size==config['published_pdf']['illustrations_manifest']['bytes'],'Local illustration map must equal the frozen PDF-owner map')
    book_map=book_illustrations(load(book_map_path),order['rows'])
    composition_path=checked_file(config['illustration_composition_review']);crop_path=checked_file(config['illustration_crop_review'])
    compositions=load(composition_path);crops=load(crop_path)
    require(compositions['passed']is True and compositions['actual70_compositions_reviewed']is True and compositions['count']==crops['count']==70,'Actual full70 illustration composition review required')
    require(compositions['crop_review_sha256']==digest(crop_path) and all(r['actually_visually_reviewed']is True and r['review_state']=='approved_composition'for r in crops['articles']),'Actual individually reviewed illustration crops changed')
    compose_by_id={r['source_id']:r for r in compositions['articles']};crop_by_id={r['source_id']:r for r in crops['articles']}
    require(len(compositions['articles'])==len(crops['articles'])==len(compose_by_id)==len(crop_by_id)==70 and set(compose_by_id)==set(crop_by_id)==set(book_map),'Illustration review source mapping incomplete')
    request_root = Path(config['request_source_root']).resolve(); root = Path(config['final_source_root']).resolve(); records = []
    for item in config['articles']:
        records.append(validate_article(config,item,old,reorder,book_map,compose_by_id,crop_by_id,changed_audio,probe_media))
    require(isinstance(config.get('unchanged_videos', []), list), 'unchanged_videos must be an array')
    require(not config.get('unchanged_videos'), 'All70 must be new official actualpassed outputs')
    exact_assets(records,config['published_pdf'])
    return records


def validate_article(config,item,old,reorder,book_map,compose_by_id,crop_by_id,changed_audio,probe_media=True):
    """Real per-article checks, reusable without pretending a partial set is publishable."""
    request_root=Path(config['request_source_root']).resolve();root=Path(config['final_source_root']).resolve()
    n = item['id']; require(n in old, f'Unknown article {n}')
    video = checked_file(item['mp4']); require(video.suffix.lower() == '.mp4', str(video))
    require(0 < video.stat().st_size < MAX_BLOB, f'Git regular-blob 100MiB limit exceeded: {video}')
    canonical = checked_file(item['canonical_mp4'])
    receipt_path = checked_file(item['qc']); qc = load(receipt_path)
    require(qc['article'] == n and qc['status'] == 'passed' and qc['actual_new_mp4'] is True, f'Actual QC not passed: {n}')
    require(qc['video_sha256'] == item['mp4']['sha256'] and qc['video_bytes'] == video.stat().st_size,
            f'QC is for another MP4: {n}')
    require(qc.get('simulation', False) is False and qc.get('proposal_only', False) is False, f'Proposal/simulation QC rejected: {n}')
    run = qc['official_run']
    official_job_declaration(run, n, item['canonical_mp4']['sha256'])
    artifact_zip = checked_file(run['artifact_zip'])
    native_status=artifact_contents(run, n, item['canonical_mp4']['sha256'], artifact_zip.read_bytes())
    with zipfile.ZipFile(artifact_zip)as z:native_status_sha256=hashlib.sha256(z.read(run['artifact_status_member'])).hexdigest()
    if 'artifact_main_status_member'in run:
        with zipfile.ZipFile(artifact_zip)as z:main_bytes=z.read(run['artifact_main_status_member'])
        main_native=json.loads(main_bytes)
        require(hashlib.sha256(main_bytes).hexdigest()==run['artifact_main_status_sha256']and main_native['passed']is True and main_native['stage']=='final4K-passed'and main_native['article']==n and main_native['video_sha256']==item['mp4']['sha256']and main_native['illustration_frames']==main_native['summary_frames']==60,'Actual native inline final status/media differs')
    actual_json=item['final_source']['json']
    require(actual_json['origin']=='official_artifact_working_copy'and actual_json['artifact_id']==run['artifact_id'],'Actual final JSON must be an observed immutable producer artifact member')
    with zipfile.ZipFile(artifact_zip)as z:
        require(hashlib.sha256(z.read(actual_json['artifact_member'])).hexdigest()==actual_json['sha256'],'Final JSON differs from actual producer working-source ZIP member')
    require(run['entrypoint'].endswith('定稿.sh') and run['stage'] == '4K', f'Not official finalization: {n}')
    require(isinstance(run['run_id'], int) and run['run_id'] > 0 and isinstance(run['artifact_id'], int) and run['artifact_id'] > 0, n)
    require(HEX40.fullmatch(run['head_sha']) is not None and HEX64.fullmatch(run['artifact_zip_sha256']) is not None, n)
    require(run['workflow_path'].startswith('.github/workflows/'), n)
    actual = probe(video) if probe_media else qc['actual_probe']
    require(actual['width'] == 3840 and actual['height'] == 2160, n)
    require(actual['frames'] == qc['actual_probe']['frames'], f'Actual total frames mismatch: {n}')
    summary = qc['summary']
    require(summary['decoded_from_actual_mp4'] is True and summary['frames'] == 60, f'No actual 60-frame summary proof: {n}')
    require(summary['start_frame'] + 60 == actual['frames'], f'Summary is not the final 60 frames: {n}')
    require(summary['overflow'] is False and summary['normal_font_size'] is True and summary['font_px'] > 0, f'Summary layout not accepted: {n}')
    audio = qc['audio']; canonical_qc = audio['canonical_qc']
    evidence_hashes = {e['sha256'] for e in item['evidence']}
    checked_file(item['illustration'])
    preparation=qc['illustration']['preparation']
    require(preparation['preparer_program_sha256']==load(checked_file(config['illustration_composition_review']))['postprocessor_sha256'],'Actual illustration preparer differs from approved program')
    approved_illustration_pixels(item['illustration'],preparation,book_map[n],compose_by_id[n],crop_by_id[n])
    layouts=load(checked_file(config['video_layout_approval']));require(layouts['passed']is True and layouts['count']==len(layouts['articles'])==70,'Actual current70 static layout approvals required')
    actual_illustrated_tail_report(qc,run,item['evidence'],native_status_sha256,next(r for r in layouts['articles']if r['source_id']==n),book_map[n])
    tail_contract(qc, item['illustration'], item['stills'], evidence_hashes,book_map[n])
    require(audio['repair_applied'] is (n in changed_audio), f'Actual repair flag differs from dynamic audio_changed_articles: {n}')
    if n in changed_audio or n == '44':
        target = audio['targeted_review']
        require(target['article'] == n and target['actual_new_output'] is True and target['status'] == 'passed' and
                target['canonical_video_sha256'] == item['canonical_mp4']['sha256'] and target['report_sha256'] in evidence_hashes,
                f'{n} actual targeted canonical audio review required')
        if n == '44': require(target['whole_track_loudness_review'] is True, '44 requires whole-track loudness review, repaired or unchanged')
    if n in changed_audio:
        require(audio['controlled_repair']['status'] == 'passed' and audio['controlled_repair']['actual_new_output'] is True and
                audio['controlled_repair']['canonical_video_sha256'] == item['canonical_mp4']['sha256'] and
                audio['controlled_repair']['report_sha256'] in evidence_hashes and audio['controlled_repair']['authorization'],
                f'Controlled repair actual proof/authorization absent: {n}')
    # Canonical container/video SHA may differ. The actual copied AAC and absolute packet timing may not.
    canonical_audio = actual_aac(canonical); final_audio = actual_aac(video)
    audio_basis=canonical_audio_contract(canonical_qc,native_status,n,item['canonical_mp4']['sha256'],canonical_audio['aac_adts_sha256'],evidence_hashes,native_status_sha256,n in changed_audio or n in {'10','12','44','51'})
    if audio_basis=='actual_official_audio_gates_plus_exact_accepted_AAC':
        require(native_status['accepted_source']['sha256']==old[n]['sha256'],'Native accepted audio reference differs from existing catalog baseline')
    else:
        raw_audio=load(checked_file(next(e for e in item['evidence']if e['sha256']==canonical_qc['report_sha256'])))
        if audio_basis=='actual_dedicated_audio_qc_then_verified_exact_AAC_copy':
            copy_sha=canonical_qc['copy_verification_sha256'];copy_proof=load(checked_file(next(e for e in item['evidence']if e['sha256']==copy_sha)))
            tail_sha=qc['illustration']['frame_comparison']['report_sha256'];tail_proof=load(checked_file(next(e for e in item['evidence']if e['sha256']==tail_sha)))
            require(tail_proof['upstream_verification_sha256']==copy_sha,'Actual inline tail does not reference this original native audio-copy proof')
            reviewed_canonical_audio_copy(canonical_qc,native_status,raw_audio,copy_proof,n,item['canonical_mp4']['sha256'],canonical_audio['aac_adts_sha256'])
        else:
            require(raw_audio['article']==n and raw_audio['passed']is True and raw_audio['canonical_sha256']==item['canonical_mp4']['sha256']and raw_audio['checks']and all(c['passed']is True for c in raw_audio['checks']),'Original actual dedicated acoustic-QC file is not passed for this exact canonical MP4')
    require(canonical_audio['aac_adts_sha256'] == final_audio['aac_adts_sha256'], f'AAC ADTS content changed after canonical QC: {n}')
    require(canonical_audio['packet_projection_sha256'] == final_audio['packet_projection_sha256'], f'Audio packet payload/timing/priming changed after canonical QC: {n}')
    chain = audio['lossless_copy']
    require(chain['canonical_video_sha256'] == item['canonical_mp4']['sha256'] and chain['final_video_sha256'] == item['mp4']['sha256'], f'Audio chain belongs to other files: {n}')
    require(chain['audio_packet_times_identical'] is True and chain['canonical_aac_adts_sha256'] == chain['final_aac_adts_sha256'] == canonical_audio['aac_adts_sha256'], f'AAC proof chain mismatch: {n}')
    require(chain['canonical_packet_projection_sha256'] == chain['final_packet_projection_sha256'] == canonical_audio['packet_projection_sha256'], f'Actual packet timing proof chain mismatch: {n}')
    require(chain['canonical_packet_count'] == chain['final_packet_count'] == canonical_audio['packet_count'], f'Packet count changed: {n}')
    request_sources = item['request_source']; sources = item['final_source']
    require(set(request_sources) == set(sources) == {'json', 'gen', 'md'}, f'Need request and actual final JSON/gen/MD: {n}')
    for kind, spec in sources.items():
        relpath(spec['path']); checked_file(spec, root); checked_file(request_sources[kind], request_root)
        require(spec['path'] == request_sources[kind]['path'], f'Source path drift: {n}/{kind}')
        origin=spec['origin']
        if origin in ('official_artifact_working_copy','actual_working_manuscript','used_generator'):
            require(spec['artifact_id']==run['artifact_id']and spec['artifact_member'],f'Actual observed working-source artifact identity missing: {n}/{kind}')
        else:
            require((kind=='gen'and origin=='derived_after_final_QC')or(kind=='md'and origin=='request_manuscript_with_verified_final_source_equivalence'),f'Untruthful/unknown final-source origin: {n}/{kind}')
            require(spec['derived_from_json_sha256']==sources['json']['sha256']and spec['derivation_proof']['sha256']in evidence_hashes,f'Derived source must retain actual JSON and original derivation proof: {n}/{kind}')
        if kind == 'json': require(spec['path'] == f'视频/脚本/{n}.json', n)
        if kind == 'gen': require(spec['path'] == f'视频/工具/初稿生成/gen{n}.py', n)
        if kind == 'md': require(spec['path'].startswith(f'新版定稿/{n}-') and spec['path'].endswith('.md'), n)
        require(qc['source_sha256']['final'][kind] == spec['sha256'] and qc['source_sha256']['request'][kind] == request_sources[kind]['sha256'], f'Render source-layer fingerprints differ: {n}/{kind}')
    if sources['gen']['origin']=='derived_after_final_QC':
        from derive_final_generator import derive
        policy=config['source_derivation'];factory=checked_file(policy['factory']);proof=load(checked_file(sources['gen']['derivation_proof']))
        require(proof['origin']=='derived_after_final_QC'and proof['actual_original_job_execution_claimed']is False and proof['source_json_sha256']==sources['json']['sha256']and proof['derived_generator_sha256']==sources['gen']['sha256']and proof['whole_JSON_roundtrip_exact']is True,'Original derived-source proof does not describe these exact files')
        with tempfile.TemporaryDirectory(prefix='validate-derived-gen-')as temp:
            native_path=Path(temp)/'native-status.json'
            with zipfile.ZipFile(artifact_zip)as z:native_path.write_bytes(z.read(run.get('artifact_main_status_member',run['artifact_status_member'])))
            verified=derive(root/sources['json']['path'],request_root/request_sources['json']['path'],request_root/request_sources['gen']['path'],request_root/request_sources['md']['path'],native_path,policy['original_tools_root'],factory,Path(temp)/'rederived')
            require(verified['derived_generator_sha256']==sources['gen']['sha256']and verified['changed_paths']==proof['changed_paths'],'Actual unchanged-helper recheck differs from the claimed final derived GEN')
    if sources['md']['origin']=='request_manuscript_with_verified_final_source_equivalence':
        require(sources['md']['sha256']==request_sources['md']['sha256']and sources['gen']['origin']=='derived_after_final_QC'and sources['md']['derivation_proof']['sha256']==sources['gen']['derivation_proof']['sha256'],'Unobserved manuscript must be the immutable request original with exact final-source equivalence proof')
    transform = qc['source_transform']
    require(transform['status'] == 'passed' and transform['actual_working_copy'] is True and
            set(transform['operations']) <= {'L19', 'T38', 'production_qc_metadata'} and transform['report_sha256'] in evidence_hashes,
            f'Unapproved/non-mechanical source transformation: {n}')
    request_json = load(request_root / request_sources['json']['path']); final_json = load(root / sources['json']['path'])
    actual_changed_paths = changed_json_paths(request_json, final_json)
    require(sorted(transform['changed_paths']) == sorted(actual_changed_paths), f'Actual mechanical source diff ledger mismatch: {n}')
    invariants = source_invariants(request_json, final_json, n)
    invariants['actual_changed_paths'] = actual_changed_paths
    # Markdown English/Chinese prose and fact appendix must also remain stable under style/wrapping.
    req_md = (request_root / request_sources['md']['path']).read_text(); final_md = (root / sources['md']['path']).read_text()
    for heading, stop in [('## 英文', '## 中文'), ('## 中文', '## 速查表')]:
        require(visible_tokens(req_md.split(heading, 1)[1].split(stop, 1)[0], heading == '## 中文') ==
                visible_tokens(final_md.split(heading, 1)[1].split(stop, 1)[0], heading == '## 中文'), f'Markdown prose changed outside mechanical style: {n}/{heading}')
    require(visible_tokens(req_md.split('## 史实与来源', 1)[-1]) == visible_tokens(final_md.split('## 史实与来源', 1)[-1]), f'Markdown facts changed: {n}')
    require({s['kind'] for s in item['stills']} >= {'summary', 'body_end', 'illustration'}, f'Need actual body/illustration/card stills: {n}')
    for still in item['stills']:
        checked_file(still); require(still['video_sha256'] == item['mp4']['sha256'], f'Still from other MP4: {n}')
        require(still['decoded_from_actual_mp4'] is True and isinstance(still['frame'], int), n)
    for evidence in item['evidence']: checked_file(evidence)
    require(item['evidence'], f'Actual original QC/log/probe evidence required: {n}')
    require(HEX64.fullmatch(summary['text_sha256']) is not None, n)
    source_json = load(root / sources['json']['path'])
    found = []
    for sentence in source_json['sentences']:
        for chunk in sentence['chunks']:
            text = chunk.get('note', ''); start = text.find('（简述：')
            if start >= 0:
                depth = 0
                for end in range(start, len(text)):
                    depth += (text[end] == '（') - (text[end] == '）')
                    if depth == 0:
                        found.append(text[start:end + 1]); break
    require(len(found) == 1 and found[0].count('▸') == 5, f'No unique approved five-point summary in final source: {n}')
    require(hashlib.sha256(found[0].encode()).hexdigest() == summary['text_sha256'], f'Actual summary QC text differs from approved source: {n}')
    return ({'id': n, 'new_id': reorder[n]['new_id'], 'canonical_path': old[n]['path'],
                    'reordered_path': '顺序重排版/' + reorder[n]['video'], 'sha256': item['mp4']['sha256'],
                    'bytes': video.stat().st_size, 'actual_probe': actual, 'qc': qc,
                    'canonical_video_sha256': item['canonical_mp4']['sha256'], 'canonical_video_bytes': canonical.stat().st_size,
                    'actual_audio_chain': {k: v for k, v in canonical_audio.items() if k != 'projection'},
                    'source_invariants': invariants, 'audio_repaired': n in changed_audio, 'canonical_audio_acceptance_basis':audio_basis,'illustration': item['illustration'],
                    'tail': tail_contract(qc,item['illustration'],item['stills'],evidence_hashes,book_map[n])})


def stage(config_path, output):
    config = load(config_path); records = validate(config); out = Path(output).resolve()
    require(not out.exists(), f'Stage must be a fresh directory: {out}'); out.mkdir(parents=True)
    srcroot = Path(config['final_source_root']); requestroot = Path(config['request_source_root']); audit = f'视频/制作记录/4K重制定稿/{config["revision"]}'
    files = {}
    def copyfile(src, dest):
        relpath(dest); p = out / dest; p.parent.mkdir(parents=True, exist_ok=True)
        require(dest not in files, f'Duplicate staged path: {dest}')
        shutil.copy2(src, p); files[dest] = {'bytes': p.stat().st_size, 'sha256': digest(p)}
    book_map_path=audit+'/book-illustrations70.json'
    copyfile(checked_file(config['book_illustrations']),book_map_path)
    for key in ('illustration_composition_review','illustration_crop_review','video_layout_approval'):
        copyfile(checked_file(config[key]),audit+'/'+key+'.json')
    for item, rec in zip(config['articles'], records):
        n = item['id']; copyfile(item['mp4']['path'], rec['canonical_path']); copyfile(item['mp4']['path'], rec['reordered_path'])
        for spec in item['final_source'].values(): copyfile(srcroot / spec['path'], spec['path'])
        for spec in item['request_source'].values(): copyfile(requestroot / spec['path'], f'{audit}/{n}/request-source/' + spec['path'])
        # Retain the actual approved canonical AAC and exact packet proof, without duplicating 70 intermediate MP4s.
        aac = out / f'{audit}/{n}/audio/canonical.aac'; aac.parent.mkdir(parents=True, exist_ok=True)
        command(['ffmpeg', '-v', 'error', '-i', item['canonical_mp4']['path'], '-map', '0:a:0', '-vn', '-c:a', 'copy', '-f', 'adts', str(aac)])
        files[str(aac.relative_to(out))] = {'bytes': aac.stat().st_size, 'sha256': digest(aac)}
        proof = out / f'{audit}/{n}/audio/lossless-packet-proof.json'
        write(proof, {'canonical_video_sha256': item['canonical_mp4']['sha256'], 'final_video_sha256': item['mp4']['sha256'], 'canonical': actual_aac(item['canonical_mp4']['path']), 'final': actual_aac(item['mp4']['path'])})
        files[str(proof.relative_to(out))] = {'bytes': proof.stat().st_size, 'sha256': digest(proof)}
        copyfile(item['qc']['path'], f'{audit}/{n}/actual-qc.json')
        copyfile(item['illustration']['path'], f'{audit}/{n}/approved-illustration/' + Path(item['illustration']['path']).name)
        copyfile(item['illustration']['native_source']['path'], f'{audit}/{n}/approved-native-illustration/' + Path(item['illustration']['native_source']['path']).name)
        for group in ('evidence', 'stills'):
            for i, spec in enumerate(item[group]):
                copyfile(spec['path'], f'{audit}/{n}/{group}/{i:03d}-{Path(spec["path"]).name}')
    # Copies must remain the exact approved files if another process was still writing artifacts.
    for item, rec in zip(config['articles'], records):
        require(digest(out / rec['canonical_path']) == digest(out / rec['reordered_path']) == rec['sha256'], 'Staged MP4 changed after validation')
        checked_file(item['canonical_mp4'])
        for spec in item['final_source'].values(): checked_file(spec, out)
        for spec in item['request_source'].values():
            frozen = {'path': f'{audit}/{item["id"]}/request-source/' + spec['path'], 'sha256': spec['sha256']}
            checked_file(frozen, out)
    catalog, order, old, reorder = mapping(config)
    for rec in records:
        old[rec['id']].update({'sha256': rec['sha256'], 'bytes': rec['bytes'], 'width': 3840, 'height': 2160,
                              'summary_frames': 60, 'illustration_frames':60, 'revision': config['revision'], 'actual_qc_status': 'passed'})
        reorder[rec['id']].update({'video_sha256': rec['sha256'], 'video_bytes': rec['bytes'], 'video_revision': config['revision']})
    catalog['latest_video_revision'] = config['revision']
    catalog['current_video_repository'] = PRIMARY[0]
    catalog['current_video_ref'] = 'main'
    catalog['source_commit_scope'] = 'Historical import provenance only; current video hashes below are stored on current_video_repository/current_video_ref; the immutable new commit is in the delivery archive receipt.'
    order['latest_video_revision'] = config['revision']
    # Preserve all unrelated/PDF fields exactly; these are video catalogs, not PDF rebuilds.
    for name, value in [(config['catalog_repo_path'], catalog), (config['order_map_repo_path'], order)]:
        write(out / relpath(name), value)
    assets=exact_assets(records,config['published_pdf'])
    inventory_path=audit+'/release-assets.json'; sums_path=audit+'/SHA256SUMS.txt'
    write(out/inventory_path,{'schema_version':3,'revision':config['revision'],'assets':assets})
    (out/sums_path).write_text(''.join(a['sha256']+'  '+a['name']+'\n'for a in assets))
    for path in [inventory_path,sums_path]:files[path]={'bytes':(out/path).stat().st_size,'sha256':digest(out/path)}
    manifest = {'schema_version': 3, 'revision': config['revision'], 'requested_ids': config['requested_ids'],
                'status': 'all_requested_actual_4K_passed_and_book_PDF_reference_frozen', 'videos_in_catalog': 70, 'summary_frames': 60, 'illustration_frames':60,
                'width': 3840, 'height': 2160, 'articles': records, 'audio_changed_articles': config['audio_changed_articles'], 'source_files': {r['id']: {'request': r['request_source'], 'final': r['final_source']} for r in config['articles']},
                'inherited_unmodified_for_optional_full70': [], 'PDF_modified_by_video_stage': False, 'published_pdf':config['published_pdf'],'exact_release_assets':assets,'book_illustrations_repo_path':book_map_path}
    write(out / config['finalization_manifest_repo_path'], manifest)
    write(out / audit / 'finalization-manifest.json', manifest)
    for name in [config['catalog_repo_path'], config['order_map_repo_path'], config['finalization_manifest_repo_path'], audit + '/finalization-manifest.json']:
        p = out / name; files[name] = {'bytes': p.stat().st_size, 'sha256': digest(p)}
    here = Path(__file__).resolve().parent
    copyfile(here / 'release_actions.py', PROGRAM_DIR + '/release_actions.py')
    copyfile(here / 'release_contract.py', PROGRAM_DIR + '/release_contract.py')
    copyfile(here / 'derive_final_generator.py', PROGRAM_DIR + '/derive_final_generator.py')
    if any(item['final_source']['gen']['origin']=='derived_after_final_QC'for item in config['articles']):
        copyfile(checked_file(config['source_derivation']['factory']),audit+'/source-derivation/pure-data-factory.py')
    copyfile(here / 'publish-video-revisions.yml', WORKFLOW)
    plan = {'schema_version': 3, 'revision': config['revision'], 'release': config['release'],
            'records': [{k: v for k, v in r.items() if k != 'qc'} for r in records],
            'unchanged_videos': config.get('unchanged_videos', []),
            'order_rows': order['rows'], 'manifest_path': config['finalization_manifest_repo_path'],
            'audit_path': audit, 'files': files, 'published_pdf':config['published_pdf'],'exact_assets':assets,'book_illustrations_repo_path':book_map_path,
            'repository_asset_inventory_path':inventory_path,'repository_asset_inventory_sha256':digest(out/inventory_path),
            'repository_sha256sums_path':sums_path,'repository_sha256sums_sha256':digest(out/sums_path),
            'remote_receipt_repo_path':audit+'/REMOTE-DELIVERY-VERIFICATION.json','cleanup_targets':config.get('cleanup_targets',[])}
    write(out / PROGRAM_DIR / 'release-plan.json', plan)
    write(out / PROGRAM_DIR / 'archive-config.json', {k: config[k] for k in ['revision', 'asset_branch', 'expected_heads', 'backup_master_expected']})
    # Stage inventory intentionally excludes its own hash to avoid circular evidence.
    inventory = []
    for p in sorted(out.rglob('*')):
        if p.is_file():
            require(p.stat().st_size < MAX_BLOB, f'Staged file too large for regular Git blob: {p}')
            inventory.append({'path': str(p.relative_to(out)), 'bytes': p.stat().st_size, 'sha256': digest(p)})
    write(out / PROGRAM_DIR / 'staged-files.json', inventory)
    write(out.parent / (out.name + '-validation.json'), {'passed': True, 'requested_ids': config['requested_ids'], 'files': len(inventory), 'publishing_executed': False})
    return out


class GitHub:
    def __init__(self):
        self.token = os.environ.get('GH_TOKEN') or command(['gh', 'auth', 'token'])
    def raw_artifact(self,repo,artifact_id):
        return subprocess.run(['gh','api',f'repos/{repo}/actions/artifacts/{artifact_id}/zip'],check=True,capture_output=True).stdout
    def raw_job_logs(self,repo,job_id):
        return subprocess.run(['gh','api',f'repos/{repo}/actions/jobs/{job_id}/logs'],check=True,capture_output=True).stdout.decode(errors='replace')
    def api(self, repo, route, method='GET', data=None):
        req = urllib.request.Request('https://api.github.com/repos/' + repo + '/' + route,
            data=None if data is None else json.dumps(data).encode(), method=method,
            headers={'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json',
                     'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=120) as response:
            body = response.read(); return json.loads(body) if body else None


def artifact_upload_step_proof(logs, steps, selected, artifact_id, zip_sha):
    """Bind the upload action's own ID/digest to its API step, not arbitrary job output."""
    require(selected['status']=='completed' and selected['conclusion']=='success','Selected upload step must actually complete successfully')
    def stamp(value):
        return datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
    start=stamp(selected['started_at']);end=stamp(selected['completed_at'])+datetime.timedelta(seconds=1)
    require(start<end and isinstance(selected['number'],int),'Actual upload step interval/number required')
    lines=logs.lstrip('\ufeff').splitlines();headers=[]
    for index,line in enumerate(lines):
        match=re.match(r'^(\S+) ##\[group\]Run (.+)$',line)
        if match:headers.append((index,stamp(match[1]),match[2]))
    candidates=[row for row in headers if start<=row[1]<end and re.fullmatch(r'actions/upload-artifact@\S+',row[2])]
    require(len(candidates)==1,'Upload action log block is missing or ambiguous in selected API step interval')
    index,header_time,action=candidates[0]
    # GitHub API step dates have whole-second precision. Reject overlapping upload
    # steps instead of assigning a fast neighboring action by guesswork.
    overlaps=[step for step in steps if step.get('status')=='completed'and step.get('number')!=selected['number']and re.search(r'upload',step.get('name',''),re.I)and stamp(step['started_at'])<=header_time<stamp(step['completed_at'])+datetime.timedelta(seconds=1)]
    require(not overlaps,'Coarse API timestamps cannot uniquely assign this upload action')
    stop=next((i for i,line in enumerate(lines[index+1:],index+1)if re.match(r'^\S+ ##\[group\]Run ',line)or re.match(r'^\S+ Post job cleanup\.',line)),len(lines))
    block='\n'.join(lines[index:stop]);ids=set();digests=set()
    for line in lines[index:stop]:
        match=re.match(r'^(\S+) (.*)$',line)
        if not match:continue
        payload=match[2]
        if re.search(r'Artifact ID|SHA256 digest of uploaded artifact zip is',payload,re.I):
            require(start<=stamp(match[1])<end,'Artifact upload identity logged outside selected API step')
            ids.update(int(v)for v in re.findall(r'Artifact ID(?:\s+is)?\s*:?\s*(\d+)',payload,re.I))
            digests.update(re.findall(r'SHA256 digest of uploaded artifact zip is\s+([0-9a-f]{64})',payload,re.I))
    require(ids=={artifact_id}and digests=={zip_sha},'Specified successful upload action did not upload this exact artifact ID/ZIP digest')
    return {'step_name':selected['name'],'step_number':selected['number'],'started_at':selected['started_at'],'completed_at':selected['completed_at'],'action':action,'upload_block_sha256':hashlib.sha256(block.encode()).hexdigest(),'artifact_id':artifact_id,'artifact_zip_sha256':zip_sha,'unambiguous_selected_step_upload':True}


def verify_remote_official_job(api,run,article,canonical_sha,final_sources=None):
    job=official_job_declaration(run,article,canonical_sha)
    actual=api.api(run['repository'],f'actions/runs/{run["run_id"]}/attempts/{run["run_attempt"]}')
    require(actual['head_sha']==run['head_sha'] and actual['path']==run['workflow_path'],'Official run/head/workflow mismatch')
    actual_job=api.api(run['repository'],f'actions/jobs/{job["id"]}')
    require(actual_job['run_id']==run['run_id'] and actual_job['run_attempt']==run['run_attempt'] and actual_job['name']==job['name'] and actual_job['status']=='completed' and actual_job['conclusion']==('failure'if post_quality_missing_art_recovery(run,article)else'success'),'Actual job identity/conclusion differs from declared successful or exact recovered upstream quality')
    steps=[v for v in actual_job['steps']if v['name']==job['upload_step_name']]
    require(len(steps)==1 and steps[0]['conclusion']=='success','Actual artifact-upload step not successful')
    art=api.api(run['repository'],f'actions/artifacts/{run["artifact_id"]}')
    require(not art['expired'] and art.get('workflow_run',{}).get('id')==run['run_id'] and art.get('digest')=='sha256:'+run['artifact_zip_sha256'],'Artifact/run/ZIP identity mismatch')
    # The actual successful article job, immutable run artifact, native passed
    # article/media and working-source hashes are the acceptance evidence.
    # Upload text is useful corroboration; transient/missing log text must not
    # invalidate an otherwise proven output (current repository/user policy).
    logs=''
    try:
        logs=api.raw_job_logs(run['repository'],job['id'])
        upload_proof=artifact_upload_step_proof(logs,actual_job['steps'],steps[0],run['artifact_id'],run['artifact_zip_sha256'])
    except Exception as error:
        upload_proof={'unambiguous_selected_step_upload':False,'auxiliary_only':True,'reason':str(error),'acceptance_blocked_by_log':False}
    blob=api.raw_artifact(run['repository'],run['artifact_id']);native_status=artifact_contents(run,article,canonical_sha,blob)
    import io
    with zipfile.ZipFile(io.BytesIO(blob))as z:status_bytes=z.read(run['artifact_status_member'])
    if final_sources is not None:
        import io
        with zipfile.ZipFile(io.BytesIO(blob))as z:
            for kind,spec in final_sources.items():
                if spec['origin']in('official_artifact_working_copy','actual_working_manuscript','used_generator'):
                    require(spec['artifact_id']==run['artifact_id']and hashlib.sha256(z.read(spec['artifact_member'])).hexdigest()==spec['sha256'],f'Actual official artifact working source member differs: {article}/{kind}')
                else:
                    require(kind in('gen','md')and spec['derived_from_json_sha256']==final_sources['json']['sha256'],'Derived source lost its actual final JSON provenance')
    return {'actual_successful_job_verified':actual_job['conclusion']=='success','actual_genuine_upstream_pass_with_missing_art_recovery':post_quality_missing_art_recovery(run,article),'actual_job_uploaded_selected_artifact':upload_proof['unambiguous_selected_step_upload'],'overall_matrix_success_required':False,'acceptance_basis':('genuine immutable upstream quality-passed 4K + original outer missing-art failure retained + actual local approved-art postprocessing and complete final V3 media validation'if post_quality_missing_art_recovery(run,article)else'actual successful article job + immutable run artifact + actual native passed article/media/source identity; upload log is auxiliary'),
        'run':actual,'job':actual_job,'artifact':art,'upload_step_proof':upload_proof,'native_status':native_status,'native_status_sha256':hashlib.sha256(status_bytes).hexdigest(),
        '_native_status_bytes':status_bytes,'_actual_job_log':logs}


def archive(stage_path, execute=False):
    require(execute, 'Archive is not executed without explicit --execute; draft preparation requires no publication')
    work = Path(stage_path).resolve(); cfg = load(work / PROGRAM_DIR / 'archive-config.json')
    inventory = load(work / PROGRAM_DIR / 'staged-files.json'); api = GitHub()
    for f in inventory: checked_file({'path': f['path'], 'bytes': f['bytes'], 'sha256': f['sha256']}, work)
    require(api.api(BACKUP[0], 'git/ref/heads/master')['object']['sha'] == cfg['backup_master_expected'], 'Protected backup master changed')
    # Verify the official run and artifact on GitHub before any mutation.
    final = load(work / load(work / PROGRAM_DIR / 'release-plan.json')['manifest_path'])
    for item in final['articles']:
        run = item['qc']['official_run'];observed=verify_remote_official_job(api,run,item['id'],item['canonical_video_sha256'],final['source_files'][item['id']]['final'])
        audit=work/('视频/制作记录/4K重制定稿/'+cfg['revision']+'/'+item['id']+'/official-job')
        audit.mkdir(parents=True,exist_ok=True);(audit/'native-status.json').write_bytes(observed.pop('_native_status_bytes'));(audit/'actual-upload-job.log').write_text(observed.pop('_actual_job_log'));write(audit/'verification.json',observed)
        item['official_job_verification']={'path':str((audit/'verification.json').relative_to(work)),'sha256':digest(audit/'verification.json')}
    # Preserve actual remote job observations permanently, without adding Release attachments.
    plan_path=work/PROGRAM_DIR/'release-plan.json';plan=load(plan_path)
    write(work/plan['manifest_path'],final);write(work/plan['audit_path']/'finalization-manifest.json',final)
    for path in work.rglob('*'):
        if path.is_file()and str(path.relative_to(work))not in (PROGRAM_DIR+'/release-plan.json',PROGRAM_DIR+'/staged-files.json'):
            require(path.stat().st_size<MAX_BLOB,'Actual verification record exceeds regular Git blob limit')
            plan['files'][str(path.relative_to(work))]={'bytes':path.stat().st_size,'sha256':digest(path)}
    write(plan_path,plan)
    inventory=[{'path':str(p.relative_to(work)),'bytes':p.stat().st_size,'sha256':digest(p)}for p in sorted(work.rglob('*'))if p.is_file()and str(p.relative_to(work))!=PROGRAM_DIR+'/staged-files.json']
    write(work/PROGRAM_DIR/'staged-files.json',inventory)
    # Check both destinations before pushing any orphan assets branch.
    for role, (repo, branch) in [('primary', PRIMARY), ('backup', BACKUP)]:
        require(api.api(repo, 'git/ref/heads/' + branch)['object']['sha'] == cfg['expected_heads'][role], role + ' destination HEAD moved; rebase metadata first')
    require(not (work / '.git').exists(), 'Use fresh staged checkout; archive state exists')
    command(['git', 'init', '-q', '-b', cfg['asset_branch']], work)
    command(['git', 'config', 'user.name', 'Codex'], work); command(['git', 'config', 'user.email', 'codex@users.noreply.github.com'], work)
    command(['git', 'config', 'credential.helper', '!gh auth git-credential'], work)
    allfiles = [p for p in work.rglob('*') if p.is_file() and '.git' not in p.relative_to(work).parts]
    # Push incremental commits well below the per-push 2GiB limit; repeated MP4 bytes deduplicate as Git blobs.
    batch = []; size = 0
    for p in sorted(allfiles):
        batch.append(str(p.relative_to(work))); size += p.stat().st_size
        if size >= 350 * 1024 * 1024:
            command(['git', 'add', '--', *batch], work); command(['git', 'commit', '-qm', 'Archive actual reviewed MP4/source/QC assets [skip ci]'], work)
            for repo, _ in (PRIMARY, BACKUP): command(['git', 'push', 'https://github.com/' + repo + '.git', 'HEAD:refs/heads/' + cfg['asset_branch']], work)
            batch = []; size = 0
    if batch:
        command(['git', 'add', '--', *batch], work); command(['git', 'commit', '-qm', 'Freeze reviewed delivery assets and manifests [skip ci]'], work)
        for repo, _ in (PRIMARY, BACKUP): command(['git', 'push', 'https://github.com/' + repo + '.git', 'HEAD:refs/heads/' + cfg['asset_branch']], work)
    asset_commit = command(['git', 'rev-parse', 'HEAD'], work)
    receipt = {'schema_version':3,'revision': cfg['revision'], 'asset_branch': cfg['asset_branch'], 'asset_commit': asset_commit,'backup_master_expected':cfg['backup_master_expected'], 'archives': []}
    for role, (repo, branch) in [('primary', PRIMARY), ('backup', BACKUP)]:
        parent = api.api(repo, 'git/ref/heads/' + branch)['object']['sha']; require(parent == cfg['expected_heads'][role], 'Concurrent destination change; stop without force')
        base = api.api(repo, 'git/commits/' + parent)['tree']['sha']; cache = {}; verified_blobs = set()
        def listing(tree):
            if tree not in cache:
                data = api.api(repo, 'git/trees/' + tree); require(not data.get('truncated'), 'Truncated shallow tree')
                cache[tree] = {r['path']: {k: r[k] for k in ('path', 'mode', 'type', 'sha')} for r in data['tree']}
            return copy.deepcopy(cache[tree])
        patches = {}
        for p in allfiles:
            name = str(p.relative_to(work)); node = patches
            for part in name.split('/')[:-1]: node = node.setdefault(part, {})
            node[name.split('/')[-1]] = {'@leaf': {'mode': '100644', 'type': 'blob', 'sha': command(['git', 'rev-parse', asset_commit + ':' + name], work)}}
        def graft(oldtree, patch):
            existing = listing(oldtree) if oldtree else {}
            for name, value in patch.items():
                leaf = value.get('@leaf')
                if leaf is None:
                    leaf = {'mode': '040000', 'type': 'tree', 'sha': graft(existing.get(name, {}).get('sha'), value)}
                existing[name] = {'path': name, **leaf}
            return api.api(repo, 'git/trees', 'POST', {'tree': list(existing.values())})['sha']
        tree = graft(base, patches)
        commit = api.api(repo, 'git/commits', 'POST', {'message': cfg['revision'] + ': archive verified 4K videos, sources and QC [skip ci]', 'tree': tree, 'parents': [parent]})['sha']
        api.api(repo, 'git/refs/heads/' + branch, 'PATCH', {'sha': commit, 'force': False})
        require(api.api(repo, 'git/ref/heads/' + branch)['object']['sha'] == commit, 'Destination ref verification failed')
        # Verify each canonical/new-order MP4 by Git blob identity AND remote stored size.
        for rec in final['articles']:
            for path in (rec['canonical_path'], rec['reordered_path']):
                blob = command(['git', 'rev-parse', asset_commit + ':' + path], work)
                if blob not in verified_blobs:
                    remote = api.api(repo, 'git/blobs/' + blob)
                    require(remote['size'] == rec['bytes'] and remote.get('encoding') == 'base64', 'Remote MP4 byte count/encoding mismatch')
                    require(hashlib.sha256(base64.b64decode(remote['content'])).hexdigest() == rec['sha256'], 'Remote actual MP4 SHA-256 mismatch')
                    verified_blobs.add(blob)
                parts = path.split('/'); node = tree
                for index, part in enumerate(parts):
                    entry = listing(node).get(part); require(entry is not None, 'Missing archived MP4 path')
                    if index == len(parts) - 1: require(entry['sha'] == blob, 'Archived MP4 content identity mismatch')
                    else: node = entry['sha']
        require(api.api(BACKUP[0], 'git/ref/heads/master')['object']['sha'] == cfg['backup_master_expected'], 'Protected master changed')
        receipt['archives'].append({'role': role, 'repository': repo, 'branch': branch, 'previous_commit': parent, 'commit': commit,
                                    'both_video_paths_verified': True, 'backup_master_unchanged': True})
        write(work.parent / (work.name + '-archive-receipt.json'), receipt)
    return receipt


def remote_release_assets(api,release_id):
    rows=[];page=1
    while True:
        part=api.api(PRIMARY[0],f'releases/{release_id}/assets?per_page=100&page={page}');rows+=part
        if len(part)<100:return rows
        page+=1


def verify_public_release_receipt(api,data,archive_receipt):
    import release_actions as R
    require(data['schema_version']==3 and data['passed']is True and data['release_public']is True and data['all_remote_bytes_and_digests_verified']is True,'Actual public remote verification receipt required')
    require(data['repository']==PRIMARY[0]and data['asset_commit']==archive_receipt['asset_commit']and data['revision']==archive_receipt['revision'],'Receipt/archive identity mismatch')
    primary=next(r for r in archive_receipt['archives']if r['role']=='primary')
    require(primary['repository']==PRIMARY[0]and primary['branch']==PRIMARY[1]and primary['commit']==data['primary_archive_commit'],'Receipt not bound to actual primary archive commit')
    release=api.api(PRIMARY[0],f'releases/{data["release_id"]}')
    require(not release['draft']and release['tag_name']==data['revision']==data['tag_name']and release['html_url']==data['release_url'],'New public release identity differs')
    obj=api.api(PRIMARY[0],'git/ref/tags/'+urllib.parse.quote(data['tag_name'],safe=''))['object'];seen=set()
    while obj['type']=='tag':
        require(obj['sha']not in seen,'Tag cycle');seen.add(obj['sha']);obj=api.api(PRIMARY[0],'git/tags/'+obj['sha'])['object']
    require(obj['type']=='commit'and obj['sha']==data['primary_archive_commit'],'Actual public tag changed')
    manifest_bytes=R.raw_primary(data['finalization_manifest_path'],data['primary_archive_commit'])
    require(hashlib.sha256(manifest_bytes).hexdigest()==data['finalization_manifest_sha256'],'Frozen primary manifest changed')
    manifest=json.loads(manifest_bytes);planned=exact_assets(manifest['articles'],data['published_pdf'])
    require(planned==data['planned_assets']==manifest['exact_release_assets']and manifest['published_pdf']==data['published_pdf'],'Remote receipt71 inventory/PDF differs from actual immutable source manifest')
    actual=remote_release_assets(api,data['release_id']);require([a['name']for a in actual]==[a['name']for a in planned]and len(actual)==71,'Actual remote asset count/order differs')
    verified=[R.verify_asset(a,b)for a,b in zip(actual,planned)];require(verified==data['assets'],'Actual remote asset IDs/bytes/digests changed after receipt')
    return planned


def commit_records(api,repo,branch,files,message):
    """Narrow non-force metadata graft on the latest actual HEAD; never writes backup master."""
    require((repo,branch)in(PRIMARY,BACKUP),'Unapproved destination branch')
    parent=api.api(repo,'git/ref/heads/'+branch)['object']['sha'];base=api.api(repo,'git/commits/'+parent)['tree']['sha'];patch={};blobs={};cache={}
    for path,content in files.items():
        relpath(path);require(len(content)<MAX_BLOB,'Receipt record too large')
        obj=api.api(repo,'git/blobs','POST',{'content':base64.b64encode(content).decode(),'encoding':'base64'});blobs[path]=obj['sha'];node=patch
        for part in path.split('/')[:-1]:node=node.setdefault(part,{})
        node[path.split('/')[-1]]={'@leaf':{'mode':'100644','type':'blob','sha':obj['sha']}}
    def listing(tree):
        if tree not in cache:
            result=api.api(repo,'git/trees/'+tree);require(not result.get('truncated'),'Truncated receipt tree');cache[tree]={e['path']:{k:e[k]for k in('path','mode','type','sha')}for e in result['tree']}
        return copy.deepcopy(cache[tree])
    def graft(tree,changes):
        out=listing(tree)if tree else{}
        for name,value in changes.items():
            leaf=value.get('@leaf')or{'mode':'040000','type':'tree','sha':graft(out.get(name,{}).get('sha'),value)};out[name]={'path':name,**leaf}
        return api.api(repo,'git/trees','POST',{'tree':list(out.values())})['sha']
    newtree=graft(base,patch);commit=api.api(repo,'git/commits','POST',{'message':message,'tree':newtree,'parents':[parent]})['sha']
    require(api.api(repo,'git/ref/heads/'+branch)['object']['sha']==parent,'Receipt destination moved concurrently; retry from latest HEAD')
    api.api(repo,'git/refs/heads/'+branch,'PATCH',{'sha':commit,'force':False})
    require(api.api(repo,'git/ref/heads/'+branch)['object']['sha']==commit,'Receipt HEAD verification failed')
    for path,blob in blobs.items():
        stored=api.api(repo,'git/blobs/'+blob);require(stored['encoding']=='base64'and base64.b64decode(stored['content'])==files[path],'Remote receipt blob bytes differ')
    return {'repository':repo,'branch':branch,'previous_commit':parent,'commit':commit,'blobs':blobs,'remote_bytes_verified':True}


def persist_release_receipt(archive_receipt_path,publication_proof_path,execute=False):
    require(execute,'Receipt publication needs explicit --execute')
    archive_receipt=load(archive_receipt_path);proof=load(publication_proof_path);api=GitHub()
    require(archive_receipt['schema_version']==3 and {(r['repository'],r['branch'])for r in archive_receipt['archives']}=={PRIMARY,BACKUP}and len(archive_receipt['archives'])==2,'Actual V3 dual archive receipt required')
    require(proof['repository']==PRIMARY[0],'Unexpected publisher artifact repository')
    run=api.api(PRIMARY[0],f'actions/runs/{proof["run_id"]}')
    require(run['path']==WORKFLOW and run['conclusion']=='success','Actual native publishing workflow did not pass')
    art=api.api(PRIMARY[0],f'actions/artifacts/{proof["artifact_id"]}')
    require(not art['expired']and art.get('workflow_run',{}).get('id')==proof['run_id']and art.get('digest')=='sha256:'+proof['artifact_zip_sha256'],'Publisher receipt artifact identity differs')
    blob=api.raw_artifact(PRIMARY[0],proof['artifact_id']);require(hashlib.sha256(blob).hexdigest()==proof['artifact_zip_sha256'],'Actual publisher artifact ZIP SHA differs')
    import io
    from release_contract import safe_path
    safe_path(proof['receipt_member'])
    with zipfile.ZipFile(io.BytesIO(blob))as z:
        require(len(z.namelist())==len(set(z.namelist())),'Duplicate publisher receipt ZIP members');data_bytes=z.read(proof['receipt_member'])
    data=json.loads(data_bytes);require(data['publisher_workflow_run_id']==proof['run_id']and data['publisher_workflow_head_sha']==run['head_sha']and data['publisher_workflow_path']==WORKFLOW,'Receipt is not from selected actual native workflow')
    planned=verify_public_release_receipt(api,data,archive_receipt)
    expected_master=archive_receipt['backup_master_expected'];require(api.api(BACKUP[0],'git/ref/heads/master')['object']['sha']==expected_master,'Protected backup master changed')
    inventory=json.dumps({'schema_version':3,'revision':data['revision'],'assets':planned},ensure_ascii=False,indent=2).encode()+b'\n';sums=''.join(a['sha256']+'  '+a['name']+'\n'for a in planned).encode()
    require(hashlib.sha256(inventory).hexdigest()==data['repository_asset_inventory_sha256']and hashlib.sha256(sums).hexdigest()==data['repository_sha256sums_sha256'],'Repository inventory/SHA bytes do not match immutable stage')
    files={data['remote_receipt_repo_path']:data_bytes,data['repository_asset_inventory_path']:inventory,data['repository_sha256sums_path']:sums}
    archived=[commit_records(api,repo,branch,files,data['revision']+': preserve actual71-file remote receipt [skip ci]')for repo,branch in(PRIMARY,BACKUP)]
    verification={'schema_version':3,'passed':True,'delivery_complete':True,'release_public':True,'revision':data['revision'],'release_id':data['release_id'],'release_url':data['release_url'],
        'remote_receipt_path':data['remote_receipt_repo_path'],'remote_receipt_sha256':hashlib.sha256(data_bytes).hexdigest(),'publisher_proof':proof,'primary_archive_commit':data['primary_archive_commit'],
        'asset_commit':data['asset_commit'],'receipt_archives':archived,'all71_remote_assets_verified':True,'backup_master_expected':expected_master}
    vpath=data['audit_path']+'/DUAL-ARCHIVE-VERIFICATION.json';vbytes=json.dumps(verification,ensure_ascii=False,indent=2).encode()+b'\n'
    ack=[commit_records(api,repo,branch,{vpath:vbytes},data['revision']+': record verified dual-repository delivery [skip ci]')for repo,branch in(PRIMARY,BACKUP)]
    require(api.api(BACKUP[0],'git/ref/heads/master')['object']['sha']==expected_master,'Protected backup master changed')
    result={**verification,'verification_record_path':vpath,'verification_record_sha256':hashlib.sha256(vbytes).hexdigest(),'verification_archives':ack}
    write(Path(archive_receipt_path).with_name(Path(archive_receipt_path).stem+'-release-receipt.json'),result);return result


def verify_record_reference(api,row,path,expected_sha256):
    require((row['repository'],row['branch'])in(PRIMARY,BACKUP),'Unexpected record destination')
    compare=api.api(row['repository'],'compare/'+row['commit']+'...'+urllib.parse.quote(row['branch'],safe=''))
    require(compare['status']in('ahead','identical'),'Receipt commit not on designated branch')
    blob=row['blobs'][path];entry=api.api(row['repository'],'contents/'+urllib.parse.quote(path,safe='/')+'?ref='+row['commit'])
    require(entry['sha']==blob,'Receipt blob not stored at exact committed path')
    stored=api.api(row['repository'],'git/blobs/'+blob);data=base64.b64decode(stored['content'])
    require(hashlib.sha256(data).hexdigest()==expected_sha256,'Actual committed receipt bytes differ');return data


def cleanup_old_releases(dual_receipt_path,targets_path,execute=False):
    require(execute,'Exact old-release cleanup needs explicit --execute')
    result=load(dual_receipt_path);targets=load(targets_path);api=GitHub()
    require(result['passed']and result['delivery_complete']and len(result['verification_archives'])==2 and {(r['repository'],r['branch'])for r in result['verification_archives']}=={PRIMARY,BACKUP},'New delivery must first be permanently verified in both repositories')
    for row in result['verification_archives']:verify_record_reference(api,row,result['verification_record_path'],result['verification_record_sha256'])
    # Freshly revalidate public exact71 assets using the immutable native receipt.
    require(len(result['receipt_archives'])==2 and {(r['repository'],r['branch'])for r in result['receipt_archives']}=={PRIMARY,BACKUP},'Both permanent native receipts required')
    for row in result['receipt_archives']:receipt_bytes=verify_record_reference(api,row,result['remote_receipt_path'],result['remote_receipt_sha256'])
    data=json.loads(receipt_bytes)
    archive={'revision':result['revision'],'asset_commit':result['asset_commit'],'archives':[{'role':'primary','repository':PRIMARY[0],'branch':PRIMARY[1],'commit':result['primary_archive_commit']}]}
    verify_public_release_receipt(api,data,archive)
    require(isinstance(targets,list)and targets and len({(t['repository'],t['release_id'])for t in targets})==len(targets),'Explicit distinct old-release targets required')
    actual=[]
    for t in targets:
        require(set(t)=={'repository','release_id','tag_name','html_url'}and t['repository']in(PRIMARY[0],BACKUP[0]),'Exact repository/id/tag/url allowlist required; Git tags are never deleted')
        require(not(t['repository']==PRIMARY[0]and(t['release_id']==data['release_id']or t['tag_name']==data['tag_name'])),'New release/tag is protected')
        current=api.api(t['repository'],f'releases/{t["release_id"]}')
        require(current['id']==t['release_id']and current['tag_name']==t['tag_name']and current['html_url']==t['html_url'],'Old release identity changed; cleanup rejected')
        actual.append(t)
    report={'schema_version':3,'revision':data['revision'],'new_release_id':data['release_id'],'new_release_verified_again':True,'authorized_exact_targets':actual,'deleted_exact_releases':[],'git_tags_deleted':False,'status':'running'}
    local=Path(dual_receipt_path).with_name(Path(dual_receipt_path).stem+'-cleanup.json');write(local,report);error=None
    try:
        for t in actual:
            api.api(t['repository'],f'releases/{t["release_id"]}','DELETE');report['deleted_exact_releases'].append(t);write(local,report)
        report['status']='completed'
    except Exception as exc:
        error=exc;report['status']='partial_failure';report['error']=str(exc)
    path=data['audit_path']+'/EXACT-OLD-RELEASE-CLEANUP.json';raw=json.dumps(report,ensure_ascii=False,indent=2).encode()+b'\n';report['archives']=[];archive_errors=[]
    for repo,branch in(PRIMARY,BACKUP):
        try:report['archives'].append(commit_records(api,repo,branch,{path:raw},data['revision']+': record exact authorized old-release cleanup [skip ci]'))
        except Exception as exc:archive_errors.append({'repository':repo,'error':str(exc)})
    report['archive_errors']=archive_errors;write(local,report)
    require(error is None and not archive_errors,'Exact cleanup/record archival incomplete; actual partial results saved at '+str(local));return report


def dispatch(receipt_path, execute=False):
    require(execute, 'Workflow dispatch requires explicit --execute')
    receipt = load(receipt_path); require(len(receipt['archives']) == 2, 'Archive both repositories first')
    primary = next(r for r in receipt['archives'] if r['role'] == 'primary')
    GitHub().api(PRIMARY[0], 'actions/workflows/publish-video-revisions.yml/dispatches', 'POST',
        {'ref': 'main', 'inputs': {'asset_commit': receipt['asset_commit'], 'target_commit': primary['commit'], 'revision': receipt['revision']}})


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='cmd', required=True)
    v = sub.add_parser('validate'); v.add_argument('config')
    s = sub.add_parser('stage'); s.add_argument('config'); s.add_argument('output')
    a = sub.add_parser('archive'); a.add_argument('stage'); a.add_argument('--execute', action='store_true')
    d = sub.add_parser('dispatch'); d.add_argument('receipt'); d.add_argument('--execute', action='store_true')
    q=sub.add_parser('persist-release-receipt');q.add_argument('archive_receipt');q.add_argument('publication_proof');q.add_argument('--execute',action='store_true')
    c=sub.add_parser('cleanup-old-releases');c.add_argument('dual_receipt');c.add_argument('targets');c.add_argument('--execute',action='store_true')
    args = p.parse_args()
    if args.cmd == 'validate': print(json.dumps({'passed': True, 'articles': len(validate(load(args.config))), 'published': False}))
    elif args.cmd == 'stage': print(stage(args.config, args.output))
    elif args.cmd == 'archive': print(json.dumps(archive(args.stage, args.execute), ensure_ascii=False))
    elif args.cmd == 'dispatch': dispatch(args.receipt, args.execute)
    elif args.cmd == 'persist-release-receipt':print(json.dumps(persist_release_receipt(args.archive_receipt,args.publication_proof,args.execute),ensure_ascii=False))
    elif args.cmd == 'cleanup-old-releases':print(json.dumps(cleanup_old_releases(args.dual_receipt,args.targets,args.execute),ensure_ascii=False))

if __name__ == '__main__': main()
