"""Inactive proposal: exact source46/book48 user-format compatibility only.

No metadata flag grants format permission; audio metadata is not approved by this helper. A separately reviewed binding must pin the
immutable final JSON bytes, actual loader-selected runtime path, and raw user
evidence. Missing, stale, malformed, or mismatched proof means False.
"""
import hashlib
import json
import os
from pathlib import Path

KIND = 'source46-book48-exact-user-format-portable-text-binding-v3'
BINDING_NAME = '_source46_exact_user_format_binding.json'
ORIGINAL_GATE_PINS = {
    '踩坑核查.py': 'f6efb9df33705fadac3d78d588adb722b4f07eab134818983a869f1d9e0c748d',
    '破折号.py': '39c48548d75a730ff7641b37d7a132fa0a14d8a65d1d179541922a649d18722f',
}
EVIDENCE = {'authority': {'file': 'authority.json', 'sha256': '82cd0b5dbe9b796faef7c8c108aad00efef68fb9797d7eaef6d8ea5a97da9038'}, 's4': {'file': 's4.json', 'sha256': '87dac2ac129f1953d73685af1e209d1e0249fb7d5382f38ddd6138ece3adea4c'}, 's10': {'file': 's10.json', 'sha256': 'dfb01ca8488289913df5d08dc3747815eb00c9fd670535b85c2ad9f2438f2cbe'}}
S4_TRANSLATION = '事实上，昆虫本能地保持背部朝向任何最亮的东西, 通常是天空, 以保持平稳。'
S4_VALUES = {
    'S4-1': ('事实上，昆虫**本能地**(instinctively)保持背部朝向任何最亮的东西, ',
             ['事实上，', '昆虫', '**本能地**(instinctively)', '保持', '背部', '朝向', '任何最亮的东西, ']),
    'S4-2': ('通常是天空, 以保持平稳。', ['通常是', '天空, ', '以保持', '平稳。']),
}
S10_EXPLANATION = 'reciprocate - 指情感上和行为上的回应'
S10_NOTE = '（under red or blue light：条件状语）\n（' + S10_EXPLANATION + '）'


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key')
        out[key] = value
    return out


