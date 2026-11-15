"""Concrete f188 wrapper. Existing installer and immutable observer only.

No whole observer, original maker main/build, TTS, ASR or gain computation runs.
The original cached machine's video inode is isolated and restored by the same
already-reviewed original observer.work_namespace context manager.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, subprocess, sys, traceback
sys.dont_write_bytecode = True

ROOT_SHA = 'f188560294cd4a373ed2bde7495d23639cf928b28aef329864d1106fd6986490'
HELPER_SHA = '153b4daae5908691a05a9d0f7cefdb752cbef644d64ce37a424d8da452c47f63'
PROFILE_SHA = '1dd0651c9c27bb34977334bb9bc7410b3b54dce978f2f971e46c7a1605dc7fc7'
ARGV_SHA = '661a572a939908d76c4ec02fae6b13fa36b74df48fa4dcd34d84f5fc2e8546b1'
H_SHA = '6a1903302b95a72b496072cfd2df3bd3c23e50b156c00fd5a2ed2fe6cf286b0c'
SOURCE_SHA = 'dc3fec8cb898d8a7279739b6c4c62d38caf509580e26511acd95d07f1bbc18ef'
MOTHER_KEY = 'Linux-native56-exact-S11-first-spoken-comma-43721094194'
MOTHER_VERSION = '7368862e74747836adc191d99e433a5c870b2d184e3f9e387280fecd8c07432c'
MATH_KEY = 'Linux-native56-only-target-whole-original-math-43729197848'
MATH_VERSION = 'e64dc6e131ead6fee8e56c8b20ae45b4234f00b5f4a12a556d02eaa69af30a6c'


def require(value, message):
    if not value: raise AssertionError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def validate_root(path, literal_sha, package):
    p = Path(path)
    require(literal_sha == ROOT_SHA and p.is_file() and not p.is_symlink() and sha(p) == ROOT_SHA,
            'Mandatory actual f188 ROOT CLI file/fullSHA required before setup')
    require(p.read_bytes() == (Path(package) / 'root-S11-breath-execution-adoption.json').read_bytes(), 'ROOT transport copy differs')
    value = json.loads(p.read_text())
    require(value['reviewed_handoff']['sha256'] == H_SHA and value['program']['sha256'] == HELPER_SHA and
            value['profile']['sha256'] == PROFILE_SHA and value['exact_profile_scope'] ==
            {'source': '56', 'book': 65, 'sentence': 'S11', 'w_seconds': [1.95, 2.7],
             'only_first_spoken_comma_removed_display_both_commas_kept': True, 'BREATH_FRAC': .7},
            'Actual ROOT record must bind this exact reviewed S11 program/profile/scope')
    return value


def verify_transport(package):
    N = Path(package)
    rows = json.loads((N / 'transport-file-pins.json').read_text())
    require(rows and len({row['relative'] for row in rows}) == len(rows), 'Finite unique transport pins required')
    for row in rows:
        rel = Path(row['relative'])
        require(not rel.is_absolute() and '..' not in rel.parts, 'Transport path escaped package')
        p = N / rel
        require(p.is_file() and not p.is_symlink() and p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], 'Frozen runtime transport differs: ' + str(rel))
    require(sha(N / 'probe/observe56_only_S11_breath_scalar.py') == HELPER_SHA and
            sha(N / 'probe/profile.json') == PROFILE_SHA and sha(N / 'native-arguments.json') == ARGV_SHA and
            sha(N / 'reviewed-code-only-H.json') == H_SHA, 'Exact adopted observer/profile/argv/H required')
    return rows


def cache_api_row(path, key, version):
    value = json.loads(Path(path).read_text())
    require(value['total_count'] == len(value['actions_caches']) == 1, 'Unique actual API cache identity required')
    row = value['actions_caches'][0]
    require(row['key'] == key and row['version'] == version and
            row['ref'] == 'refs/heads/codex/finish-05-and-summaries-20261112', 'Wrong exact actual API cache key/version/ref')
    return row


def helper_argv(package, repo, machine, tools, public):
    N = Path(package)
    require(sha(N / 'native-arguments.json') == ARGV_SHA, 'Wrong closed helper argument file')
    d = json.loads((N / 'native-arguments.json').read_text())
    require(d['root_execution_adoption_SHA256'] == ROOT_SHA, 'Argument ROOT identity differs')
    mapping = {'{{PACKAGE}}': str(N), '{{TOOLS}}': str(tools), '{{VIDEO_ROOT}}': str(machine), '{{PUBLIC}}': str(public)}
    args = []
    require(list(d['arguments']) == ['--tools', '--video-root', '--inputs', '--profile', '--output'], 'Only unchanged helper CLI supported')
    for key, value in d['arguments'].items():
        for old, new in mapping.items(): value = value.replace(old, new)
        require('{{' not in value, 'Unresolved literal CLI role')
        args.extend([key, value])
    helper = Path(repo) / d['helper']
    require(helper.resolve() == (N / 'probe/observe56_only_S11_breath_scalar.py').resolve() and sha(helper) == HELPER_SHA, 'Wrong only-S11 helper entrypoint')
    return [sys.executable, str(helper), *args]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--actual-root-execution-adoption', type=Path, required=True)
    parser.add_argument('--actual-root-execution-adoption-sha256', required=True)
    a = parser.parse_args()
    N = Path(__file__).resolve().parent
    validate_root(a.actual_root_execution_adoption, a.actual_root_execution_adoption_sha256, N)
    pins = verify_transport(N)
    ROOT = Path(os.environ['GITHUB_WORKSPACE']); M = Path(os.environ['RUNNER_TEMP']) / 'completion-machine'
    W = M / 'video'; T = ROOT / 'official-main/视频/工具'; O = ROOT / 'source56-only-S11-breath-public'
    require(not O.exists(), 'A fresh scalar-output namespace is required')
    require(all(os.environ.get(k) == '1' for k in ['AUDIO_ONLY', 'STRICT_CACHE', 'XG_NOPUSH', 'XG_KEEP_REVIEWED_GAIN', 'XG_KEEP_REVIEWED_ENDING', 'XG_KEEP_REVIEWED_CUTS']), 'Original reviewed STRICT flags required')
    require(not any(os.environ.get(k) for k in ['VOICE', 'AFFILE', 'OLD_IV_VOID', 'ONLY', 'BREATH_FRAC', 'CACHE_LOG']), 'No acoustic override')
    require(os.environ.get('S11_MOTHER_CACHE_HIT') == os.environ.get('S11_G36_CACHE_HIT') == 'true', 'Both exact existing target caches must hit')
    mother_api = cache_api_row(N / 'actual-mother-cache-API.json', MOTHER_KEY, MOTHER_VERSION)
    math_api = cache_api_row(N / 'actual-G36-cache-API.json', MATH_KEY, MATH_VERSION)
    identity = json.loads((N / 'probe/inputs/identity.json').read_text())
    C = M / 'tts/cache_tts'
    require(len(identity['actual_four_private_files']) == 4 and all(
        (C / name).is_file() and not (C / name).is_symlink() and sha(C / name) == expected
        for name, expected in identity['actual_four_private_files'].items()), 'Only exact four saved mother leaves are acceptable')
    profile = json.loads((N / 'probe/profile.json').read_text())
    require(sha(N / 'probe/inputs/source.json') == SOURCE_SHA and
            profile['inputs']['source']['sha256'] == SOURCE_SHA, 'Exact same-byte immutable final source required')
    runid = os.environ.get('GITHUB_RUN_ID', '')
    require(runid.isdigit(), 'Actual native run ID required for isolated work namespace')
    scratch = M / ('_source56_S11_breath_scalar_setup_' + runid)
    require(not scratch.exists(), 'Do not reuse an old diagnostic setup namespace')
    scratch.mkdir(); O.mkdir()
    report = {'kind': 'actual-f188-bound-original-setup-and-only-S11-scalar-caller',
        'ROOT_execution_adoption_sha256': ROOT_SHA, 'helper_sha256': HELPER_SHA, 'profile_sha256': PROFILE_SHA,
        'argv_sha256': ARGV_SHA, 'source_sha256': SOURCE_SHA, 'transport_pin_count': len(pins),
        'quality_acceptance': False, 'no_whole_TTS_new_math_GT_ASR_render_or_audio_export': True,
        'restoration': {}, 'errors': []}
    status = 1
    try:
        observer = load('_source56_S11_existing_namespace_guard', N / 'probe/inputs/observer.py')
        # Keep the original cached video inode and all its files isolated. The
        # newly initialized W is the sole setup target, and the same original
        # context manager restores the cached inode even after a failure.
        with observer.work_namespace(W, scratch, report['restoration']):
            W.mkdir()
            subprocess.run([sys.executable, str(N / 'install_actual_certified22_context.py')], check=True)
            source_dir = W / 'scripts'; source_dir.mkdir()
            source = source_dir / '56.json'
            require(not source.exists(), 'Same-byte setup must never replace an existing source')
            source.write_bytes((N / 'probe/inputs/source.json').read_bytes())
            require(sha(source) == SOURCE_SHA, 'Initial isolated source copy differs')
            restore = load('_source56_original_existing_G36_restore', N / 'restore_exact_existing_S11_G36_JSON_original.py')
            saved = M / 'tts/source56-only-target-whole-original-math-cache' / restore.NAME
            destination = C / restore.NAME
            historical = restore.restore_existing_original_math(saved, destination, os.environ['S11_G36_CACHE_HIT'])
            require(sha(saved) == sha(destination) == profile['existing_G36']['sha256'], 'Original single-G36 exact readback required')
            report['actual_target_cache_API'] = {'mother': mother_api, 'G36': math_api}
            report['historical_original_G36_readback_verbatim'] = historical
            report['wrong_historical_68_label_is_not_transport_authority'] = True
            report['actual_G36_transport_key'] = math_api['key']
            report['actual_G36_transport_version'] = math_api['version']
            status = subprocess.run(helper_argv(N, ROOT, M, T, O)).returncode
            report['unchanged_helper_exit'] = status
            require((O / '56-S11-bounded-original-breath-scalar.json').is_file(), 'Actual scalar result missing')
            scalar = json.loads((O / '56-S11-bounded-original-breath-scalar.json').read_text())
            report['unchanged_helper_diagnostic_completed'] = scalar['diagnostic_completed']
            require(status == 0 and scalar['diagnostic_completed'] is True and scalar['errors'] == [], 'Original bounded observation did not complete; never relax')
    except BaseException as error:
        report['errors'].append({'type': type(error).__name__, 'detail': str(error)})
        traceback.print_exc(); status = 1
    finally:
        report['original_cached_video_inode_and_top_PCM_restored'] = report['restoration'].get('normal_work_inode_and_PCM_restored') is True
        report['caller_completed'] = status == 0 and not report['errors'] and report['original_cached_video_inode_and_top_PCM_restored']
        if not report['caller_completed']: status = 1
        (O / '56-S11-actual-f188-binding-and-setup.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return status


if __name__ == '__main__':
    sys.exit(main())
