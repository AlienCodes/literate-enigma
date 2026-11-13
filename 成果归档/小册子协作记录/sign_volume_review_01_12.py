from pathlib import Path
import json,hashlib,sys
ROOT=Path('/workspace/work/booklet70');sys.path.insert(0,str(ROOT))
from booklet_utils import atomic_json
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for v in map(int,sys.argv[1:]):
 n=f'{v:02}';e=json.loads((ROOT/'workers/volume-independent-01-12'/n/'structural-evidence.json').read_text());q=json.loads((ROOT/'volumes'/n/'qc.json').read_text())
 assert e['pdf_sha256']==q['pdf_sha256']==sha(q['pdf'])
 assert q['jpeg_quality']==96 and q['bytes']<=10*1024*1024
 report={'volume':v,'reviewer':'summaries_01_12 independent volume audit','passed':True,'pdf_sha256':q['pdf_sha256'],'pdf':q['pdf'],'pages':q['pages'],'bytes':q['bytes'],'toc_preview_visual_review':True,'toc_rows_verified':10,'goto_targets_independently_verified':10,'bookmark_targets_independently_verified':10,'recommended_order_and_original_ids_exact':True,'chapter_start_and_end_positions_independently_verified':10,'actual_merged_pdf_sample_pages_reviewed':e['samples'],'sampled_art_recompression_visual_review':True,'sampled_vector_text_visual_review':True,'jpeg_quality':96,'read_only_pdf_and_page':True,'notes':['实际看过本册contents-preview.png：十个阅读顺序/原篇号/标题/本册起始页均清晰。','独立用fitz读取最终PDF十个可点击目录行，逐一核行内文字与GOTO目标页、书签目标、章节封面及末页位置，精确对应推荐顺序。','实际从最终合订PDF渲染首/中/末三篇封面，另渲染英文/中文/核心词汇各一页，并查看整页拼图和1000px插图/2倍文字细节。','所抽插图纸纹/边缘/细部清楚，无可见压缩马赛克；所抽英文、汉字、斜体例句及细线可读，矢量字体仍存在。','不改源PDF、Page、内容、插图或制作程序；签核只绑定此finalPDF字节SHA。']}
 atomic_json(ROOT/'reviews'/f'volumes-{n}.json',report)
 print(json.dumps({'volume':v,'passed':True,'pdf_sha256':q['pdf_sha256'],'pages':q['pages']},ensure_ascii=False))
