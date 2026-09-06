// Isolated controller tests: no browser, network, or changes to the corpus.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const script = fs.readFileSync(path.join(__dirname, '../web/home.js'), 'utf8');

function controller({reduced = false, response} = {}) {
  const nodes = new Map();
  function node(key) {
    if (!nodes.has(key)) {
      const classes = new Set();
      nodes.set(key, {textContent: '', innerHTML: '', dataset: {}, listeners: {},
        classList: {add: v => classes.add(v), remove: v => classes.delete(v), contains: v => classes.has(v)},
        addEventListener(type, fn) { this.listeners[type] = fn; },
        setAttribute() {}, remove() {},
        focus(options) { this.focusOptions = options; },
        scrollIntoView(options) { this.scrollOptions = options; },
      });
    }
    return nodes.get(key);
  }
  const scroll = node('scroll'); scroll.dataset.introScroll = 'origins';
  const root = node('root');
  root.querySelector = node;
  root.querySelectorAll = selector => selector === '[data-intro-scroll]' ? [scroll] : [];
  const window = {addEventListener() {}};
  vm.runInNewContext(script, {
    document: {querySelector: () => root, getElementById: node}, window,
    matchMedia: query => ({matches: query.includes('reduced-motion') ? reduced : false}),
    fetch: async () => response || {ok: false},
    Date, Map, Math,
  });
  return {intro: window.Introduction, node, scroll};
}

test('HTTP failure leaves a browse link and a working retry action', async () => {
  const {intro, node} = controller();
  await intro.render();
  assert.match(node('#intro-data-status').innerHTML, /href="#\/explore"/);
  assert.match(node('#intro-chart').textContent, /unavailable/);
  assert.equal(typeof node('#intro-retry').listeners.click, 'function');
  await node('#intro-retry').listeners.click();
  assert.match(node('#intro-data-status').innerHTML, /Try again/);
});

test('an inconsistent identity snapshot fails visibly instead of drawing false counts', async () => {
  const {intro, node} = controller({response: {ok: true, json: async () => ({identity_count: 2, identities: []})}});
  await intro.render();
  assert.equal(node('#intro-data-status').classList.contains('is-error'), true);
  assert.match(node('#intro-selection').textContent, /unavailable/);
});

test('reduced motion makes the story jump immediate and transfers keyboard focus', () => {
  const {scroll, node} = controller({reduced: true});
  let prevented = false;
  scroll.listeners.click({preventDefault() { prevented = true; }});
  assert.equal(prevented, true);
  assert.equal(node('origins').scrollOptions.behavior, 'instant');
  assert.equal(node('origins').focusOptions.preventScroll, true);
});

test('invalidating a snapshot clears old totals before another load can fail', async () => {
  const {intro, node} = controller();
  node('#intro-total').textContent = '123';
  intro.invalidate();
  assert.equal(node('#intro-total').textContent, '—');
  assert.match(node('#intro-snapshot-note').textContent, /pending/);
  await intro.render();
  assert.equal(node('#intro-total').textContent, '—');
});
