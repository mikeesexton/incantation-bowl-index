const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('web/reading.js','utf8');
const context = vm.createContext({data:{manifest:{access_tier:'private_research'}},
  privateResearch:()=>context.data.manifest.access_tier==='private_research',
  esc:value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]))});
vm.runInContext(source.slice(source.indexOf('  function contextPassages('),
                            source.indexOf('  function renderContexts('))+'\nglobalThis.passages=contextPassages;',context);
const rows=[{id:'CTX1',reference:'DC29',kind:'provided_transcription',script:'Hebrew',editor:'Ford',
  content:'אבג\nשמר',locator:'page39',notes:'Tentative <script>bad</script>',citation:'Ford 2002',
  source_url:'./captures/CAP-TEST.pdf#page=9',editorial_annotations:[{substring:'word',annotation:'not applied'}]},
  {id:'CTX2',reference:'Ginza',kind:'provided_translation',editor:'Ford',content:'primeval radiance',locator:'page46'}];
test('source passages search all content and preserve right-to-left rows',()=>{
  const result=context.passages(rows,'אבג');assert.match(result,/1 of 2 passages/);
  assert.match(result,/dir="rtl"/);assert.match(result,/אבג<br>שמר/);assert.doesNotMatch(result,/primeval radiance/);
  assert.match(context.passages(rows,'Ginza radiance'),/1 of 2 passages/);
});
test('source notes are escaped and deletion metadata is visible',()=>{
  const result=context.passages(rows,'');assert.match(result,/&lt;script&gt;bad&lt;\/script&gt;/);
  assert.doesNotMatch(result,/<script>/);assert.match(result,/word: not applied/);
  assert.match(result,/CAP-TEST\.pdf#page=9/);
});
test('search joins word pieces around printed anchors without altering the copy',()=>{
  const split=[{...rows[0],content:'אב(360)גד'}];
  const result=context.passages(split,'אבגד');assert.match(result,/1 of 1 passages/);
  assert.match(result,/אב\(360\)גד/);
});
test('shared and public surfaces cannot render private source passages',()=>{
  context.data.manifest.access_tier='reviewed_release';assert.equal(context.passages(rows,''),'');
  context.data.manifest.access_tier='private_research';
});
test('loader fetches source contexts only for Mike private tier',async()=>{
  for(const tier of ['reviewed_release','private_research']){
    const requests=[];
    const loader=vm.createContext({window:{},fetch:async url=>{
      requests.push(url);return {ok:true,json:async()=>url.endsWith('/manifest')
        ? {access_tier:tier,source_contexts_url:'/private-contexts'}
        : {rows:url==='/private-contexts'?[{content:'Private contextual quotation'}]:[]}};
    }});
    vm.runInContext(source.slice(source.indexOf('const READER'),source.indexOf('const factsOf'))+
      '\nglobalThis.loadContexts=load;',loader);
    const data=await loader.loadContexts();
    assert.equal(requests.includes('/private-contexts'),tier==='private_research');
    assert.equal(data.sourceContexts.length,tier==='private_research'?1:0);
  }
});
