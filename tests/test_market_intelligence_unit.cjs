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
  assert.match(r.body.innerHTML,/Matches awaiting Mike/);
});

test('unknown sale dates are excluded from date ranges and missing results filter retains gaps',()=>{
  const r=render([{url:'https://example.org/lot/1',title:'Unknown date',market_status:'unknown'},
    {url:'https://example.org/lot/2',title:'Dated sold lot',sale_at:'2026-10-05T12:00:00Z',market_status:'sold'}]);
  r.elements.from.value='2026-10-01';r.update();
  assert.match(r.count.textContent,/1 of 2/);
  assert.doesNotMatch(r.body.innerHTML,/Unknown date/);
  r.elements.from.value='';r.elements.unknown.checked=true;r.update();
  assert.match(r.body.innerHTML,/Unknown date/);
  assert.doesNotMatch(r.body.innerHTML,/Dated sold lot/);
});

test('possible reappearances appear as explained pending review with escaped titles',()=>{
  const r=render([{listing_id:'A',title:'<one>',url:'https://example.org/1'},{listing_id:'B',title:'two',url:'https://example.org/2'}],
    [{listing_ids:['A','B'],score:.45,basis:['image dHash distance 0']}]);
  assert.match(r.children[0].innerHTML,/awaiting Mike/);
  assert.match(r.children[0].innerHTML,/&lt;one&gt; ↔ two/);
  assert.match(r.children[0].innerHTML,/not probabilities/);
});