def _load(raw):
    return json.loads(raw, object_pairs_hook=_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def _read_pin(pin):
    path = Path(pin['path'])
    if not path.is_absolute() or str(path.resolve(strict=True)) != pin['path']:
        raise ValueError('proof path must be the exact canonical path')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise ValueError('raw SHA256 mismatch')
    return raw, _load(raw)


def verify_evidence():
    """Read fixed evidence paths; caller cannot supply replacement assertions."""
    root, tools, work, request = _runtime_paths()
    proof = root / '.github/video-revision-batch/source46-user-format-proofs'
    docs = {key: _read_pin({'path': str(proof / pin['file']), 'sha256': pin['sha256']})[1] for key, pin in EVIDENCE.items()}
    if any(doc.get('source_id') != '46' or doc.get('book_order') != 48 for doc in docs.values()):
        raise ValueError('source/book identity mismatch')
    authority, s4, s10 = (docs[key] for key in ('authority', 's4', 's10'))
    if not (authority.get('kind') == 'actual-user-finalization-authority-book48-source46-after-all-feedback'
            and authority.get('final_4K_generation_authorized') is True
            and authority.get('include_all_actual_latest_book48_feedback_before_this_authority') is True
            and authority.get('no_quality_gate_or_numeric_threshold_changes_authorized') is True
            and authority.get('raw_user_text_verbatim') == '48篇定稿，第48篇定稿。这一篇定稿，这一篇定稿。记住，记住最后这个0.6，记住最后这个0.6。然后然然后这个前47天都已经弄好了吗？全都搞定了吗？'):
        raise ValueError('actual finalization authority mismatch')
    if not (s4.get('kind') == 'actual-latest-user-book48-translation-advice-collecting-not-final'
            and s4.get('source_location') == {'sentence': 'S4', 'chunks': ['C1', 'C2']}
            and s4.get('requested_translation_verbatim') == S4_TRANSLATION
            and s4.get('raw_user_text_verbatim') == '这个地方的翻译修改一下：改为：' + S4_TRANSLATION):
        raise ValueError('S4 actual user evidence mismatch')
    if not (s10.get('kind') == 'actual-new-user-request-book48-S10-translation-focus-and-note-collecting-v5'
            and s10.get('source_location') == 'S10 C1 C2'
            and s10.get('new_exact_note_text') == S10_EXPLANATION
            and '写上这个小字，小字，小字：' + S10_EXPLANATION in s10.get('raw_user_text_verbatim', '')
            and s10.get('under_red_or_blue_condition_note_and_second_ellipsis_note_preserved') is True):
        raise ValueError('S10 actual user evidence mismatch')


def verify_source_values(d):
    if d.get('no') != '46':
        raise ValueError('source JSON must identify source46')
    for location, (value, chinese_align) in S4_VALUES.items():
        chunk = d['sentences'][3]['chunks'][int(location[-1]) - 1]
        if chunk['zh'] != value or [pair[1] for pair in chunk['align']] != chinese_align:
            raise ValueError('exact S4 translation/Chinese align mismatch')
    if d['sentences'][9]['chunks'][0].get('note') != S10_NOTE:
        raise ValueError('exact S10 note mismatch')



REQUEST_SHA256 = '118f49d11edf54345cdc4064ca4241f5aa7cecc3a00ff646f610f5e3f003d1f7'
TEXT_PROJECTION_SHA256 = 'd6ada96f623758d2c0d3b3be782ea9a4e55eea2dcda410b0dab06d9e260ff9a8'
ACTIVE_PROGRAMS = {'踩坑核查.py': 'e13cb4a1fdfcf80641748f4052d4d80ca8b539071453d82f9c2736551011a26b', '破折号.py': '8837131165b423390bc9b7ee856dd9f5d24eb2adbc4c17f0591d79cb478da061', 'make_video.py': '935fe59fa6c212b1d43ad325f17cedd6392dcc774f7e43e0171479e419ffd5b9'}
EXPECTED_BINDING = {'kind': 'source46-book48-exact-user-format-portable-text-binding-v3', 'status': 'ROOT_REVIEWED_EXACT_USER_FORMAT_TEXT_PROJECTION', 'source_id': '46', 'book_order': 48, 'final_request_raw_sha256': '118f49d11edf54345cdc4064ca4241f5aa7cecc3a00ff646f610f5e3f003d1f7', 'text_projection_sha256': 'd6ada96f623758d2c0d3b3be782ea9a4e55eea2dcda410b0dab06d9e260ff9a8', 'runtime_data_requirement': 'complete parsed passed data equals actual disk JSON', 'audio_metadata_authorization_by_this_format_helper': False, 'evidence': {'authority': {'file': 'authority.json', 'sha256': '82cd0b5dbe9b796faef7c8c108aad00efef68fb9797d7eaef6d8ea5a97da9038'}, 's4': {'file': 's4.json', 'sha256': '87dac2ac129f1953d73685af1e209d1e0249fb7d5382f38ddd6138ece3adea4c'}, 's10': {'file': 's10.json', 'sha256': 'dfb01ca8488289913df5d08dc3747815eb00c9fd670535b85c2ad9f2438f2cbe'}}, 'active_three_program_sha256': {'踩坑核查.py': 'e13cb4a1fdfcf80641748f4052d4d80ca8b539071453d82f9c2736551011a26b', '破折号.py': '8837131165b423390bc9b7ee856dd9f5d24eb2adbc4c17f0591d79cb478da061', 'make_video.py': '935fe59fa6c212b1d43ad325f17cedd6392dcc774f7e43e0171479e419ffd5b9'}, 'unreviewed_text_or_extra_format_error': 'REJECT'}
CI_ROOT = '/home/runner/work/literate-enigma/literate-enigma'
LOCAL_REHEARSAL_ROOT = '/dev/shm/source46-official-exact-format-text-projection-CI-v3-20261115/rehearsal/repository'


def _runtime_paths():
    # The only local profile is an explicitly named non-production rehearsal.
    root = Path(os.environ['XG_P'])
    if str(root) not in (CI_ROOT, LOCAL_REHEARSAL_ROOT) or root.resolve(strict=True) != root:
        raise ValueError('unreviewed checkout root')
    tools = root / '视频/工具'
    if Path(os.environ['XG_TOOLS']).resolve(strict=True) != tools:
        raise ValueError('wrong tools root')
    temp = Path(os.environ['RUNNER_TEMP'])
    if not temp.is_absolute() or temp.resolve(strict=True) != temp:
        raise ValueError('noncanonical original RUNNER_TEMP')
    machine = temp / 'completion-machine'
    work = machine / 'video'
    if (Path(os.environ['VIDEO_ROOT']).resolve(strict=True) != machine
            or Path(os.environ['XG_WORK']).resolve(strict=True) != work
            or Path.cwd().resolve(strict=True) != work):
        raise ValueError('wrong original work/cwd relationship')
    # The original G27 copier imports this module into W as well as T.
    this = Path(__file__).resolve(strict=True)
    if this not in (tools / '_source46_exact_user_format.py', work / '_source46_exact_user_format.py'):
        raise ValueError('wrong helper origin')
    if this.read_bytes() != (tools / '_source46_exact_user_format.py').read_bytes():
        raise ValueError('stale work helper')
    request = root / '.github/video-revision-batch/request/46/视频/脚本/46.json'
    return root, tools, work, request


def _text_projection(d):
    field = lambda obj, key: {'present': key in obj, 'value': obj.get(key)}
    value = {key: field(d, key) for key in ('no','title_en','title_zh','title_fx','术语')}
    value['sentences'] = [{'para': field(sentence,'para'),
        'chunks': [{key: field(chunk,key) for key in ('en','zh','align','note')} for chunk in sentence['chunks']]}
        for sentence in d['sentences']]
    return _canonical(value)

def _bound(d, no):
    try:
        if str(no) != '46' or d.get('no') != '46':
            return False
        root, tools, work, request = _runtime_paths()
        binding = _load((tools / BINDING_NAME).read_bytes())
        if _canonical(binding) != _canonical(EXPECTED_BINDING):
            return False
        for name, digest in ACTIVE_PROGRAMS.items():
            p = tools / name
            if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
                return False
        request_raw, request_d = _read_pin({'path': str(request), 'sha256': REQUEST_SHA256})
        # This guard only identifies the three explicitly requested text formats.
        # It grants no approval to audio controls or confirmation metadata.
        selected = work / 'scripts/46.json'
        if selected.resolve(strict=True) != selected:
            return False
        runtime_d = _load(selected.read_bytes())
        if not (_canonical(runtime_d) == _canonical(d)
                and hashlib.sha256(_text_projection(d).encode()).hexdigest() == TEXT_PROJECTION_SHA256
                and hashlib.sha256(_text_projection(request_d).encode()).hexdigest() == TEXT_PROJECTION_SHA256):
            return False
        verify_evidence()
        verify_source_values(d)
        return True
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, RuntimeError):
        return False


def permits_ascii_comma(d, no, location, value):
    if location not in S4_VALUES or value != S4_VALUES[location][0]:
        return False
    return _bound(d, no)


def permits_note_hyphen(d, no, location, value, match):
    expected = S10_NOTE.index(' - ') + 1
    if not (location == 'S10-1 note' and value == S10_NOTE
            and match.group(0) == '-' and match.span() == (expected, expected + 1)):
        return False
    return _bound(d, no)
