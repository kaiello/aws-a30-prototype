// Synthetic UI contracts only: no listener, model, database, or external request.
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const html = execFileSync('python', ['-X', 'utf8', '-B', '-c',
  "import ast,pathlib; t=ast.parse(pathlib.Path('src/web.py').read_text(encoding='utf-8')); n=next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='HTML_INDEX' for x in n.targets)); print(ast.literal_eval(n.value))"
], {cwd: root, encoding: 'utf8'});
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const panels = ['citationsBox', 'groundedClaimsBox', 'seeAlsoBox', 'epistemicTraceBox', 'answerRouteBox', 'visualContent'];

function fixture(result = {}, ok = true) {
  const elements = new Map();
  const nodes = [];
  class Element {
    constructor(tag = 'div') {this.tagName = tag.toUpperCase(); this.style = {}; this.children = []; this.listeners = {}; this.attributes = {}; this._text = ''; this._html = ''; this.value = ''; nodes.push(this);}
    set textContent(value) {this._text = String(value ?? ''); this._html = ''; this.children = [];}
    get textContent() {return this._text + this._html + this.children.map(child => child.textContent).join('');}
    set innerText(value) {this.textContent = value;}
    get innerText() {return this.textContent;}
    set innerHTML(value) {this._html = String(value); this._text = ''; this.children = [];}
    get innerHTML() {return this._html;}
    appendChild(child) {this.children.push(child); return child;}
    append(...children) {for (const child of children) this.appendChild(typeof child === 'string' ? Object.assign(new Element(), {textContent: child}) : child);}
    replaceChildren(...children) {this.textContent = ''; this.append(...children);}
    setAttribute(key, value) {this.attributes[key] = String(value);}
    getAttribute(key) {return this.attributes[key];}
    addEventListener(name, handler) {this.listeners[name] = handler;}
    scrollIntoView() {}
  }
  function element(id) {if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id);}
  const context = vm.createContext({
    document: {getElementById: element, createElement: tag => new Element(tag), createTextNode: text => Object.assign(new Element(), {textContent: text}), body: new Element('body'), querySelectorAll: () => []},
    window: {addEventListener() {}},
    localStorage: {getItem: () => '{}', setItem() {}, removeItem() {}},
    alert() {}, console,
    fetch: async () => ({ok, status: ok ? 200 : 502, json: async () => result})
  });
  vm.runInContext(script, context);
  element('queryInput').value = 'Synthetic reviewed term';
  element('engineSelect').value = 'custom'; element('modeSelect').value = 'mix';
  return {context, element, nodes, elements};
}
function result(overrides = {}) {
  return {answer: 'Synthetic answer', answer_outcome: 'generated', answer_origin: 'generated', answer_assessment: {status: 'UNASSESSED'}, citations: {}, grounded_claims: [], resolved_figures: [], resolved_tables: [], see_also: [], ...overrides};
}
function text(f) {return Array.from(f.elements.values()).filter(el => el.style.display !== 'none').map(el => el.textContent).join('\n');}
const tests = [];
function test(name, run) {tests.push({name, run});}

test('static answer heading makes no automatic correctness promise', () => {
  assert.ok(!html.includes('Verified Standard Answer'));
  assert.ok(!html.includes('100% Traceable'));
  assert.ok(!html.includes('Claims Verified'));
  assert.ok(!html.includes('Every material proposition is mapped'));
});

test('generated output and graph links remain explicitly unassessed', async () => {
  const f = fixture(result({grounded_claims: [{claim: 'A synthetic unsupported statement.', anchors: ['Inferred from context']}], epistemic_trace: {epistemic_status: 'VERIFIED_GROUNDED', provenance_score: 1, graph_link_coverage: 1, manifest_summary: 'Graph nodes were found.', concepts_verified: []}, answer_route: {all_evidence_recovered: true, evidence_recall_score: 1, epistemic_score: 1, evidence_group: [{evidence_type: 'text', element_id: 'Clause 4', title: 'Synthetic graph record'}]}}));
  await f.context.executeSearch();
  assert.match(text(f), /Generated answer/i);
  assert.match(text(f), /not (?:independently )?verified|support (?:is )?not assessed/i);
  assert.ok(!text(f).includes('VERIFIED_GROUNDED'));
  assert.ok(!text(f).includes('ALL-EVIDENCE RECOVERED'));
  assert.ok(!text(f).includes('Evidence Recall:'));
  assert.ok(!text(f).includes('100%'));
});

test('reviewed composed answer is distinguished from a model-generated answer', async () => {
  const f = fixture(result({answer_outcome: 'extractive', answer_origin: 'composed', answer_assessment: {status: 'SUPPORTED_REVIEWED_FACTS', validated: true}, grounded_claims: [{claim: 'A synthetic reviewed fact.', anchors: ['Clause 4, p. 7'], support_status: 'SUPPORTED_REVIEWED_FACTS', source_anchors: [{section_id: 'Clause 4', printed_label: '7', verification_state: 'verified'}]}]}));
  await f.context.executeSearch();
  assert.match(text(f), /Reviewed source answer/i);
  assert.match(text(f), /composed from reviewed (?:source )?facts/i);
  assert.ok(!text(f).includes('Generated answer'));
  assert.ok(!text(f).includes('100%'));
});

test('a reviewed status without a validated assessment does not certify a source extract', async () => {
  const f = fixture(result({answer_outcome: 'extractive', answer_origin: 'composed', answer_assessment: {status: 'SUPPORTED_REVIEWED_FACTS', validated: false}}));
  await f.context.executeSearch();
  assert.ok(!text(f).includes('Reviewed source answer'));
  assert.match(text(f), /not (?:independently )?verified|support (?:is )?not assessed/i);
});

