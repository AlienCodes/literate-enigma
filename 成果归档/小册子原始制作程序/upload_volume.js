(async function uploadVolume(volume, pageId, previous={}) {
  const n=String(volume.volume).padStart(2,'0');
  const path='/workspace/work/booklet70/publication/volume-'+n+'.json';
  if(previous.pdf_sha256 && previous.pdf_sha256!==volume.pdf_sha256)throw Error('Volume changed after upload '+n);
  const j={...previous,volume:volume.volume,pdf_sha256:volume.pdf_sha256,pages:volume.pages};
  function data(r){const x=r.structuredContent;if(r.isError||!x||x.error)throw Error(JSON.stringify(x));return x;}
  async function save(){const cmd="python - <<'SAVE_VOLUME'\nimport json\nfrom pathlib import Path\np=Path('"+path+"')\nd=json.loads("+JSON.stringify(JSON.stringify(j))+")\np.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\\n')\nSAVE_VOLUME";const x=await tools.exec_command({cmd,max_output_tokens:500});if(x.exit_code!==0)throw Error(x.output);}
  if(!j.pdf_attachment){const a=data(await tools.mcp__codex_apps__chatgpt_space_write_page_reference({page_id:pageId,file:volume.pdf,title:'下载第'+volume.volume+'册合订PDF '+volume.pages+'页'}));if(!a.file_access_confirmed||a.sha256!==volume.pdf_sha256||!a.markdown)throw Error('Volume PDF verification failed');j.pdf_attachment=a;await save();}
  if(!j.contents_preview){const a=data(await tools.mcp__codex_apps__chatgpt_space_write_page_reference({page_id:pageId,file:volume.preview,title:'第'+volume.volume+'册 目录实页预览'}));if(!a.file_access_confirmed||a.sha256!==volume.preview_sha256||!a.markdown)throw Error('Volume contents verification failed');j.contents_preview=a;await save();}
  j.status='assets_ready';await save();return j;
})
