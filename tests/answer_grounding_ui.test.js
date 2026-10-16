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
const panels = ['citationsBox', 'groundedClaimsBox', 'claimEvidenceBox', 'seeAlsoBox', 'epistemicTraceBox', 'answerRouteBox', 'visualContent'];

function fixture(result = {}, ok = true) {
  const elements = new Map();
  const nodes = [];
  class Element {
    constructor(tag = 'div') {this.tagName = tag.toUpperCase(); this.style = {}; this.children = []; this.listeners = {}; this.attributes = {}; this._text = ''; this._html = ''; this.value = ''; nodes.push(this);}
    set textContent(value) {this._text = String(value ?? ''); this._html = ''; this.children = [];}
    get textContent() {return this._text + this._html + this.children.map(child => child.textContent).join('');}
    set innerText(value) {this.textContent = value;}
    get innerText() {return this.textContent;}
    set innerHTML(value) {
      this._html = String(value); this._text = ''; this.children = [];
      // Model legacy table markup so delayed responses target the currently
      // rendered node when two requests use the same export filename.
      for (const match of this._html.matchAll(/<pre\b[^>]*\bid=["']([^"']+)["'][^>]*>([^<]*)<\/pre>/g)) {
        const child = new Element('pre'); child.textContent = match[2]; child.id = match[1]; this.children.push(child);
      }
    }
    set id(value) {this.attributes.id = String(value); elements.set(String(value), this);}
    get id() {return this.attributes.id;}
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
  return {answer: 'Synthetic answer', answer_outcome: 'generated', answer_origin: 'generated', answer_assessment: {status: 'UNASSESSED'}, citations: {}, grounded_claims: [], claim_evidence_links: [], resolved_figures: [], resolved_tables: [], see_also: [], ...overrides};
}
function evidenceLink(overrides = {}) {
  return {claim_id: 'claim-1', claim: 'A synthetic visual assertion.', mentions: [{raw: '[Annex B, Figure B2]', start: 0, end: 20, kind: 'figure', requested_label: 'Figure B2', resolution: {status: 'exact', labels: ['Figure B2'], target_ids: ['Figure B2']}, qualifiers: {panel: null, page: null}}], reference_status: 'exact', binding_status: 'unavailable', asset_status: 'complete', support_status: 'UNASSESSED', ordered_evidence: [{element_id: 'Figure B2', label: 'Figure B2', relationship: 'direct', source_anchors: [{section_id: 'Annex B', printed_label: '10'}], asset_status: 'complete', assets: [{path: '/synthetic/primary.png', sha256: 'a'.repeat(64), source_anchor_orders: [0], kind: 'image', verification_state: 'verified'}]}], diagnostics: [], ...overrides};
}
const tableMention = {raw: '[Annex A, Table A2]', start: 0, end: 19, kind: 'table', requested_label: 'Table A2', resolution: {status: 'exact', labels: ['Table A2'], target_ids: ['Table A2']}, qualifiers: {panel: null, page: null}};
function text(f) {return Array.from(f.elements.values()).filter(el => el.style.display !== 'none').map(el => el.textContent).join('\n');}
function descendants(node) {return [node, ...node.children.flatMap(descendants)];}
function assetUrls(node) {
  const urls = [];
  if (node.tagName === 'IMG') urls.push(node.getAttribute('src') || node.src);
  for (const match of node.innerHTML.matchAll(/<img\b[^>]*\bsrc=["']([^"']+)["']/g)) urls.push(match[1]);
  for (const child of node.children) urls.push(...assetUrls(child));
  return urls;
}
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

test('figure evidence renders every declared primary and continuation asset in order', async () => {
  const f = fixture(result({resolved_figures: [{figure_id: 'Figure B2', image_path: 'C:\\synthetic\\primary.png', image_paths: ['C:\\synthetic\\primary.png', '/synthetic/continuation-two.png', '/synthetic/continuation-three.png']}]}));
  await f.context.executeSearch();
  assert.deepEqual(assetUrls(f.element('visualContent')), ['/figures/primary.png', '/figures/continuation-two.png', '/figures/continuation-three.png']);
});

for (const imagePaths of [undefined, []]) {
  test('figure evidence retains its primary image fallback for ' + (imagePaths ? 'an empty collection' : 'a legacy payload'), async () => {
    const figure = {figure_id: 'Figure B2', image_path: '/synthetic/primary-fallback.png'};
    if (imagePaths) figure.image_paths = imagePaths;
    const f = fixture(result({resolved_figures: [figure]}));
    await f.context.executeSearch();
    assert.deepEqual(assetUrls(f.element('visualContent')), ['/figures/primary-fallback.png']);
  });
}

test('a declared figure asset collection does not append the legacy primary again', async () => {
  const f = fixture(result({resolved_figures: [{figure_id: 'Figure B2', image_path: '/synthetic/legacy-primary.png', image_paths: ['/synthetic/declared-primary.png', '/synthetic/declared-continuation.png']}]}));
  await f.context.executeSearch();
  assert.deepEqual(assetUrls(f.element('visualContent')), ['/figures/declared-primary.png', '/figures/declared-continuation.png']);
});

test('claim evidence has a dedicated panel with four independent readable states', async () => {
  assert.match(html, /id="claimEvidenceBox"/);
  const f = fixture(result({claim_evidence_links: [evidenceLink()]}));
  await f.context.executeSearch();
  const panel = f.element('claimEvidenceBox');
  assert.equal(panel.style.display, 'block');
  assert.match(panel.textContent, /claim-1/);
  assert.match(panel.textContent, /A synthetic visual assertion\./);
  assert.match(panel.textContent, /Reference resolution:\s*exact/i);
  assert.match(panel.textContent, /Evidence binding:\s*unavailable/i);
  assert.match(panel.textContent, /Asset availability:\s*complete/i);
  assert.match(panel.textContent, /Claim support:\s*UNASSESSED/i);
  assert.ok(!panel.textContent.includes('SUPPORTED_REVIEWED_FACTS'));
});

for (const supportStatus of ['UNASSESSED', 'INSUFFICIENT_EVIDENCE']) {
  test('withheld generated text is labeled as rejected diagnostics while retaining evidence states: ' + supportStatus, async () => {
    const rejectedClaim = 'Synthetic rejected generated statement.';
    const payload = result({answer: 'The generated answer was withheld because its source references could not be resolved.', answer_outcome: 'insufficient_evidence', answer_origin: 'none', grounded_claims: [], claim_evidence_assessment: {answer_withheld: true}, claim_evidence_links: [evidenceLink({claim: rejectedClaim, reference_status: 'unknown', binding_status: 'unavailable', asset_status: 'unavailable', support_status: supportStatus})]});
    const f = fixture(payload);
    await f.context.executeSearch();
    const panel = f.element('claimEvidenceBox');
    assert.match(panel.textContent, /Rejected generated claim diagnostics/);
    assert.match(panel.textContent, /not an asserted answer or proof of support/i);
    assert.match(panel.textContent, /Reference resolution:\s*unknown/i);
    assert.match(panel.textContent, /Evidence binding:\s*unavailable/i);
    assert.match(panel.textContent, /Asset availability:\s*unavailable/i);
    assert.ok(panel.textContent.includes('Claim support: ' + supportStatus));
    assert.ok(panel.textContent.includes(rejectedClaim));
    assert.ok(!f.element('answerContent').textContent.includes(rejectedClaim));
    assert.equal(f.element('groundedClaimsBox').style.display, 'none');
    assert.ok(!panel.textContent.includes('SUPPORTED_REVIEWED_FACTS'));
  });
}

test('an explicit false withheld flag retains the ordinary claim evidence presentation', async () => {
  const f = fixture(result({claim_evidence_assessment: {answer_withheld: false}, claim_evidence_links: [evidenceLink()]}));
  await f.context.executeSearch();
  const panel = f.element('claimEvidenceBox');
  assert.match(panel.textContent, /Claim evidence links/);
  assert.ok(!panel.textContent.includes('Rejected generated claim diagnostics'));
  assert.match(panel.textContent, /Claim support:\s*UNASSESSED/i);
});

test('a wrong existing resolved source with complete assets does not acquire claim support', async () => {
  const f = fixture(result({answer_outcome: 'extractive', answer_origin: 'composed', answer_assessment: {status: 'SUPPORTED_REVIEWED_FACTS', validated: true}, claim_evidence_links: [evidenceLink({binding_status: 'mismatched', support_status: 'INSUFFICIENT_EVIDENCE', diagnostics: ['SELECTED_EVIDENCE_MISMATCH']})]}));
  await f.context.executeSearch();
  const panel = f.element('claimEvidenceBox');
  assert.match(panel.textContent, /Reference resolution:\s*exact/i);
  assert.match(panel.textContent, /Evidence binding:\s*mismatched/i);
  assert.match(panel.textContent, /Asset availability:\s*complete/i);
  assert.match(panel.textContent, /Claim support:\s*INSUFFICIENT_EVIDENCE/i);
  assert.ok(!panel.textContent.includes('SUPPORTED_REVIEWED_FACTS'));
});

test('claim and mention order and unsupported panel qualifiers survive display', async () => {
  const first = evidenceLink({claim_id: 'claim-first', claim: 'First synthetic claim.', reference_status: 'unsupported_qualifier', mentions: [{raw: '[Annex B, Figure B2 (panel z)]', start: 5, end: 34, kind: 'figure', requested_label: 'Figure B2', resolution: {status: 'unsupported_qualifier', labels: ['Figure B2'], target_ids: []}, qualifiers: {panel: 'panel z', page: null}}, {raw: '[Annex B, Figure B3]', start: 40, end: 60, kind: 'figure', requested_label: 'Figure B3', resolution: {status: 'exact', labels: ['Figure B3'], target_ids: ['Figure B3']}, qualifiers: {panel: null, page: null}}], ordered_evidence: [{element_id: 'Figure B2', label: 'Figure B2', relationship: 'navigation_candidate', source_anchors: [], asset_status: 'complete', assets: []}]});
  const second = evidenceLink({claim_id: 'claim-second', claim: 'Second synthetic claim.', ordered_evidence: []});
  const f = fixture(result({claim_evidence_links: [first, second]}));
  await f.context.executeSearch();
  const content = f.element('claimEvidenceBox').textContent;
  assert.ok(content.indexOf('claim-first') < content.indexOf('claim-second'));
  assert.ok(content.indexOf('[Annex B, Figure B2 (panel z)]') < content.indexOf('[Annex B, Figure B3]'));
  assert.match(content, /unsupported_qualifier/i);
  assert.match(content, /navigation candidate/i);
  assert.ok(!content.includes('SUPPORTED_REVIEWED_FACTS'));
});

test('a source-only table keeps its identity and source anchor without inventing an export', async () => {
  const payload = result({claim_evidence_links: [evidenceLink({mentions: [tableMention], reference_status: 'exact', asset_status: 'source_only', ordered_evidence: [{element_id: 'Table A2', label: 'Table A2', relationship: 'direct', source_anchors: [{section_id: 'Annex A', printed_label: '12'}], asset_status: 'source_only', assets: []}]})]});
  const f = fixture(payload); const requested = [];
  f.context.fetch = async url => {requested.push(url); return {ok: true, status: 200, json: async () => payload};};
  await f.context.executeSearch();
  assert.match(f.element('claimEvidenceBox').textContent, /Table A2/);
  assert.match(f.element('claimEvidenceBox').textContent, /Annex A/);
  assert.match(f.element('claimEvidenceBox').textContent, /12/);
  assert.match(f.element('claimEvidenceBox').textContent, /source_only/i);
  assert.deepEqual(requested, ['/api/query']);
  assert.deepEqual(assetUrls(f.element('visualContent')), []);
});

test('an image-only table keeps its declared image set and does not request Markdown', async () => {
  const payload = result({claim_evidence_links: [evidenceLink({mentions: [tableMention], ordered_evidence: [{element_id: 'Table A2', label: 'Table A2', relationship: 'direct', source_anchors: [{section_id: 'Annex A', printed_label: '12'}, {section_id: 'Annex A', printed_label: '13'}], asset_status: 'complete', assets: [{path: '/synthetic/table-first.png', sha256: 'b'.repeat(64), source_anchor_orders: [0], kind: 'image', verification_state: 'verified'}, {path: '/synthetic/table-second.png', sha256: 'c'.repeat(64), source_anchor_orders: [1], kind: 'image', verification_state: 'verified'}]}]})]});
  const f = fixture(payload); const requested = [];
  f.context.fetch = async url => {requested.push(url); return {ok: true, status: 200, json: async () => payload};};
  await f.context.executeSearch();
  assert.deepEqual(assetUrls(f.element('visualContent')), ['/tables/table-first.png', '/tables/table-second.png']);
  assert.deepEqual(requested, ['/api/query']);
  assert.match(f.element('claimEvidenceBox').textContent, /Claim support:\s*UNASSESSED/i);
});

for (const tablePath of [null, undefined]) {
  test('resolved source-only table retains identity and anchors without structured claims or export: ' + tablePath, async () => {
    const table = {table_id: 'Table D2', table_path: tablePath, image_paths: [], source_anchors: [{section_id: 'Annex D', printed_label: '167'}, {section_id: 'Annex D', printed_label: '168'}]};
    const payload = result({resolved_tables: [table]});
    const f = fixture(payload), requested = [];
    f.context.fetch = async url => {requested.push(url); return {ok: true, status: 200, json: async () => payload};};
    await f.context.executeSearch();
    const visual = f.element('visualContent');
    assert.match(visual.textContent, /Table D2/);
    assert.match(visual.textContent, /Annex D/);
    assert.match(visual.textContent, /167/); assert.match(visual.textContent, /168/);
    assert.match(visual.textContent, /source.only/i);
    assert.deepEqual(requested, ['/api/query']);
    assert.deepEqual(assetUrls(visual), []);
    assert.match(f.element('answerStatusBox').textContent, /not assessed/i);
    assert.ok(!text(f).includes('SUPPORTED_REVIEWED_FACTS'));
  });
}

test('resolved image-only table renders healthy ordered images without requesting nonexistent Markdown', async () => {
  const payload = result({resolved_tables: [{table_id: 'Table D2', table_path: null, image_paths: ['C:\\synthetic\\table-primary.png', '/synthetic/table-continuation.png'], source_anchors: [{section_id: 'Annex D', printed_label: '167'}]}]});
  const f = fixture(payload), requested = [];
  f.context.fetch = async url => {requested.push(url); return {ok: true, status: 200, json: async () => payload};};
  await f.context.executeSearch();
  assert.deepEqual(assetUrls(f.element('visualContent')), ['/tables/table-primary.png', '/tables/table-continuation.png']);
  assert.deepEqual(requested, ['/api/query']);
  assert.match(f.element('visualContent').textContent, /Annex D/);
  assert.match(f.element('answerStatusBox').textContent, /not assessed/i);
});

test('an older Markdown response cannot overwrite a newer request using the same export', async () => {
  const payload = result({resolved_tables: [{table_id: 'Table D2', table_path: '/synthetic/shared.md', image_paths: []}]});
  const f = fixture(payload), pendingText = [];
  f.context.fetch = async url => url === '/api/query'
    ? {ok: true, json: async () => payload}
    : {ok: true, text: () => new Promise(resolve => pendingText.push(resolve))};
  await f.context.executeSearch(); await new Promise(resolve => setImmediate(resolve));
  f.element('queryInput').value = 'Second table query';
  await f.context.executeSearch(); await new Promise(resolve => setImmediate(resolve));
  assert.equal(pendingText.length, 2);
  pendingText[1]('New current table'); await new Promise(resolve => setImmediate(resolve));
  pendingText[0]('Stale earlier table'); await new Promise(resolve => setImmediate(resolve));
  const currentPre = descendants(f.element('visualContent')).find(node => node.tagName === 'PRE');
  assert.equal(currentPre.textContent, 'New current table');
});

test('figure inspection invalidates a pending table Markdown response', async () => {
  const payload = result({resolved_tables: [{table_id: 'Table D2', table_path: '/synthetic/old.md', image_paths: []}]});
  const f = fixture(payload); let finishText;
  f.context.fetch = async url => url === '/api/query'
    ? {ok: true, json: async () => payload}
    : {ok: true, text: () => new Promise(resolve => {finishText = resolve;})};
  await f.context.executeSearch(); await new Promise(resolve => setImmediate(resolve));
  const oldPre = descendants(f.element('visualContent')).find(node => node.tagName === 'PRE');
  vm.runInContext("figureMap={'Figure A1':{id:'Figure A1',title:'Synthetic figure',image_file:'synthetic.png',page:'Annex A',groups:[]}}", f.context);
  f.context.inspectFigureDirectly('Figure A1');
  finishText('Stale earlier table'); await new Promise(resolve => setImmediate(resolve));
  assert.equal(oldPre.textContent, 'Loading table content...');
  assert.ok(!f.element('visualContent').textContent.includes('Stale earlier table'));
  assert.match(f.element('answerStatusBox').textContent, /Figure inspection/);
});

test('canonical internal table IDs retain image-only table rendering by display label', async () => {
  const payload=result({claim_evidence_links:[evidenceLink({ordered_evidence:[{element_id:'table:table_a2',label:'Table A2',relationship:'direct',assets:[{path:'/synthetic/canonical.png',kind:'image',verification_state:'verified'}]}]})]});
  const f=fixture(payload);await f.context.executeSearch();
  assert.deepEqual(assetUrls(f.element('visualContent')),['/tables/canonical.png']);
});

for (const state of ['complete','missing','corrupt']) {
  test('canonical figure claim assets render when legacy projection is absent: '+state,async()=>{
    const payload=result({claim_evidence_links:[evidenceLink({asset_status:state,ordered_evidence:[{element_id:'figure:figure_b16c',label:'Figure B16C',relationship:'direct',asset_status:state,assets:[{path:'/synthetic/healthy.png',kind:'image',verification_state:'verified'}],declared_assets:[{path:'/synthetic/healthy.png'},{path:'/synthetic/unavailable.png'}]}]})]});
    const f=fixture(payload);await f.context.executeSearch();
    assert.deepEqual(assetUrls(f.element('visualContent')),['/figures/healthy.png']);
    assert.match(f.element('claimEvidenceBox').textContent,/UNASSESSED/);
  });
}

test('a late older response cannot overwrite a newer query evidence', async () => {
  const f=fixture();const pending=[];
  f.context.fetch=()=>new Promise(resolve=>pending.push(resolve));
  const first=f.context.executeSearch();
  f.element('queryInput').value='Second query';const second=f.context.executeSearch();
  pending[1]({ok:true,json:async()=>result({answer:'Second answer',claim_evidence_links:[evidenceLink({claim:'Second claim'})]})});await second;
  pending[0]({ok:true,json:async()=>result({answer:'First answer',claim_evidence_links:[evidenceLink({claim:'First claim'})]})});await first;
  assert.equal(f.element('answerContent').textContent,'Second answer');
  assert.ok(f.element('claimEvidenceBox').textContent.includes('Second claim'));
});

test('figure inspection invalidates a pending query response', async () => {
  const f=fixture();let finish;
  f.context.fetch=()=>new Promise(resolve=>{finish=resolve;});
  const search=f.context.executeSearch();
  vm.runInContext("figureMap={'Figure A1':{id:'Figure A1',title:'Synthetic figure',image_file:'synthetic.png',page:'Annex A',groups:[]}}",f.context);
  f.context.inspectFigureDirectly('Figure A1');
  finish({ok:true,json:async()=>result({answer:'Late answer',claim_evidence_links:[evidenceLink()]})});await search;
  assert.equal(f.element('claimEvidenceBox').textContent,'');
  assert.ok(!f.element('answerContent').textContent.includes('Late answer'));
});

test('claim evidence payload strings cannot create HTML, inline handlers, or arbitrary links', async () => {
  const hostile = '<img src=x onerror=alert(4)>';
  const link = evidenceLink({claim_id: hostile, claim: hostile, mentions: [{raw: hostile, requested_label: hostile, href: 'javascript:alert(4)'}], ordered_evidence: [{element_id: hostile, label: hostile, relationship: 'direct', source_anchors: [{section_id: hostile, printed_label: hostile, href: 'https://invalid.example/source'}], asset_status: 'source_only', assets: []}], href: 'javascript:alert(4)', diagnostics: [hostile]});
  const f = fixture(result({claim_evidence_links: [link]}));
  await f.context.executeSearch();
  const panel = f.element('claimEvidenceBox');
  assert.ok(panel.textContent.includes(hostile));
  for (const node of descendants(panel)) {
    assert.ok(!node.innerHTML.includes(hostile));
    assert.equal(node.getAttribute('onclick'), undefined);
    assert.equal(node.getAttribute('href'), undefined);
    assert.equal(node.href, undefined);
  }
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

test('direct figure inspection renders its ordered primary and continuation assets with separate zoom targets', () => {
  const f = fixture();
  vm.runInContext("figureMap = {'Figure B6': {id: 'Figure B6', title: 'Synthetic continued figure', image_file: 'legacy.png', image_files: ['primary.png', 'continuation-two.png', 'continuation-three.png'], page: 'Annex B', chip_count: 0, groups: []}}", f.context);
  f.context.inspectFigureDirectly('Figure B6');
  const visual = f.element('visualContent');
  assert.deepEqual(assetUrls(visual), ['/figures/primary.png', '/figures/continuation-two.png', '/figures/continuation-three.png']);
  const images = descendants(visual).filter(node => node.tagName === 'IMG');
  const zoomTargets = descendants(visual).filter(node => node.listeners.click && node.getAttribute('role') === 'button');
  assert.equal(images.length, 3);
  assert.equal(zoomTargets.length, 3);
  const opened = []; f.context.openImageModal = (...args) => opened.push(args);
  zoomTargets.forEach(target => target.listeners.click());
  assert.deepEqual(opened.map(args => args[0]), ['/figures/primary.png', '/figures/continuation-two.png', '/figures/continuation-three.png']);
  assert.ok(opened.every(args => !args[1].includes('SUPPORTED_REVIEWED_FACTS')));
});

for (const imageFiles of [undefined, []]) {
  test('direct figure inspection retains primary fallback for ' + (imageFiles ? 'an empty array' : 'a legacy catalog entry'), () => {
    const f = fixture();
    const data = {id: 'Figure A1', title: 'Synthetic figure', image_file: 'primary-fallback.png', page: 'Annex A', chip_count: 0, groups: []};
    if (imageFiles) data.image_files = imageFiles;
    f.context.fixtureFigure = data;
    vm.runInContext("figureMap = {'Figure A1': fixtureFigure}", f.context);
    f.context.inspectFigureDirectly('Figure A1');
    assert.deepEqual(assetUrls(f.element('visualContent')), ['/figures/primary-fallback.png']);
  });
}

test('direct figure inspection restores a citation panel hidden by the preceding request', () => {
  const f = fixture();
  vm.runInContext("figureMap = {'Figure A1': {id: 'Figure A1', title: 'Synthetic figure', image_file: 'synthetic.png', page: 'Annex A', chip_count: 0, groups: []}}", f.context);
  f.element('citationsBox').style.display = 'none';
  f.context.inspectFigureDirectly('Figure A1');
  assert.equal(f.element('citationsBox').style.display, 'block');
  assert.match(f.element('citationsBox').textContent, /Figure source reference/);
  assert.match(f.element('citationsBox').textContent, /Annex A/);
});

test('figure inspection clears all earlier answer-dependent evidence panels', () => {
  const f = fixture();
  vm.runInContext("figureMap = {'Figure A1': {id: 'Figure A1', title: 'Synthetic figure', image_file: 'synthetic.png', page: 'Annex A', chip_count: 0, groups: []}}", f.context);
  const answerPanels = panels.filter(id => !['citationsBox', 'visualContent'].includes(id));
  for (const id of answerPanels) {f.element(id).textContent = 'Previous answer evidence'; f.element(id).style.display = 'block';}
  f.context.inspectFigureDirectly('Figure A1');
  for (const id of answerPanels) {
    assert.equal(f.element(id).style.display, 'none', id + ' hides during figure inspection');
    assert.equal(f.element(id).textContent, '', id + ' clears during figure inspection');
  }
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
