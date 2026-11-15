"""Offline contract tests: no GitHub calls, credentials, or external dependencies."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import io
import json
import struct
import unittest
import zipfile
import publish_release as p


def png(width, height):
    return b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', width, height) + b'\x08\x02\0\0\0' + b'\0' * 4


def jpeg(width, height):
    return b'\xff\xd8\xff\xe0\x00\x04ab\xff\xc0\x00\x08\x08' + struct.pack('>HH', height, width) + b'\x00\xff\xd9'


def fixture():
    titles = [{'order': f'{n:02}', 'source_id': f'{n:02}', 'title_zh': f'标题{n}', 'title_en': f'Title {n}'} for n in range(1, 71)]
    rows = [f"{t['order']} 🐙 {t['title_zh']}｜{t['title_en']}" for t in titles]
    originals = {p.FULL_NAME: ('\n'.join(rows) + '\n').encode(),
                 p.SHORT_NAME: ('\n'.join(r.split('｜')[0] for r in rows) + '\n').encode()}
    for name, bounds in zip(p.PART_NAMES, [(0, 18), (18, 35), (35, 53), (53, 70)]):
        originals[name] = ('\n'.join(rows[bounds[0]:bounds[1]]) + '\n').encode()
    for name, (width, height, fmt) in p.COVER_NAMES.items():
        originals[name] = png(width, height) if fmt == 'PNG' else jpeg(width, height)
    def item(name, data, prefix):
        return {'name': name, 'bytes': len(data), 'sha256': p.sha(data), 'sources': {
            role: {'repository': repo, 'commit': 'a' * 40, 'path': prefix + name}
            for role, repo in [('primary', p.PRIMARY), ('backup', p.BACKUP)]}}
    catalog = p.json_bytes({'titles': titles})
    config = {'schema': p.NAMESPACE, 'repository': p.PRIMARY, 'tag': p.TAG, 'name': p.TITLE,
              'ready': True, 'cover_source_prefix': 'B站封面/考研学人-70篇/2026-11-15-4300-v6/成品/',
              'authority': {'approved': True, 'scope': p.NAMESPACE,
                    'event_sha256': 'b' * 64, 'reference': 'ROOT-verified-offline-fixture'},
              'assets': [item(n, data, 'B站封面/考研学人-70篇/2026-11-15-4300-v6/成品/' if n in p.COVER_NAMES else p.TEXT_PREFIX)
                         for n, data in originals.items()],
              'catalog': item(p.CATALOG_NAME, catalog, p.TEXT_PREFIX)}
    return config, originals, catalog


class FakeGitHub:
    def __init__(self, files, *, tag=None, release=None):
        self.files = files
        self.tag = tag
        self.release = release
        self.remote = []
        self.mutations = []

    def request(self, path, body=None, method='GET', missing_ok=False):
        if method == 'POST':
            self.mutations.append(method)
            self.release = {**body, 'id': 42, 'html_url': 'https://github.com/example/release'}
            return self.release
        if method == 'PATCH':
            self.mutations.append(method)
            self.release.update(body)
            self.tag = {'object': {'type': 'commit', 'sha': self.release['target_commitish']}}
            return self.release
        if '/git/ref/' in path:
            return self.tag
        if '/releases/tags/' in path:
            return self.release
        raise RuntimeError('unexpected fake endpoint ' + path)

    def assets(self, rid):
        return list(self.remote)

    def upload(self, tag, path):
        self.mutations.append('UPLOAD')
        data = path.read_bytes()
        self.remote.append({'id': len(self.remote) + 1, 'name': path.name, 'size': len(data),
            'digest': 'sha256:' + p.sha(data), 'state': 'uploaded',
            'browser_download_url': f'https://github.com/{p.PRIMARY}/releases/download/{p.TAG}/{path.name}'})


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.config, self.originals, self.catalog = fixture()

    def test_config_pending_or_mutable_or_wrong_name_rejected(self):
        p.validate_config(self.config)
        for mutate in [lambda c: c.update(ready=False),
                       lambda c: c.update(cover_source_prefix='B站封面/考研学人-70篇/2026-11-15-4300-v5/成品/'),
                       lambda c: c['authority'].update(approved=False),
                       lambda c: c['assets'][0]['sources']['backup'].update(commit=None),
                       lambda c: c['assets'][0]['sources']['backup'].update(commit='main'),
                       lambda c: c['assets'][0]['sources']['primary'].update(path='../private'),
                       lambda c: c['assets'][0].update(name='old-draft.txt')]:
            bad = deepcopy(self.config)
            mutate(bad)
            with self.assertRaises(ValueError):
                p.validate_config(bad)

    def test_dual_readback_rejects_one_bad_stream(self):
        item = self.config['assets'][0]
        data = self.originals[item['name']]
        result, records = p.fetch_dual(item, lambda url, size: data)
        self.assertEqual(result, data)
        self.assertEqual(len(records), 2)
        with self.assertRaises(ValueError):
            p.fetch_dual(item, lambda url, size: data if p.PRIMARY in url else data[:-1])

    def test_image_dimensions_and_truncation(self):
        self.assertEqual(p.image_header(png(1440, 1080)), (1440, 1080, 'PNG'))
        self.assertEqual(p.image_header(jpeg(1600, 900)), (1600, 900, 'JPEG'))
        for data in [b'', png(1, 2)[:20], jpeg(1, 2)[:10], b'\xff\xd8\xff\xda\0\2']:
            with self.assertRaises(ValueError):
                p.image_header(data)

    def test_exact_titles_and_missing_reordered_part(self):
        self.assertTrue(p.validate_titles(self.originals, self.catalog)['all70_ordered_bilingual_titles_exact'])
        for data in [self.originals[p.PART_NAMES[0]].replace(b'Title 1', b'Wrong 1', 1),
                     b'\n'.join(self.originals[p.PART_NAMES[0]].splitlines()[1:]),
                     b'\n'.join(reversed(self.originals[p.PART_NAMES[0]].splitlines()))]:
            bad = dict(self.originals)
            bad[p.PART_NAMES[0]] = data
            with self.assertRaises(ValueError):
                p.validate_titles(bad, self.catalog)

    def test_package_is_deterministic_original_bytes_and_exact_zip(self):
        first, _ = p.build_package(self.config, self.originals, self.catalog)
        second, _ = p.build_package(self.config, self.originals, self.catalog)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 13)
        for name, data in self.originals.items():
            self.assertEqual(first[name], data)
        inside = {n: b for n, b in first.items() if n != p.ZIP_NAME}
        self.assertTrue(p.verify_zip(first[p.ZIP_NAME], inside))
        wrong = dict(inside)
        wrong[p.FULL_NAME] += b'changed'
        with self.assertRaises(ValueError):
            p.verify_zip(first[p.ZIP_NAME], wrong)
        corrupt = bytearray(first[p.ZIP_NAME])
        with zipfile.ZipFile(io.BytesIO(corrupt)) as archive:
            member = archive.infolist()[0]
            offset = member.header_offset + 30 + len(member.filename.encode()) + len(member.extra)
        corrupt[offset] ^= 1
        with self.assertRaises((ValueError, zipfile.BadZipFile)):
            p.verify_zip(bytes(corrupt), inside)

    def test_changed_image_dimensions_fail_even_matching_item_digest(self):
        changed = dict(self.originals)
        name = next(n for n in p.COVER_NAMES if n.endswith('.png'))
        changed[name] = png(900, 1600)
        item = next(a for a in self.config['assets'] if a['name'] == name)
        item.update(bytes=len(changed[name]), sha256=p.sha(changed[name]))
        with self.assertRaises(ValueError):
            p.build_package(self.config, changed, self.catalog)

    @patch.dict('os.environ', {'GITHUB_REPOSITORY': p.PRIMARY})
    def test_draft_publish_then_public_verify_only_and_collisions(self):
        files, _ = p.build_package(self.config, self.originals, self.catalog)
        gh = FakeGitHub(files)
        with TemporaryDirectory() as temp:
            output = Path(temp)
            for name, data in files.items():
                (output / name).write_bytes(data)
            fetch = lambda url, size: files[url.rsplit('/', 1)[1]]
            report = p.publish(self.config, files, output, 'c' * 64, 'd' * 40, gh, fetch)
            self.assertEqual(report['asset_count'], 13)
            self.assertEqual(gh.mutations.count('UPLOAD'), 13)
            self.assertFalse(gh.release['draft'])
            previous = list(gh.mutations)
            p.publish(self.config, files, output, 'c' * 64, 'd' * 40, gh, fetch)
            self.assertEqual(gh.mutations, previous)
            gh.release['body'] += 'collision'
            with self.assertRaises(ValueError):
                p.publish(self.config, files, output, 'c' * 64, 'd' * 40, gh, fetch)
            self.assertEqual(gh.mutations, previous)
            gh.tag['object']['sha'] = 'e' * 40
            with self.assertRaises(ValueError):
                p.publish(self.config, files, output, 'c' * 64, 'd' * 40, gh, fetch)

    @patch.dict('os.environ', {'GITHUB_REPOSITORY': p.PRIMARY})
    def test_draft_resume_missing_tag_and_bad_remote_digest(self):
        files, _ = p.build_package(self.config, self.originals, self.catalog)
        gh = FakeGitHub(files)
        with TemporaryDirectory() as temp:
            output = Path(temp)
            for name, data in files.items():
                (output / name).write_bytes(data)
            fetch = lambda url, size: files[url.rsplit('/', 1)[1]]
            p.publish(self.config, files, output, 'c' * 64, 'd' * 40, gh, fetch)
            gh.release['draft'] = True
            gh.tag = None
            gh.remote = gh.remote[:3]
            gh.mutations = []
            p.publish(self.config, files, output, 'c' * 64, 'd' * 40, gh, fetch)
            self.assertEqual(gh.mutations.count('UPLOAD'), 10)
            gh.remote[0]['digest'] = 'sha256:' + '0' * 64
            before = list(gh.mutations)
            with self.assertRaises(ValueError):
                p.publish(self.config, files, output, 'c' * 64, 'd' * 40, gh, fetch)
            self.assertEqual(gh.mutations, before)


if __name__ == '__main__':
    unittest.main()
