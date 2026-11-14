"""Exact two approved existing-body H kinds; no QA or media alteration."""
import hashlib,json
from pathlib import Path
CASES={
 '29':{'book':'39','authority':'110','run':43532011110,'handoff_sha256':'76eaf13c24eda655cf897ebeb19c5a22ecf80bfa1e5a8578492c9e9a033b34d5','user_sha256':'642c51f18fc3421823bd53dc4d9549b3ccd10609806972dc865a40dd88d0b2fc','final_sha256':'b26c43e7dfef10cd17a068d36a0cdd24e58d522a15d75e6595b73b14f914e244','final_bytes':16699167,'prior_handoff_sha256':'5182f5abb510246822e7267dd7cc463960396220c324d9e55e29372e11a159c9'},
 '31':{'book':'44','authority':'134','run':43533004625,'handoff_sha256':'fbdda3d52e0b366630248eedb961720ba8ba33f20f37719c9d4f035072476c94','user_sha256':'19458a5fe4ba5dfdb3908c2708cb3859870b6cc44914725f17478071181f661c','final_sha256':'c6cc2bbfb224338bfb64a4f753e065d072ece9c2a022e17a453ebfe515ae64f9','final_bytes':15958705,'prior_handoff_sha256':'9a461a42861364201f3b8b7eedb61522b2dfceebf46287299f33ad32fed730a9'},
}
def check(h,sha):
 assert len(h['articles'])==1;a=h['articles'][0];sid=a['source_id'];c=CASES[sid]
 assert sha==c['handoff_sha256']and h['kind']==f"authorized-existing-full-V3-source{sid}-user{c['authority']}-normal18-tail-only"
 assert h['status']=='passed_actual_normal18_post_only_for_permanent_archive'and a['passed_per_article']is True
 assert h['source_run']==c['run']and a['new_id']==c['book']
 assert h['local_postprocessing_only']is True and h['new_native_job_or_TTS_claimed']is False and h['source_and_voice_generation_rerun']is False
 assert h['production_delivery_eligible']is True and h['preview_only']is False
 assert h['actual_current_final_normal18_verified']is True and h['fresh_original_helper_full_JSON_and_GENDigest_exact']is True
 assert h['specific_authorization_id']==c['authority']and h['specific_authorization']['sha256']==c['user_sha256']and h['inherited_full_V3']['sha256']==c['prior_handoff_sha256']
 assert a['final_mp4']['bytes']==c['final_bytes']and a['final_mp4']['sha256']==c['final_sha256']
 u=h['specific_authorization'];raw=Path(u['path']).read_bytes();assert len(raw)==u['bytes']and hashlib.sha256(raw).hexdigest()==c['user_sha256'];user=json.loads(raw);assert user['author']=='user'and user['source_id']==sid and user['book_order']==c['book']
 return True
