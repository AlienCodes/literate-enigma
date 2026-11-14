"""Narrow equivalence for an official MD sync to an already requested JSON summary.

This helper never approves new prose or a new summary.  Request/final JSON must
already agree on the embedded approved summary; the final working MD must match
that exact visible text.  The immutable old request MD remains untouched.
"""
import hashlib


def markdown_prose_equivalence(request_md, final_md, request_json, final_json,
                               article, visible_tokens, require):
    marker = '（简述：'

    def section(md, heading, stop):
        require(md.count(heading) == md.count(stop) == 1,
                f'Unique Markdown section required: {article}/{heading}')
        return md.split(heading, 1)[1].split(stop, 1)[0]

    def approved_summary(document):
        hits = [c['note'].split(marker, 1)[1].strip()
                for s in document['sentences'] for c in s['chunks']
                if marker in c.get('note', '')]
        require(len(hits) == 1 and hits[0].endswith('）'),
                f'One complete approved JSON summary required: {article}')
        return hits[0][:-1]

    request_en = section(request_md, '## 英文', '## 中文')
    final_en = section(final_md, '## 英文', '## 中文')
    require(visible_tokens(request_en) == visible_tokens(final_en),
            f'Markdown English prose changed: {article}')
    request_cn = section(request_md, '## 中文', '## 速查表')
    final_cn = section(final_md, '## 中文', '## 速查表')
    result = {'kind': 'unchanged_visible_Markdown_prose', 'article': article}
    if visible_tokens(request_cn, True) != visible_tokens(final_cn, True):
        require(request_cn.count(marker) == final_cn.count(marker) == 1,
                f'One embedded Markdown summary required: {article}')
        old_prefix, old_tail = request_cn.split(marker, 1)
        new_prefix, new_tail = final_cn.split(marker, 1)
        old_tail, new_tail = old_tail.strip(), new_tail.strip()
        require(old_tail.endswith('）') and new_tail.endswith('）'),
                f'Markdown summary must end its Chinese section: {article}')
        require(visible_tokens(old_prefix, True) == visible_tokens(new_prefix, True),
                f'Markdown Chinese body/note prose changed: {article}')
        requested = approved_summary(request_json)
        actual = approved_summary(final_json)
        expected = visible_tokens(requested, True)
        require(expected == visible_tokens(actual, True) ==
                visible_tokens(new_tail[:-1], True),
                f'Working MD summary is not the already requested JSON summary: {article}')
        result.update(kind='official_sync_of_already_requested_JSON_summary',
                      request_JSON_and_final_JSON_and_working_MD_summary_visible_exact=True,
                      all_other_Chinese_body_and_note_prose_visible_exact=True,
                      original_request_MD_retained_unmodified=True,
                      old_request_MD_summary=old_tail[:-1],
                      approved_JSON_summary=requested,
                      final_working_MD_summary=new_tail[:-1])
    require(visible_tokens(request_md.split('## 史实与来源', 1)[-1]) ==
            visible_tokens(final_md.split('## 史实与来源', 1)[-1]),
            f'Markdown facts changed: {article}')
    result['request_MD_sha256'] = hashlib.sha256(request_md.encode()).hexdigest()
    result['final_MD_sha256'] = hashlib.sha256(final_md.encode()).hexdigest()
    return result
