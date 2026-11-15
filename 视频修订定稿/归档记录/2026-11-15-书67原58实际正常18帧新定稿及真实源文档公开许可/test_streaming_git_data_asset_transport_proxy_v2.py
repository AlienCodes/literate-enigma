"""Offline contract tests; fixtures only, no sockets/Git repositories/media files."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import streaming_git_data_asset_transport_proxy_v2 as m

def blob(data,path=Path('offline.fixture')):
    return m.Blob(path,len(data),hashlib.sha256(data).hexdigest(),m.git_sha('blob',data),())

class ShortRead:
    def __init__(self,data):self.data=data;self.at=0;self.n=0
    def read(self,size):
        assert 0<size<=m.CHUNK
        choices=[1,2,5,19,m.CHUNK-1,71];n=min(size,choices[self.n%len(choices)]);self.n+=1
        x=self.data[self.at:self.at+n];self.at+=len(x);return x

class Response:
    def __init__(self,data,status=200,headers=None):self.f=io.BytesIO(data);self.status=status;self.headers=headers or {}
    def read(self,n=-1):return self.f.read(n)
    def getheader(self,k):return self.headers.get(k)

class Connection:
    def __init__(self,response):self.response=response;self.sent=[];self.headers={};self.closed=False
    def putrequest(self,*a,**kw):self.request_args=a
    def putheader(self,k,v):self.headers[k]=v
    def endheaders(self):pass
    def send(self,b):
        assert len(b)<=4*((m.CHUNK+2)//3)
        self.sent.append(b)
    def request(self,*a,**kw):self.request_args=a
    def getresponse(self):return self.response
    def close(self):self.closed=True

class BodyTests(unittest.TestCase):
    def test_zero_and_mod3_and_chunk_boundaries_with_short_reads(self):
        for n in [0,1,2,3,m.CHUNK-1,m.CHUNK,m.CHUNK+1,2*m.CHUNK+1]:
            data=bytes(range(256))*(n//256)+bytes(range(n%256));b=blob(data)
            for source in [io.BytesIO(data),ShortRead(data)]:
                pieces=list(m.encoded_body(source,b));actual=b''.join(pieces)
                self.assertEqual(actual,m.PREFIX+base64.b64encode(data)+m.SUFFIX)
                self.assertEqual(len(actual),m.content_length(n))
                self.assertEqual(base64.b64decode(json.loads(actual)['content']),data)
                self.assertLessEqual(max(map(len,pieces)),262144)
    def test_wrong_same_size_truncated_and_growing_inputs_never_close_JSON(self):
        original=b'\x00\xffbinary\r\n'*30000;b=blob(original)
        for data in [b'X'+original[1:],original[:-1],original+b'X']:
            sent=[]
            with self.assertRaises(m.GuardError):
                for p in m.encoded_body(ShortRead(data),b):sent.append(p)
            self.assertNotEqual(sent[-1],m.SUFFIX)
    def test_changed_inode_pin_stops_before_sending_body(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'source.fixture';p.write_bytes(b'old');b=m.inspect_blob(p,3,hashlib.sha256(b'old').hexdigest());p.write_bytes(b'new')
            with self.assertRaises(m.GuardError):list(m.validated_source_body(b))
    def test_content_length_rejects_invalid_or_above_supported_limit(self):
        for n in [-1,True,1.0,100000001]:
            with self.assertRaises(m.GuardError):m.content_length(n)

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'source.fixture';self.data=b'\x00\xff\x80abc'*40000;self.p.write_bytes(self.data);self.b=m.inspect_blob(self.p,len(self.data),hashlib.sha256(self.data).hexdigest())
    def tearDown(self):self.tmp.cleanup()
    def client(self,response):
        c=Connection(response);return m.GitDataClient('OFFLINE-SECRET',lambda:c),c
    def test_real_POST_serializer_and_headers_only_offline_connection(self):
        client,c=self.client(Response(json.dumps({'sha':self.b.git_sha}).encode(),201))
        client.post_blob('alienalgorithm/postgraduate-vocabulary',self.b)
        self.assertEqual(c.headers['Content-Length'],str(len(b''.join(c.sent))))
        self.assertEqual(len(b''.join(c.sent)),m.content_length(self.b.size));self.assertTrue(c.closed)
        self.assertEqual(base64.b64decode(json.loads(b''.join(c.sent))['content']),self.data)
    def test_POST_500_wrong_SHA_or_malformed_JSON_fail(self):
        for response in [Response(b'no',500),Response(b'{"sha":"wrong"}',201),Response(b'not-json',201)]:
            client,c=self.client(response)
            with self.assertRaises(m.GuardError):client.post_blob('AlienCodes/literate-enigma',self.b)
            self.assertTrue(c.closed)
    def test_real_raw_GET_exact_and_wrong_readbacks(self):
        client,c=self.client(Response(self.data,headers={'Content-Length':str(len(self.data))}));client.verify_blob('AlienCodes/literate-enigma',self.b);self.assertTrue(c.closed)
        for response in [Response(self.data[:-1]),Response(self.data+b'X'),Response(b'X'+self.data[1:]),Response(self.data,headers={'Content-Length':'1'}),Response(self.data,status=403),Response(self.data,headers={'Content-Encoding':'gzip'})]:
            client,c=self.client(response)
            with self.assertRaises(m.GuardError):client.verify_blob('AlienCodes/literate-enigma',self.b)
            self.assertTrue(c.closed)
    def test_api_error_does_not_leak_response_or_token(self):
        client,c=self.client(Response(b'OFFLINE-SECRET-with-server-details',422))
        with self.assertRaises(m.GuardError)as e:client.api('AlienCodes/literate-enigma','git/refs','POST',{})
        self.assertNotIn('SECRET',str(e.exception))

def git_hash(kind,data):return subprocess.check_output(['git','hash-object','-t',kind,'--stdin'],input=data).decode().strip()
def raw_entry(mode,name,sha):return mode.encode()+b' '+name.encode()+b'\0'+bytes.fromhex(sha)

class TreeTests(unittest.TestCase):
    def test_bottom_up_UTF8_and_directory_slash_sort_against_real_Git(self):
        values={p:m.git_sha('blob',p.encode())for p in ['a/b.txt','a.','a0','中文/页.json']}
        files=[{'repo_path':p,'git_blob_sha':sha}for p,sha in values.items()];trees,hashes=m.make_trees(files)
        a=git_hash('tree',raw_entry('100644','b.txt',values['a/b.txt']))
        cn=git_hash('tree',raw_entry('100644','页.json',values['中文/页.json']))
        root=git_hash('tree',b''.join([raw_entry('100644','a.',values['a.']),raw_entry('40000','a',a),raw_entry('100644','a0',values['a0']),raw_entry('40000','中文',cn)]))
        self.assertEqual(hashes,{'a':a,'中文':cn,'':root})
        self.assertEqual([x['path']for x in trees[-1]['tree']],['a.','a','a0','中文'])
    def test_unsafe_paths_duplicate_modes_and_file_directory_collisions(self):
        for path in ['/absolute','a//b','a/../b','a/./b','a/.git/b','a\nb','a\tb']:
            with self.assertRaises(m.GuardError):m.make_trees([{'repo_path':path,'git_blob_sha':'0'*40}])
        for entries in [[{'repo_path':'a','git_blob_sha':'0'*40}]*2,[{'repo_path':'a','git_blob_sha':'0'*40},{'repo_path':'a/b','git_blob_sha':'1'*40}],[{'repo_path':'a','git_blob_sha':'0'*40,'mode':'100755'}],[{'repo_path':'a','git_blob_sha':'bad'}]]:
            with self.assertRaises(m.GuardError):m.make_trees(entries)
    def test_deterministic_commit_matches_real_Git_and_timezone_fraction(self):
        c=m.commit_spec('0'*40,'2026-11-15T01:02:03.999+00:00');same=m.commit_spec('0'*40,'2026-11-14T20:02:03-05:00')
        self.assertEqual(c['sha'],same['sha']);self.assertEqual(c['sha'],git_hash('commit',c['raw']));self.assertEqual(c['data']['parents'],[])

def fixture_bundle():
    b=blob(b'offline');files=[{'repo_path':'视频修订定稿/测试/payload.fixture','bytes':b.size,'sha256':b.sha256,'git_blob_sha':b.git_sha}]
    trees,hashes=m.make_trees(files)
    return {'blobs':{b.git_sha:b},'files':files,'trees':trees,'hashes':hashes,'prefix':'视频修订定稿/测试','meta':{'asset_branch':'codex/passed4k-assets-123-58-hold18-postonly-v1'},'commit':m.commit_spec(hashes[''],'2026-11-15T01:02:03Z')}

class FakeGit:
    def __init__(self,bundle,fail=None):self.b=bundle;self.head=None;self.calls=[];self.fail=fail;self.posts=[]
    def post_blob(self,repo,b):
        self.calls.append('post_blob')
        if self.fail=='blob':raise m.GuardError('offline wrong POST SHA')
    def verify_blob(self,repo,b):
        self.calls.append('verify_blob')
        if self.fail=='raw':raise m.GuardError('offline wrong raw SHA')
    def api(self,repo,path,method='GET',data=None,allow404=False):
        self.calls.append((method,path))
        if method=='POST':self.posts.append(path)
        if path.startswith('git/ref/heads/'):
            return None if self.head is None else {'object':{'sha':self.head}}
        if path=='git/trees' and method=='POST':
            match=next(t for t in self.b['trees']if t['tree']==data['tree'])
            return {'sha':'f'*40 if self.fail=='tree' else match['sha']}
        if path=='git/commits' and method=='POST':return {'sha':'f'*40 if self.fail=='commit'else self.b['commit']['sha']}
        if path.startswith('git/trees/'):
            rows=[{'path':f['repo_path'],'mode':'100644','type':'blob','sha':f['git_blob_sha'],'size':f['bytes']}for f in self.b['files']]
            rows+=[{'path':p,'mode':'040000','type':'tree','sha':s}for p,s in self.b['hashes'].items()if p]
            if self.fail=='remote-tree':rows[0]['size']+=1
            return {'sha':self.b['hashes'][''],'truncated':False,'tree':rows}
        if path.startswith('git/commits/'):
            c=self.b['commit']['data'];result={'sha':self.b['commit']['sha'],'tree':{'sha':c['tree']},'parents':[],'message':c['message'],'author':dict(c['author']),'committer':dict(c['committer'])}
            if self.fail=='identity':result['author']['date']='wrong'
            if self.fail=='race':self.head='f'*40
            return result
        if path=='git/refs':
            assert self.head is None;self.head=data['sha']
            if self.fail=='ref-timeout':raise TimeoutError('offline connection lost after accepted ref')
            return {'object':{'sha':self.head}}
        raise AssertionError((path,method))

class ProgressionTests(unittest.TestCase):
    def test_changed_control_pin_blocks_before_any_network(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'control.json';p.write_text('{"frozen":1}');expected=m.sha256(p);p.write_text('{"frozen":2}')
            b=fixture_bundle();b['control_pins']=[(p,expected)];client=FakeGit(b)
            with self.assertRaises(m.GuardError):m.publish_repository(client,'AlienCodes/literate-enigma',b,lambda row:None)
            self.assertEqual(client.calls,[])
    def test_control_mutation_after_commit_verification_blocks_new_ref(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'control.json';p.write_text('{"frozen":1}');b=fixture_bundle();b['control_pins']=[(p,m.sha256(p))];client=FakeGit(b);original=client.api
            def api(*a,**kw):
                result=original(*a,**kw)
                if a[1].startswith('git/commits/'):p.write_text('{"frozen":2}')
                return result
            client.api=api
            with self.assertRaises(m.GuardError):m.publish_repository(client,'AlienCodes/literate-enigma',b,lambda row:None)
            self.assertNotIn('git/refs',client.posts)
    def test_all_failures_block_ref_and_no_READY_side_effect(self):
        for fail in ['blob','raw','tree','commit','remote-tree','identity','race']:
            b=fixture_bundle();client=FakeGit(b,fail)
            with self.assertRaises(m.GuardError):m.publish_repository(client,'alienalgorithm/postgraduate-vocabulary',b,lambda row:None)
            self.assertNotIn('git/refs',client.posts)
    def test_success_exact_existing_readonly_resume_and_conflicting_ref(self):
        b=fixture_bundle();client=FakeGit(b);r=m.publish_repository(client,'alienalgorithm/postgraduate-vocabulary',b,lambda row:None)
        self.assertEqual(r['asset_commit'],b['commit']['sha']);self.assertEqual(client.posts.count('git/refs'),1)
        client.posts=[];client.calls=[];m.publish_repository(client,'alienalgorithm/postgraduate-vocabulary',b,lambda row:None)
        self.assertEqual(client.posts,[]);self.assertNotIn('post_blob',client.calls)
        client.head='f'*40;client.posts=[]
        with self.assertRaises(m.GuardError):m.publish_repository(client,'AlienCodes/literate-enigma',b,lambda row:None)
        self.assertEqual(client.posts,[])
    def test_timeout_after_ref_create_not_success_then_exact_readonly_recovery(self):
        b=fixture_bundle();client=FakeGit(b,'ref-timeout')
        with self.assertRaises(TimeoutError):m.publish_repository(client,'AlienCodes/literate-enigma',b,lambda row:None)
        self.assertEqual(client.head,b['commit']['sha']);client.posts=[];client.fail=None
        r=m.publish_repository(client,'AlienCodes/literate-enigma',b,lambda row:None)
        self.assertEqual(client.posts,[]);self.assertTrue(r['all_blobs_raw_HTTP_readback_exact'])

class DiskAndGateTests(unittest.TestCase):
    def test_allocated_block_temp_and_directory_margin_budget_boundary(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);p=root/'new.json';owned={root};value={'small':'offline'};block=os.statvfs(root).f_frsize
            raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode();limit=m.allocated_budget(root,block)+((len(raw)+block-1)//block)*block+16*block
            with patch.object(m,'MAX_NEW_METADATA',limit-1):
                with self.assertRaises(m.GuardError):m.write_small(p,value,owned)
            self.assertFalse(p.exists())
            with patch.object(m,'MAX_NEW_METADATA',limit):m.write_small(p,value,owned)
            self.assertTrue(p.exists());self.assertFalse(p.with_name(p.name+'.stream-atomic.tmp').exists())
    def test_small_metadata_cap_and_existing_asset_never_overwritten(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'result.json';owned=set()
            with patch.object(m,'MAX_NEW_METADATA',100):
                with self.assertRaises(m.GuardError):m.write_small(p,{'too_big':'x'*100},owned)
            self.assertFalse(p.exists());self.assertEqual(list(Path(d).iterdir()),[])
            m.write_exact_asset(p,{'exact':1},owned);original=p.read_bytes()
            with self.assertRaises(m.GuardError):m.write_exact_asset(p,{'different':1},owned)
            self.assertEqual(p.read_bytes(),original)
    def test_prepare_bundle_is_local_only_and_wrong_approval_prevents_auth_network(self):
        with tempfile.TemporaryDirectory()as d:
            w=Path(d);prefix='视频修订定稿/离线测试';pay=w/'payload';(pay/prefix).mkdir(parents=True);data=b'offline synthetic not media';final=pay/prefix/'final.fixture';final.write_bytes(data)
            hsfile=w/'handoff.json';h={'status':'passed_actual_normal18_post_only_for_permanent_archive','kind':'actual-new-native-source-QA-then-authorized-normal18-local-tail','actual_new_source_QA_then_final_normal18_verified':True,'source_run':123,'production_delivery_eligible':True,'preview_only':False,'articles':[{'source_id':'58','new_id':'67','passed_per_article':True,'final_mp4':{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}}]};hsfile.write_text(json.dumps(h));hs=m.sha256(hsfile);(pay/prefix/'H.fixture').write_bytes(hsfile.read_bytes())
            row={'source_id':'58','new_id':'67','passed_per_article':True,'production_delivery_eligible':True,'preview_only':False,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'postprocessing_full_V3_handoff_sha256':hs,'video_repo_path':prefix+'/final.fixture'}
            meta={'created_utc':'2026-11-15T01:02:03Z','prefix':prefix,'asset_branch':'codex/passed4k-assets-123-58-hold18-postonly-v1','actual_handoff_sha256':hs,'articles':[row]};(w/'prepared-archive.json').write_text(json.dumps(meta))
            index=[{'repo_path':str(p.relative_to(pay)),'bytes':p.stat().st_size,'sha256':m.sha256(p)}for p in pay.rglob('*')if p.is_file()];(w/'payload-file-index.json').write_text(json.dumps(index));ps=m.sha256(w/'prepared-archive.json');ix=m.sha256(w/'payload-file-index.json')
            b=m.prepare_bundle(w,hsfile,hs,ps,ix);self.assertEqual(len(b['files']),2)
            approval=w/'wrong-approval.json';approval.write_text('{}')
            args=['transport','--execute','--work-dir',str(w),'--handoff',str(hsfile),'--handoff-sha256',hs,'--prepared-sha256',ps,'--index-sha256',ix,'--approval',str(approval)]
            with patch('sys.argv',args),patch.object(m.subprocess,'check_output',side_effect=AssertionError('auth/network forbidden')):
                with self.assertRaises(m.GuardError):m.main()
            self.assertFalse((w/'assets.git').exists());self.assertFalse(list(w.glob('streaming-attempt-*')))
            self.assertFalse(any(p.suffix in {'.mp4','.zip','.pack'}for p in w.rglob('*')))

class ProxyRouteTests(unittest.TestCase):
    def test_environment_CONNECT_direct_bypass_auth_and_unsupported_proxy(self):
        class Tunnel:
            def set_tunnel(self,*a,**kw):self.tunnel=(a,kw)
        tunnel=Tunnel()
        with patch.object(m.urllib.request,'getproxies',return_value={'https':'http://offline-proxy.example:8888'}),patch.object(m.urllib.request,'proxy_bypass',return_value=False),patch.object(m.http.client,'HTTPSConnection',return_value=tunnel)as ctor:
            self.assertIs(m.environment_https_connection(),tunnel);ctor.assert_called_once_with('offline-proxy.example',port=8888,timeout=90);self.assertEqual(tunnel.tunnel,(('api.github.com',443),{'headers':{}}))
        with patch.object(m.urllib.request,'getproxies',return_value={'https':'http://u%40ser:p%3Ass@offline-proxy.example:8888'}),patch.object(m.urllib.request,'proxy_bypass',return_value=False),patch.object(m.http.client,'HTTPSConnection',return_value=tunnel):
            m.environment_https_connection();self.assertEqual(tunnel.tunnel[1]['headers']['Proxy-Authorization'],'Basic '+base64.b64encode(b'u@ser:p:ss').decode())
        for proxy,bypass in [({},False),({'https':'http://offline-proxy.example'},True)]:
            with patch.object(m.urllib.request,'getproxies',return_value=proxy),patch.object(m.urllib.request,'proxy_bypass',return_value=bypass),patch.object(m.http.client,'HTTPSConnection',return_value=tunnel)as ctor:
                m.environment_https_connection();ctor.assert_called_once_with('api.github.com',timeout=90)
        with patch.object(m.urllib.request,'getproxies',return_value={'https':'https://offline-proxy.example'}),patch.object(m.urllib.request,'proxy_bypass',return_value=False),patch.object(m.http.client,'HTTPSConnection',side_effect=AssertionError('must reject before connection')):
            with self.assertRaises(m.GuardError):m.environment_https_connection()

if __name__=='__main__':unittest.main(verbosity=2)
