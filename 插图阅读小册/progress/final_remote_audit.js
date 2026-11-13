(async function auditRemote(input, state, expected, deferIds = []) {
  const reportPath = '/workspace/work/booklet70/publication/final-remote-audit.json';
  state = state || {};
  const readyById = new Map(input.ready.map(j => [j.id, j]));
  function fingerprint(j) {
    return JSON.stringify([j.page_id,j.title,j.pdf_sha256,j.content_sha256,j.pdf_markdown,j.previews.map(p=>p.markdown)]);
  }
  function structured(r, label) {
    if (r.isError || !r.structuredContent || r.structuredContent.error) throw Error(label+': '+JSON.stringify(r.structuredContent??r));
    return r.structuredContent;
  }
  async function readWithRetry(j) {
    let r = await tools.mcp__codex_apps__chatgpt_space_read_page({page_id:j.page_id});
    if(r.structuredContent?.error?.retryable)r=await tools.mcp__codex_apps__chatgpt_space_read_page({page_id:j.page_id});
    return structured(r,'read '+j.id);
  }
  async function inspect(j) {
    const v=await readWithRetry(j), blocks=v.content.blocks, m=v.metadata;
    const images=blocks.filter(b=>/^!\[/.test(b.markdown));
    const pdfCount=blocks.filter(b=>b.markdown===j.pdf_markdown).length;
    const nativeFileLinks=blocks.filter(b=>/^\[[^\]]*\]\((?:library-file|project-file):[^)]+\)$/.test(b.markdown));
    const imageSequenceMatches=images.length===j.previews.length&&images.every((b,i)=>b.markdown===j.previews[i].markdown);
    const imageOccurrenceCounts=j.previews.map(p=>blocks.filter(b=>b.markdown===p.markdown).length);
    const headingPages=images.map(b=>{
      const index=blocks.indexOf(b);
      for(let k=index-1;k>=0;k--){
        const match=/^## 第(\d+)页(?:\s|$)/.exec(blocks[k].markdown);
        if(match)return Number(match[1]);
        if(/^#/.test(blocks[k].markdown))break;
      }
      return null;
    });
    const headingOrderMatches=headingPages.every((p,i)=>p===i+1);
    let s=structured(await tools.mcp__codex_apps__chatgpt_space_get_page_sharing({page_id:v.content.page_id}),'sharing '+j.id);
    let ownerOnly=false, ownerId=s.owner?.principal_id??s.page_owner?.principal_id??null;
    let sharingEvidence;
    if(s.scope==='page_owner'&&s.sharing_available===false){
      ownerOnly=s.owner_only===true;
      sharingEvidence={scope:s.scope,owner_only_observed:s.owner_only??null,owner_id:ownerId,roster_available:false};
    } else {
      const inherited=['inherited_access','inherited_access_summary','inherited_workspace_link_access'].map(k=>s[k]);
      ownerOnly=ownerId===expected.creator_id&&Array.isArray(s.shares)&&s.shares.length===0&&s.next_cursor===null&&inherited.every(x=>x?.complete===true&&Array.isArray(x.sources)&&x.sources.length===0)&&s.workspace_id===null&&s.space_id===null;
      sharingEvidence={scope:s.scope,owner_id:ownerId,share_count:s.shares?.length??null,roster_complete:s.next_cursor===null,inherited_snapshots_complete:inherited.every(x=>x?.complete===true),inherited_source_count:inherited.reduce((a,x)=>a+(x?.sources?.length??0),0),roster_available:true};
    }
    const checks={
      local_payload_manifest_and_upload_hashes_match:j.local_checks_passed===true,
      page_id_matches:v.content.page_id===j.page_id,
      url_matches:m.url===j.url,
      title_matches:m.title===j.title&&v.content.title===j.title,
      formal_pdf_markdown_exactly_once:pdfCount===1,
      sole_native_file_link_is_formal_pdf:nativeFileLinks.length===1&&nativeFileLinks[0].markdown===j.pdf_markdown,
      expected_preview_count:images.length===j.pages,
      each_expected_preview_exactly_once:imageOccurrenceCounts.every(n=>n===1),
      preview_sequence_matches_manifest:imageSequenceMatches,
      preview_heading_numbers_ordered:headingOrderMatches,
      pdf_link_precedes_previews:blocks.findIndex(b=>b.markdown===j.pdf_markdown)<blocks.indexOf(images[0]),
      personal_drive:m.drive_scope==='personal',
      creator_is_current_user:m.creator_account_user_id===expected.creator_id,
      parent_correct:j.id==='01'?m.parent===null:m.parent?.page_id===expected.parent_page_id,
      owner_only:ownerOnly,
      sharing_owner_is_current_user:ownerId===null?s.scope==='page_owner'&&s.owner_only===true:ownerId===expected.creator_id
    };
    const failures=Object.entries(checks).filter(([k,val])=>val!==true).map(([k])=>k);
    return {id:j.id,url:j.url,page_id:j.page_id,title:m.title,pages:j.pages,pdf_sha256:j.pdf_sha256,content_sha256:j.content_sha256,journal_sha256:j.journal_sha256,checked_at:new Date().toISOString(),passed:failures.length===0,status:failures.length===0?'passed':'failed',checks,failures,pdf_markdown_count:pdfCount,native_file_link_count:nativeFileLinks.length,preview_image_count:images.length,preview_heading_pages:headingPages,creator_account_user_id:m.creator_account_user_id,drive_scope:m.drive_scope,parent_page_id:m.parent?.page_id??null,sharing:sharingEvidence,approved_01_appendix_allowed:j.id==='01',_fingerprint:fingerprint(j)};
  }
  async function persist() {
    const pages=[];
    for(let n=1;n<=70;n++){
      const id=String(n).padStart(2,'0'),j=readyById.get(id),old=state[id];
      if(deferIds.includes(id)){pages.push({id,url:j?.url??old?.url??null,status:'pending',passed:false,reason:'root final title/navigation update pending'});continue;}
      if(j&&old?._fingerprint===fingerprint(j)){const copy={...old};delete copy._fingerprint;pages.push(copy);}
      else{const pending=input.pending.find(x=>x.id===id);const fail=input.local_failures.find(x=>x.id===id);pages.push({id,url:j?.url??null,status:fail?'failed':'pending',passed:false,reason:fail?.error??pending?.reason??'remote check pending'});}
    }
    const report={audit:'Independent final remote Pages acceptance',checked_at:new Date().toISOString(),status:pages.every(p=>p.passed)&&input.known_page_ids_unique?'complete':'in_progress',expected_articles:70,passed_count:pages.filter(p=>p.passed).length,pending_ids:pages.filter(p=>p.status==='pending').map(p=>p.id),failed_ids:pages.filter(p=>p.status==='failed').map(p=>p.id),page_ids_unique:input.known_page_ids_unique,duplicate_page_ids:input.duplicate_page_ids,formal_pdf_links_verified:pages.reduce((n,p)=>n+(p.passed?p.pdf_markdown_count:0),0),preview_image_links_verified:pages.reduce((n,p)=>n+(p.passed?p.preview_image_count:0),0),expected_creator_account_user_id:expected.creator_id,expected_parent_page_id:expected.parent_page_id,read_only:true,page_or_sharing_mutations:0,scope:'Current local payload, manifest and uploaded file digests plus actual remote Page blocks, identity, creator and sharing snapshots. Browser rendering is not independently claimed.',pages};
    const stage=reportPath+'.'+Date.now()+'-'+Math.floor(Math.random()*1e9)+'.tmp';
    const body=JSON.stringify(report,null,2)+'\n';
    await tools.apply_patch('*** Begin Patch\n*** Add File: '+stage+'\n+'+body.trimEnd().split('\n').join('\n+')+'\n*** End Patch');
    const cmd="python - <<'FINAL_REMOTE_AUDIT'\nimport os\nos.replace('"+stage+"','"+reportPath+"')\nFINAL_REMOTE_AUDIT";
    const r=await tools.exec_command({cmd,max_output_tokens:1000});if(r.exit_code!==0)throw Error('Cannot save audit report: '+r.output);
    store('booklet70_final_remote_state',state);store('booklet70_final_remote_report',report);
    return report;
  }
  const todo=input.ready.filter(j=>!deferIds.includes(j.id)&&(!state[j.id]?.passed||state[j.id]?._fingerprint!==fingerprint(j)));
  for(let i=0;i<todo.length;i+=2){
    const batch=todo.slice(i,i+2),results=await Promise.allSettled(batch.map(inspect));
    for(let k=0;k<results.length;k++){
      const r=results[k],j=batch[k];
      if(r.status==='fulfilled')state[j.id]=r.value;
      else state[j.id]={id:j.id,url:j.url,page_id:j.page_id,status:'failed',passed:false,failures:[String(r.reason)],_fingerprint:fingerprint(j)};
    }
    if((i+2)%10===0||i+2>=todo.length){const p=await persist();notify({remote_audit_progress:p.passed_count,pending:p.pending_ids,failed:p.failed_ids});}
  }
  return await persist();
})
