"""Only user143 source40 video illustration overlay; shared book/PDF declarations stay historical."""
import json,copy,hashlib,tempfile
from pathlib import Path
P=json.loads(Path(__file__).with_name('exact40-video143-overlay-reference.json').read_text())
def require(x,m):
 if not x:raise ValueError(m)
def checked(x):
 p=Path(x['path']);require(p.stat().st_size==x['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],'Actual143 declared file differs');return p
def metadata(new,old,crop,oldcrop):
 nr={x['source_id']:x for x in new['illustrations']};orr={x['source_id']:x for x in old['illustrations']};cr={x['source_id']:x for x in crop['articles']};oc={x['source_id']:x for x in oldcrop['articles']}
 require(len(nr)==len(orr)==len(cr)==len(oc)==70 and set(nr)==set(orr)==set(cr)==set(oc),'Actual143 overlay mapping incomplete')
 require(all(nr[k]==orr[k]and cr[k]==oc[k]for k in nr if k!='40'),'Any other69 artwork/crop changed')
 row=nr['40'];choice=cr['40'];require(row['new_id']=='46'and row['sha256']==P['native_image']['sha256']=='c620a3ca7f8df9985f1d7f89e055f5f33be34f67cbcc7c07fc95dd4045df585e'and row['bytes']==2920299 and row['video_only_user143_revised_asset']is True and row['shared_original_book_and_PDF_unchanged']is True and row['original_shared_book_illustration_sha256']==orr['40']['sha256']=='5b1aabe5efdc4543a1989bfac2dd27a8e1f3dbd0f5db232f32c5800ef9e496e1'and row['exact_user143_authority_sha256']==P['authority143']['sha256'],'Only exact143 new video art may replace the old source40 book image')
 require(choice['source_image_sha256']==row['sha256']and choice['new_id']=='46'and choice['mode']=='cover'and choice['source_crop_box']==[0,160,1536,1024]and choice['actually_visually_reviewed']is True and choice['review_state']=='approved_composition'and choice['actual_16by9_crop_preview_actually_viewed']is True,'Only actual reviewed143 composition')
 require(crop['illustration_manifest_sha256']==P['new_manifest']['sha256'],'Actual143 crop/manifest identity differs');return row,choice

def verify(prior,raw,current):
 for x in P.values():checked(x)
 new=json.loads(checked(P['new_manifest']).read_text());old=json.loads(checked(P['original_producer_manifest']).read_text());crop=json.loads(checked(P['new_crop']).read_text());oldcrop=json.loads(checked(P['original_producer_crop']).read_text());row,choice=metadata(new,old,crop,oldcrop)
 require(raw['article']=='40'and raw['book_new_id']=='46'and raw['approved_illustration_sha256']==row['sha256'],'Actual144 final uses another image')
 with tempfile.TemporaryDirectory(prefix='source40-exact143-compose-')as t:
  out=Path(t)/'prepared.png';current.compose_illustration(checked(P['native_image']),choice,out);png=current.sha(out);rgb=current.rgb_sha(out)
 require(png==raw['illustration_preparation']['prepared_png_sha256']and rgb==raw['illustration_preparation']['prepared_rgb_sha256']==raw['illustration_composed_4k_rgb_sha256'],'Independent actual143 composition pixel identity differs')
 overlay=dict(kind='exact-user143-source40-approved-video-only-illustration-replacement',**P,prepared_png_sha256=png,prepared_rgb_sha256=rgb,all_other69_images_and_crops_exact=True,shared_book_original_and_PDF_unchanged=True,temporary_independent_composition_recomputed_and_byte_RGB_equal=True)
 return row,overlay

def current_illustration(old,raw,overlay):
 r=copy.deepcopy(old);r.update(path=raw['illustration_preparation']['prepared_image_path'],bytes=Path(raw['illustration_preparation']['prepared_image_path']).stat().st_size,sha256=raw['illustration_preparation']['prepared_png_sha256'],native_source=P['native_image'],historical_original_shared_book_native_source=old.get('native_source'),approved_video_illustration_source_sha256=P['native_image']['sha256'],video_only_user143_replacement=True,video_illustration_authority=overlay,book_source_sha256='5b1aabe5efdc4543a1989bfac2dd27a8e1f3dbd0f5db232f32c5800ef9e496e1')
 return r
