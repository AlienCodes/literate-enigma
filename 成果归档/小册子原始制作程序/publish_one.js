(async function publishOne(payload, parentPageId, previous = {}) {
  const n = payload.id;
  const path = '/workspace/work/booklet70/publication/' + n + '.json';
  if(previous.pdf_sha256 && (previous.pdf_sha256!==payload.pdf_sha256 || previous.content_sha256!==payload.content_sha256)) {
    throw Error('Existing published artifact differs; reconcile on the same Page before replacing '+n);
  }
  const journal = {...previous, id:n, content_sha256:payload.content_sha256, pdf_sha256:payload.pdf_sha256};
  async function command(args) {
    let r=await tools.exec_command(args);let output=r.output||'';
    while(r.session_id!==undefined && r.exit_code===undefined) {
      r=await tools.write_stdin({session_id:r.session_id,chars:'',yield_time_ms:1000,max_output_tokens:1000});
      output+=r.output||'';
    }
    return {...r,output};
  }
  async function persist() {
    const encoded = JSON.stringify(JSON.stringify(journal));
    const cmd = "python - <<'BOOKLET_JOURNAL'\nfrom pathlib import Path\nimport json\np=Path('"+path+"')\np.parent.mkdir(parents=True,exist_ok=True)\nd=json.loads("+encoded+")\nt=p.with_name(p.name+'.tmp')\nt.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\\n')\nt.replace(p)\nBOOKLET_JOURNAL";
    const r=await command({cmd,max_output_tokens:1000});
    if(r.exit_code!==0) throw Error('Cannot persist publication journal '+n+': '+r.output);
  }
  function structured(r,label) {
    const v=r.structuredContent;
    if(r.isError || !v || v.error) throw Error(label+': '+JSON.stringify(v??r));
    return v;
  }
  async function createSerialized(args) {
    // Child creation updates the common parent. Serialize this short step
    // across publishers; independent immutable file uploads stay parallel.
    const lock='/workspace/work/booklet70/publication/.page-create-lock';
    let acquired=false;
    for(let attempt=0;attempt<45;attempt++) {
      const claim=await command({cmd:"python - <<'CLAIM_PAGE_LOCK'\nimport os\np='"+lock+"'\ntry:\n os.mkdir(p); print('acquired')\nexcept FileExistsError: print('busy')\nCLAIM_PAGE_LOCK",max_output_tokens:100});
      if(claim.output.trim()==='acquired'){acquired=true;break;}
      await new Promise(resolve=>setTimeout(resolve,2000));
    }
    if(!acquired)throw Error('Page creation queue busy; resume unchanged journal '+n);
    try {
      structured(await tools.mcp__codex_apps__chatgpt_space_read_page({page_id:args.parent_page_id,include_content:false}),'refresh parent before child create');
      return await tools.mcp__codex_apps__chatgpt_space_create_page(args);
    } finally {
      await command({cmd:"rmdir '"+lock+"'",max_output_tokens:100});
    }
  }
  if(journal.status==='complete') return journal;
  if(!journal.page_id) {
    const cleanTitle=payload.title_zh.replace(/[：:，,！？?!《》]/g,' ').replace(/\s+/g,' ').trim();
    const result=structured(await createSerialized({
      title:'第'+n+'篇 '+cleanTitle+' 插图英语阅读小册',
      parent_page_id:parentPageId,
      idempotency_key:'illustrated-booklet70-20261113-article-'+n+'-v1',
      initial_blocks:['这份小册子的正式版为'+payload.pages+'页PDF。下方预览直接取自同一份PDF；下载请使用附件链接。页面菜单中的导出会另外排版整个网页。']
    }),'create Page');
    journal.page_id=result.content.page_id;journal.url=result.metadata.url;journal.title=result.content.title;journal.status='created';
    await persist();
  }
  if(!journal.pdf_attachment) {
    const uploaded=structured(await tools.mcp__codex_apps__chatgpt_space_write_page_reference({
      page_id:journal.page_id,file:payload.pdf,title:'下载第'+n+'篇正式PDF '+payload.pages+'页'
    }),'upload PDF');
    if(!uploaded.file_access_confirmed||uploaded.sha256!==payload.pdf_sha256||!uploaded.markdown)throw Error('PDF access/hash failed '+n);
    journal.pdf_attachment=uploaded;await persist();
  }
  journal.previews=journal.previews||[];
  const pending=payload.preview_pages.filter(p=>!journal.previews.some(x=>x.page===p.page&&x.sha256===p.sha256));
  // File uploads create separate immutable assets and do not edit Page blocks.
  for(let start=0;start<pending.length;start+=3) {
    const group=pending.slice(start,start+3);
    const results=await Promise.allSettled(group.map(async p=>{
      const v=structured(await tools.mcp__codex_apps__chatgpt_space_write_page_reference({
        page_id:journal.page_id,file:p.path,title:'第'+p.page+'页 '+payload.title_zh+' PDF实页'
      }),'upload preview '+p.page);
      if(!v.file_access_confirmed||v.sha256!==p.sha256||!v.markdown)throw Error('Preview hash/access failed '+p.page);
      return {page:p.page,...v};
    }));
    for(let i=0;i<results.length;i++) {
      const r=results[i];if(r.status==='fulfilled')journal.previews.push(r.value);
      else {journal.upload_error=String(r.reason);}
    }
    await persist();
    if(results.some(r=>r.status==='rejected'))throw Error(journal.upload_error);
  }
  const read=structured(await tools.mcp__codex_apps__chatgpt_space_read_page({page_id:journal.page_id}),'read Page');
  const blocks=read.content.blocks;
  const already=blocks.some(b=>b.markdown===journal.pdf_attachment.markdown);
  if(!already) {
    const units=[journal.pdf_attachment.markdown,'# 正式小册子逐页预览'];
    for(const v of journal.previews.sort((a,b)=>a.page-b.page)){units.push('## 第'+v.page+'页');units.push(v.markdown);}
    const last=blocks[blocks.length-1];
    const args={page_id:read.content.page_id,operations:[{op:'insert_markdown',
      at:{kind:'between_blocks',preceding_block_id:last?last.id:null,following_block_id:null},block_units:units}]};
    if(read.metadata?.stream_kind)args.stream_kind=read.metadata.stream_kind;
    if(read.content.through_sequence!==undefined)args.base_sequence=read.content.through_sequence;
    const edit=structured(await tools.mcp__codex_apps__chatgpt_space_edit_page(args),'save Page preview');
    if(edit.operation_results?.some(x=>x.status==='rejected'||x.ignored_reason))throw Error('Preview edit not fully applied');
    journal.edit_sequence=edit.through_sequence;await persist();
  }
  const verify=structured(await tools.mcp__codex_apps__chatgpt_space_read_page({page_id:journal.page_id}),'verify Page');
  const saved=verify.content.blocks;
  if(!saved.some(b=>b.markdown===journal.pdf_attachment.markdown))throw Error('Saved PDF link missing');
  for(const p of journal.previews){if(!saved.some(b=>b.markdown===p.markdown))throw Error('Saved preview missing '+p.page);}
  if(saved.filter(b=>/^!\[/.test(b.markdown)).length!==payload.pages)throw Error('Wrong preview page count');
  journal.pages=payload.pages;journal.status='complete';journal.user_preview_matches_download=true;delete journal.upload_error;
  await persist();return journal;
})
