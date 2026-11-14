#!/usr/bin/env python3
"""Read-only validation of one real article section; never a partial Release."""
import argparse, json
from pathlib import Path
import delivery as D
from release_contract import book_illustrations

def validate_section(config, article):
    _,order,old,reorder=D.mapping(config)
    images=book_illustrations(D.load(D.checked_file(config['book_illustrations'])),order['rows'])
    compositions=D.load(D.checked_file(config['illustration_composition_review']))
    crops=D.load(D.checked_file(config['illustration_crop_review']))
    D.require(compositions['passed']is True and compositions['actual70_compositions_reviewed']is True and compositions['count']==crops['count']==70,'Actual reviewed70 illustration compositions required')
    D.require(compositions['crop_review_sha256']==config['illustration_crop_review']['sha256'],'Reviewed crop source changed')
    if 'published_pdf'in config:
        D.require(config['published_pdf']['illustrations_manifest']['sha256']==config['book_illustrations']['sha256'],'Article book map differs from frozen PDF owner map')
    items=[row for row in config['articles']if row['id']==article];D.require(len(items)==1,'Select one actual article section')
    return D.validate_article(config,items[0],old,reorder,images,{r['source_id']:r for r in compositions['articles']},{r['source_id']:r for r in crops['articles']},set(config.get('audio_changed_articles',['10','12','51'])))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('input');parser.add_argument('article');parser.add_argument('--output',required=True);args=parser.parse_args()
    record=validate_section(D.load(args.input),args.article.zfill(2));D.write(args.output,{'status':'passed_actual_article_section_only','complete70_release_validated':False,'publishing_or_remote_mutation_executed':False,'record':record})
    print(json.dumps({'article':record['id'],'new_id':record['new_id'],'status':'passed_actual_article_section_only','sha256':record['sha256'],'output':str(Path(args.output).resolve())},ensure_ascii=False))
