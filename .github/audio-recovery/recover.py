import io,json,os,pathlib,urllib.request,urllib.error,zipfile
repo='AlienCodes/literate-enigma'
run_id=43309565191
token=os.environ['GITHUB_TOKEN']
def api(path):
    req=urllib.request.Request('https://api.github.com/repos/'+repo+path,
            headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(req))
data=api('/actions/runs/'+str(run_id)+'/artifacts')
artifact=next(x for x in data['artifacts'] if x['name']=='local-repair-QC-text-only')
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args):return None
req=urllib.request.Request(artifact['archive_download_url'],headers={'Authorization':'Bearer '+token})
try:
    response=urllib.request.build_opener(NoRedirect).open(req)
    raw=response.read()
except urllib.error.HTTPError as exc:
    if exc.code!=302:raise
    raw=urllib.request.urlopen(exc.headers['Location']).read()
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    candidates=[(n,json.loads(z.read(n))) for n in z.namelist() if n.endswith('70-audio-audit.json')]
    matches=[(n,j) for n,j in candidates if j.get('original_audio_preserved') is False]
    assert len(matches)==1,[(n,j.get('original_audio_preserved')) for n,j in candidates]
    name,report=matches[0]
out=pathlib.Path('音频专项修复/67-70_20261112/70')
out.mkdir(parents=True,exist_ok=True)
(out/'70-after-audio-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'recovered_from':name,'failures':report['failures'],'health':report['current_audio_health'],'within':report['current_within_sentence_loudness'],'summary':report['canonical_mp4_loudness_check'],'preservation':report['preservation_failures']},ensure_ascii=False))
