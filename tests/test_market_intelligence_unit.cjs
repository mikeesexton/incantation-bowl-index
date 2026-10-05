const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

function render(rows, candidates = []) {
  const elements = Object.fromEntries(['house','platform','relevance','from','to','flags','unknown'].map(k => [k, {value:'',checked:false}]));
  const handlers = {};
  const form = {elements,addEventListener:(name,fn) => {handlers[name]=fn;}};
  const body = {}, count = {}, children = [];
  const container = {innerHTML:'',querySelector:selector => ({form,tbody:body,'.intelligence-count':count}[selector]),appendChild:child=>children.push(child)};
  const context = vm.createContext({window:{},document:{addEventListener:()=>{},createElement:()=>({})}});
  vm.runInContext(fs.readFileSync('web/market_intelligence.js','utf8'), context);
  context.window.MarketIntelligence.mount(container,{listings:rows,processed:{abc:{}},counts:{relevant:1},reappearance_candidates:candidates});
  return {container,body,count,elements,update:handlers.change,children};
}

test('source wording is escaped in listing, evidence, history and match disclosure',()=>{
  const attack='<img src=x onerror="steal()">';
  const r=render([{listing_id:'A',url:'https://example.org/lot/1',title:attack,full_description:attack,
    corpus_matches:[{object_id:'IBI-1',basis:attack,score:.8}],
    evidence:[{kind:'email',sha256:'a'.repeat(64),locator:attack}],
    history:[{changed:true,previous:{title:'old'},current:{title:attack},observed_at:'2026-10-05'}]}]);
  assert.doesNotMatch(r.body.innerHTML,/<img/);
  assert.match(r.body.innerHTML,/&lt;img/);
  assert.match(r.body.innerHTML,/Corpus links to discuss in chat/);
});

test('unknown sale dates are excluded from date ranges and missing results filter retains gaps',()=>{
  const r=render([{url:'https://example.org/lot/1',title:'Unknown date',market_status:'unknown'},
    {url:'https://example.org/lot/2',title:'Dated sold lot',sale_at:'2026-10-05T12:00:00Z',market_status:'sold'}]);
  r.elements.from.value='2026-10-01';r.update();
  assert.match(r.count.textContent,/1 of 2/);
  assert.doesNotMatch(r.body.innerHTML,/Unknown date/);
  r.elements.from.value='';r.elements.unknown.value='missing';r.update();
  assert.match(r.body.innerHTML,/Unknown date/);
  assert.doesNotMatch(r.body.innerHTML,/Dated sold lot/);
});

test('possible reappearances appear as explained pending review with escaped titles',()=>{
  const r=render([{listing_id:'A',title:'<one>',url:'https://example.org/1'},{listing_id:'B',title:'two',url:'https://example.org/2'}],
    [{listing_ids:['A','B'],score:.45,basis:['image dHash distance 0']}]);
  assert.match(r.children[0].innerHTML,/morning chat/);
  assert.match(r.children[0].innerHTML,/&lt;one&gt; ↔ two/);
  assert.match(r.children[0].innerHTML,/not probabilities/);
});

test('clear dropdown filters only change displayed rows and source checks do not approve matches',()=>{
  const r=render([{listing_id:'A',title:'Flagged',url:'https://example.org/1',provenance_flags:[{flag:'no_provenance_stated'}],
    source_check:{status:'checked',note:'Compared source wording',checked_at:'2026-10-05T12:00:00Z'},corpus_matches:[{object_id:'IBI',basis:'stock number',score:1}]},
    {listing_id:'B',title:'Unflagged',url:'https://example.org/2'}]);
  assert.doesNotMatch(r.container.innerHTML,/type="checkbox"/);
  assert.match(r.container.innerHTML,/With provenance flags/);
  assert.match(r.container.innerHTML,/they do not mark anything checked or approved/);
  r.elements.flags.value='flagged';r.update();
  assert.match(r.body.innerHTML,/Source compared/);
  assert.match(r.body.innerHTML,/Corpus links to discuss in chat/);
  assert.doesNotMatch(r.body.innerHTML,/Unflagged/);
  assert.match(r.count.textContent,/1 of 2/);
});

test('repeated evidence is compacted in display while complete history remains available',()=>{
  const evidence={kind:'email',sha256:'a'.repeat(64),locator:'link 1',message_id:'abc'};
  const r=render([{title:'Bowl',url:'https://example.org/1',evidence:[evidence,{...evidence}],
    history:[{changed:true,new:true,observed_at:'2026-10-05',previous:null,current:{title:'Bowl'}}]}]);
  assert.match(r.body.innerHTML,/Source evidence \(1\)/);
  assert.match(r.body.innerHTML,/Observation history/);
  assert.match(r.body.innerHTML,/first observation/);
});
