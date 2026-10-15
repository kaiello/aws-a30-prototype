// Standard-library JS tests; no browser, sockets, model clients or dependencies.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { execFileSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const html = execFileSync('python', ['-B', '-X', 'utf8', '-c',
  "import ast,pathlib; t=ast.parse(pathlib.Path('src/web.py').read_text(encoding='utf-8')); n=next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='HTML_INDEX' for x in n.targets)); print(ast.literal_eval(n.value))"
], {cwd: root, encoding: 'utf8'});
new vm.Script(html.match(/<script>([\s\S]*?)<\/script>/)[1]);

const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {value: '', style: {}, scrollIntoView() {}});
  return elements.get(id);
}
let stored = JSON.stringify({deepseekKey: 'legacy-secret', geminiKey: 'legacy-secret',
  customKey: 'legacy-secret', deepseekModel: 'saved-model', selectedEngine: 'deepseek'});
let submitted;
const context = vm.createContext({
  document: {getElementById: element},
  localStorage: {getItem() {return stored;}, setItem(key, value) {stored = value;}},
  alert() {}, toggleSettingsDrawer() {}, updateEngineBadge() {}, console,
  fetch: async (url, options) => {
    submitted = JSON.parse(options.body);
    return {ok: false, status: 400, json: async () => ({error: 'fixture stop'})};
  }
});
for (const name of ['readSavedSettings', 'loadSavedSettings', 'saveCustomSettings', 'executeSearch']) {
  const match = html.match(new RegExp('(?:async )?function ' + name + '\\([^)]*\\) \\{[\\s\\S]*?\\n        \\}'));
  assert.ok(match, name + ' exists in served HTML');
  vm.runInContext(match[0], context);
}

(async () => {
  context.loadSavedSettings();
  assert.ok(!stored.includes('legacy-secret'), 'old persisted keys are removed');
  assert.equal(element('cfgDeepseekModel').value, 'saved-model');
  element('cfgDeepseekKey').value = 'page-only-secret';
  context.saveCustomSettings();
  assert.ok(!stored.includes('page-only-secret'), 'saving settings never persists entered keys');
  assert.equal(element('cfgDeepseekKey').value, 'page-only-secret', 'key remains usable in this page');
  element('queryInput').value = 'fixture question';
  element('engineSelect').value = 'deepseek';
  element('modeSelect').value = 'mix';
  await context.executeSearch();
  assert.equal(submitted.api_key, 'page-only-secret', 'existing request key field stays compatible');
  assert.ok(!stored.includes('page-only-secret'));
  console.log('Credential settings: 4 checks passed.');
})().catch(error => {console.error(error); process.exitCode = 1;});
