// Exercise actual served modal functions with a synthetic DOM; no browser/network/models.
const assert = require('node:assert/strict');
const vm = require('node:vm');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const html = execFileSync('python', ['-B', '-X', 'utf8', '-c',
  "import ast,pathlib; t=ast.parse(pathlib.Path('src/web.py').read_text(encoding='utf-8')); n=next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='HTML_INDEX' for x in n.targets)); print(ast.literal_eval(n.value))"
], {cwd: root, encoding: 'utf8'});

function modalContext() {
  const elements = new Map();
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      style: {display: 'block'}, attributes: {}, complete: true, naturalWidth: 200,
      clientWidth: 200, clientHeight: 100,
      setAttribute(name, value) { this.attributes[name] = String(value); }
    });
    return elements.get(id);
  }
  const context = vm.createContext({document: {getElementById: element, body: {style: {}}}});
  vm.runInContext('let currentScale=1, translateX=0, translateY=0, activeBbox=null, activeLabel=null, scrimEnabled=true;', context);
  for (const name of ['openImageModal', 'updateModalTransform', 'toggleScrim']) {
    const match = html.match(new RegExp('function ' + name + '\\([^)]*\\) \\{[\\s\\S]*?\\n        \\}'));
    assert.ok(match, name + ' exists in served HTML');
    vm.runInContext(match[0], context);
  }
  return {context, element};
}

const invalid = [
  ['missing', null], ['short', [0, 0, 1]], ['long', [0, 0, 1, 1, 1]],
  ['string', '0011'], ['boolean', [false, 0, 1, 1]], ['numeric string', [0, '0', 1, 1]],
  ['null coordinate', [0, null, 1, 1]], ['NaN', [NaN, 0, 1, 1]],
  ['positive infinity', [0, 0, Infinity, 1]], ['negative infinity', [0, -Infinity, 1, 1]],
  ['reversed y', [.7, .2, .1, .8]], ['reversed x', [.1, .8, .7, .2]],
  ['zero height', [.2, .2, .2, .8]], ['zero width', [.1, .5, .7, .5]],
  ['negative', [-.01, .2, .7, .8]], ['above one', [.1, .2, 1.01, .8]],
  ['wrong scale', [100, 200, 600, 800]]
];
for (const [label, bbox] of invalid) {
  const {context, element} = modalContext();
  context.openImageModal('synthetic.png', 'Synthetic figure', bbox, 'Synthetic feature');
  assert.equal(element('svgHighlightGroup').style.display, 'none', label + ' hides highlight');
  assert.equal(element('svgScrim').style.display, 'none', label + ' hides scrim');
  assert.equal(vm.runInContext('activeBbox', context), null, label + ' clears focus state');
  assert.equal(vm.runInContext('currentScale', context), 1, label + ' resets zoom');
  assert.equal(element('modalStage').style.transform, 'translate(0px, 0px) scale(1)', label + ' has finite transform');
  context.toggleScrim();
  context.toggleScrim();
  assert.equal(element('svgScrim').style.display, 'none', label + ' cannot revive invalid scrim');
}

function numberAttribute(element, name) {
  const value = Number(element.attributes[name]);
  assert.ok(Number.isFinite(value), name + ' is finite');
  return value;
}
for (const bbox of [[.1, .2, .6, .8], [0, 0, 1, 1], [.98, .99, 1, 1], [0, 0, .001, .001]]) {
  const {context, element} = modalContext();
  const before = [...bbox];
  context.openImageModal('synthetic.png', 'Synthetic figure', bbox, 'Synthetic feature');
  assert.equal(element('svgHighlightGroup').style.display, 'block');
  const rect = element('svgHighlightRect');
  const x = numberAttribute(rect, 'x'), y = numberAttribute(rect, 'y');
  const width = numberAttribute(rect, 'width'), height = numberAttribute(rect, 'height');
  assert.ok(x >= 0 && y >= 0 && width > 0 && height > 0, 'positive contained rectangle');
  assert.ok(x + width <= 1000 && y + height <= 1000, 'minimum display size stays inside image');
  if (bbox[0] === .1) {
    assert.ok(Math.abs(x - 200) < 1e-9 && Math.abs(y - 100) < 1e-9, 'y/x convention preserved');
    assert.ok(Math.abs(width - 600) < 1e-9 && Math.abs(height - 500) < 1e-9, 'asymmetric geometry preserved');
  }
  assert.deepEqual(bbox, before, 'source coordinates remain unchanged');
}
// Invalid focus must clear immediately even when the next image never loads.
{
  const {context, element} = modalContext();
  context.openImageModal('focused.png', 'Focused figure', [.1, .2, .6, .8], 'Valid feature');
  assert.equal(element('svgHighlightGroup').style.display, 'block');
  const image = element('modalImg');
  image.complete = false;
  image.naturalWidth = 0;
  context.openImageModal('uncached-or-broken.png', 'Next figure', [.2, .2, .2, .8], 'Invalid feature');
  assert.equal(vm.runInContext('activeBbox', context), null, 'invalid transition clears focus state');
  assert.equal(element('svgHighlightGroup').style.display, 'none', 'old highlight clears before image load');
  assert.equal(element('svgScrim').style.display, 'none', 'old scrim clears before image load');
  assert.equal(element('clearFocusBtn').style.display, 'none', 'old focus control clears before image load');
  assert.equal(vm.runInContext('currentScale', context), 1, 'zoom resets before image load');
  assert.equal(element('modalStage').style.transform, 'translate(0px, 0px) scale(1)', 'transform resets before image load');
}
console.log('Bounding-box modal: 17 invalid cases, 4 valid/edge cases and 1 unloaded-image transition passed.');