test('canonical figure references retain safe source navigation', async () => {
  const f = fixture(result({citations: {figures: ['Figure A1']}}));
  vm.runInContext("figureMap = {'Figure A1': {id: 'Figure A1'}}", f.context);
  await f.context.executeSearch();
  const link = f.nodes.find(node => node.textContent === 'Figure A1' && node.listeners.click);
  assert.ok(link, 'catalog-backed figure reference is clickable');
  assert.equal(link.attributes.onclick, undefined);
  let inspected; f.context.inspectFigureDirectly = id => {inspected = id;}; link.listeners.click();
  assert.equal(inspected, 'Figure A1');
});

for (const [outcome, label] of [['clarification', /More context needed/i], ['abstention', /Out of scope/i], ['insufficient_evidence', /Insufficient evidence/i]]) {
  test(outcome + ' has a readable outcome without a correctness badge', async () => {
    const f = fixture(result({answer_outcome: outcome, answer_origin: 'none', answer_assessment: {status: outcome === 'insufficient_evidence' ? 'INSUFFICIENT_EVIDENCE' : 'NOT_APPLICABLE'}, epistemic_trace: {epistemic_status: 'TRUTHFUL_ABSTENTION', provenance_score: null, graph_link_coverage: null, concepts_verified: []}}));
    await f.context.executeSearch(); assert.match(text(f), label);
    assert.ok(!text(f).includes('TRUTHFUL_ABSTENTION')); assert.ok(!text(f).includes('NaN')); assert.ok(!text(f).includes('0%'));
  });
}

test('related term markup is text, with a functional non-inline click listener', async () => {
  const hostile = '<img src=x onerror=alert(1)>';
  const f = fixture(result({see_also: [hostile]}));
  await f.context.executeSearch();
  assert.ok(!f.nodes.some(node => node.innerHTML.includes(hostile)));
  const chip = f.nodes.find(node => node.textContent === hostile && node.listeners.click);
  assert.ok(chip, 'related term is a text node with an event listener');
  assert.equal(chip.attributes.onclick, undefined);
  let clicked; f.context.setQuery = query => {clicked = query;}; chip.listeners.click();
  assert.equal(clicked, 'What is ' + hostile + '?');
});

test('claim text and unsupported anchors cannot become executable markup', async () => {
  const hostile = '<img src=x onerror=alert(2)>';
  const f = fixture(result({grounded_claims: [{claim: hostile + ' Synthetic statement.', anchors: [hostile]}]}));
  await f.context.executeSearch();
  assert.ok(!f.nodes.some(node => node.innerHTML.includes(hostile)));
  assert.ok(f.element('groundedClaimsBox').textContent.includes(hostile));
  assert.match(f.element('groundedClaimsBox').textContent, /unassessed|not verified/i);
});

test('pending request clears all previous result-dependent evidence', async () => {
  const f = fixture(); let resolveFetch;
  f.context.fetch = () => new Promise(resolve => {resolveFetch = resolve;});
  for (const id of panels) {f.element(id).textContent = 'Previous answer evidence'; f.element(id).style.display = 'block';}
  const pending = f.context.executeSearch();
  for (const id of panels) assert.equal(f.element(id).textContent, '', id + ' clears before response');
  resolveFetch({ok: false, status: 502, json: async () => ({error: 'Synthetic failure', answer_outcome: 'error'})}); await pending;
});

test('generation failure shows a source-free error outcome and no stale panels', async () => {
  const f = fixture({error: '<img src=x onerror=alert(3)> provider detail', error_code: 'GENERATION_FAILED', answer_outcome: 'error', answer_origin: 'none'}, false);
  for (const id of panels) {f.element(id).textContent = 'Previous answer evidence'; f.element(id).style.display = 'block';}
  await f.context.executeSearch();
  assert.match(text(f), /Answer unavailable/i);
  assert.ok(!text(f).includes('provider detail'));
  for (const id of panels) assert.equal(f.element(id).textContent, '', id + ' remains clear after error');
  assert.ok(!f.nodes.some(node => node.innerHTML.includes('<img src=x')));
});

test('network failure clears stale evidence and renders an error result', async () => {
  const f = fixture(); f.context.fetch = async () => {throw new Error('Synthetic network failure');};
  for (const id of panels) f.element(id).textContent = 'Previous answer evidence';
  await f.context.executeSearch(); assert.match(text(f), /Answer unavailable/i);
  for (const id of panels) assert.equal(f.element(id).textContent, '');
});

test('figure inspection clears an earlier answer route', () => {
  const f = fixture();
  vm.runInContext("figureMap = {'Figure A1': {id: 'Figure A1', title: 'Synthetic figure', image_file: 'synthetic.png', page: 'Annex A', chip_count: 0, groups: []}}", f.context);
  f.element('answerRouteBox').textContent = 'Previous route'; f.element('answerRouteBox').style.display = 'block';
  f.context.inspectFigureDirectly('Figure A1');
  assert.equal(f.element('answerRouteBox').style.display, 'none');
  assert.equal(f.element('answerRouteBox').textContent, '');
});

(async () => {
  let failures = 0;
  for (const {name, run} of tests) {
    try {await run(); console.log('PASS ' + name);}
    catch (error) {failures++; console.error('FAIL ' + name + '\n' + error.stack);}
  }
  console.log(`${tests.length - failures}/${tests.length} answer-grounding UI checks passed.`);
  if (failures) process.exitCode = 1;
})();
