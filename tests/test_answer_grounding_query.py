"""Actual query-function orchestration with synthetic boundaries only."""
import ast, asyncio, hashlib, json, time
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
import pytest
ROOT=Path(__file__).resolve().parents[1]

def load_query(*, reviewed=None, composed=None, gate=None, response='Unassessed generated fixture.', failure=False):
    calls=[]
    def forbidden(*args,**kwargs):
        raise AssertionError('Unexpected external work')
    def lookup(query):
        calls.append('lookup');return reviewed
    def compose(query,bundle):
        calls.append('compose');return composed
    class Rag:
        async def initialize_storages(self): calls.append('initialize')
        async def aquery(self,prompt,param):
            calls.append(('generate',prompt))
            if failure: raise RuntimeError('PRIVATE PROVIDER DETAIL')
            return response
    class Missing(FileNotFoundError):pass
    class Invalid(RuntimeError):pass
    def resolve(claims, evidence_context=(), *, reviewed_fact_view=None):
        calls.append(('resolve',claims,evidence_context,reviewed_fact_view))
        supported=reviewed_fact_view is not None and bool(claims)
        return {'links':[{'claim_id':c.get('claim_id'),'support_status':'SUPPORTED_REVIEWED_FACTS' if supported else 'UNASSESSED'} for c in claims],
                'assessment':{'status':'SUPPORTED_REVIEWED_FACTS' if supported else 'UNASSESSED','complete':supported,'diagnostics':[]},
                'timings_ms':{'reference_parse':1,'manifest_lookup':2,'asset_validation':3,'binding_checks':4,'total':10}}
    from src.standard_manifest import ManifestError
    ns=dict(Optional=Optional,DEFAULT_ENGINE='custom',CUSTOM_API_KEY='',DEEPSEEK_API_KEY='',GEMINI_API_KEY='',ManifestError=ManifestError,
        STORAGE_DIR=Path('unused'),check_early_abstention=lambda q:gate,
        get_terminology_evidence=lookup,compose_grounded_answer=compose,
        hybrid_retrieve=lambda *a,**k:[{'id':'synthetic-chunk','content':'Synthetic source'}],
        ContextualIndexMissingError=Missing,TerminologyRegistryError=Invalid,
        get_rag_instance=lambda **kw:Rag(),QueryParam=lambda **kw:kw,
        extract_citations=lambda text:{},extract_grounded_claims=lambda text:[],
        resolve_multimodal_assets=lambda text:([],[]),extract_see_also_terms=lambda text:[],
        verify_epistemic_provenance=lambda *a,**kw:{'epistemic_status':kw.get('decision',{}).get('status','UNASSESSED'),'provenance_score':None},
        resolve_answer_route=lambda *a,**kw:SimpleNamespace(to_dict=lambda:{'status':'EVIDENCE_LINKS_FOUND'}),
        resolve_claim_evidence=resolve,project_reviewed_facts=lambda bundle:{'status':'SUPPORTED_REVIEWED_FACTS','facts':[{'fact_id':'fact:synthetic'}]},
        extract_reference_records=lambda text,**kwargs:[],
        qualify_reference_hierarchy=lambda text,mentions,**kwargs:{'mentions':mentions,'diagnostics':[]},
        hashlib=hashlib,json=json,time=time)
    tree=ast.parse((ROOT/'src/query.py').read_text(encoding='utf-8'))
    # Include the shared response helper if introduced by this bounded change.
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in {'async_query','_query_failure','_reviewed_trace','_scope_decision','_attach_claim_evidence','_empty_claim_evidence','_resolve_display_assets','_reject_unresolved_citations'}]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-query','exec'),ns)
    return ns['async_query'],calls,ns

def test_composed_route_needs_no_key_rag_database_or_second_retrieval():
    answer={'answer':'Reviewed synthetic answer.','citations':{},'grounded_claims':[{'claim_id':'claim:synthetic','claim':'Synthetic fact.'}],
            'answer_origin':'composed','answer_outcome':'extractive',
            'answer_assessment':{'status':'SUPPORTED_REVIEWED_FACTS','validated':True}}
    q,calls,ns=load_query(reviewed={'id':'terminology:synthetic','terminology_resolution':{}},composed=answer)
    ns['hybrid_retrieve']=lambda *a,**k:pytest.fail('Composed route must not add unrestricted retrieval')
    ns['get_rag_instance']=lambda *a,**k:pytest.fail('Composed route must not load a model')
    result=asyncio.run(q('Define synthetic legacy term',engine='custom'))
    assert result['answer']==answer['answer']
    assert result['answer_origin']=='composed'
    assert result['epistemic_trace']['provenance_score'] is None
    assert calls[:2]==['lookup','compose']
    assert [c[0] for c in calls if isinstance(c,tuple)]==['resolve']

def test_scope_gate_precedes_credentials_and_records_explicit_decision():
    q,calls,ns=load_query(gate={'answer':'This requested requirement is outside this terminology standard.','status':'TRUTHFUL_ABSTENTION'})
    result=asyncio.run(q('Synthetic scope request',engine='custom'))
    assert result['answer_outcome']=='abstention'
    assert result['answer_origin']=='none'
    assert result['epistemic_trace']['epistemic_status']=='TRUTHFUL_ABSTENTION'
    assert result['answer_assessment']['validated'] is True
    assert result['answer_assessment']['assessment_scope']=='deterministic_scope_policy'
    assert result['answer_assessment']['answer_sha256']==hashlib.sha256(result['answer'].encode()).hexdigest()
    assert calls==[]

def test_generated_route_is_distinct_and_unassessed():
    q,calls,_=load_query()
    result=asyncio.run(q('Unrelated synthetic query',engine='custom',api_key='fixture'))
    assert result['answer_outcome']=='generated'
    assert result['answer_origin']=='generated'
    assert result['answer_assessment']['status']=='UNASSESSED'
    assert len([c for c in calls if isinstance(c,tuple) and c[0]=='generate'])==1

def test_generation_failure_never_returns_raw_extract_or_provider_detail():
    q,calls,_=load_query(failure=True)
    result=asyncio.run(q('Synthetic request',engine='custom',api_key='fixture'))
    assert result['answer_outcome']=='error'
    assert result['error_code']=='GENERATION_FAILED'
    assert result['answer']==''
    assert 'PRIVATE' not in json.dumps(result)
    assert result['grounded_claims']==[]

def test_missing_provider_is_explicit_error_not_answer():
    q,_,_=load_query()
    result=asyncio.run(q('Synthetic request',engine='custom'))
    assert result['answer_outcome']=='error'
    assert result['error_code']=='MODEL_PROVIDER_UNCONFIGURED'

def test_empty_model_response_is_execution_failure():
    q,_,_=load_query(response='   ')
    result=asyncio.run(q('Synthetic request',engine='custom',api_key='fixture'))
    assert result.get('error_code')=='GENERATION_FAILED'

def test_relevant_registry_failure_precedes_provider_initialization():
    q,calls,ns=load_query()
    def bad(q):raise ns['TerminologyRegistryError']('private registry detail')
    ns['get_terminology_evidence']=bad
    result=asyncio.run(q('Synthetic request',engine='custom'))
    assert result['error_code']=='TERMINOLOGY_REGISTRY_INVALID'
    assert 'private registry detail' not in json.dumps(result)

@pytest.mark.parametrize('query', [
    'Define a synthetic weld; do not discuss acceptance criteria.',
    'Define a synthetic weld without discussing acceptance criteria.',
    'Define a synthetic weld; don\'t include preheat temperatures.'
])
def test_negated_excluded_topic_does_not_trigger_scope_refusal(query):
    from src.pre_retrieval import check_early_abstention
    assert check_early_abstention(query) is None

def test_actual_requested_requirement_still_triggers_scope_gate():
    from src.pre_retrieval import check_early_abstention
    assert check_early_abstention('Define a synthetic weld and provide acceptance criteria.') is not None

@pytest.mark.parametrize('query', [
    'Define a synthetic weld without examples and state acceptance criteria.',
    'Define a synthetic weld excluding examples, then explain acceptance criteria.',
    'Do not discuss acceptance criteria but state preheat temperatures.'
])
def test_exclusion_does_not_cancel_a_separate_positive_scope_request(query):
    from src.pre_retrieval import check_early_abstention
    assert check_early_abstention(query) is not None

@pytest.mark.parametrize('query', [
    'Define a synthetic weld without acceptance criteria or preheat temperatures.',
    'Define a synthetic weld; do not discuss acceptance criteria and preheat schedules.'
])
def test_adjacent_negated_scope_topic_list_remains_excluded(query):
    from src.pre_retrieval import check_early_abstention
    assert check_early_abstention(query) is None

@pytest.mark.parametrize('code,expected', [('MODEL_PROVIDER_UNCONFIGURED',503),('GENERATION_FAILED',502),('EVIDENCE_BINDING_FAILED',503)])
def test_http_reports_structured_execution_failure_without_success_status(code,expected,tmp_path):
    import importlib.util
    spec=importlib.util.spec_from_file_location('grounding_http_fixture',ROOT/'tests/test_security_boundaries.py')
    fixture_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture_module)
    fixture=fixture_module.web_fixture.__wrapped__(tmp_path)
    fixture[0].run_query=lambda *args,**kwargs:{'answer':'','error':'Answer unavailable.','error_code':code,'answer_outcome':'error'}
    status,_,body=fixture_module.request(fixture,'/api/query','POST',{'query':'Synthetic request'})
    assert status==expected
    assert json.loads(body)['error_code']==code


def test_composed_route_derives_privileged_view_only_from_server_bundle():
    bundle={'id':'server-reviewed','terminology_resolution':{}}
    claims=[{'claim_id':'claim:synthetic','claim':'Synthetic reviewed fact.'}]
    answer={'answer':'Reviewed synthetic answer.','grounded_claims':claims,'answer_origin':'composed',
            'answer_outcome':'extractive','answer_assessment':{'status':'SUPPORTED_REVIEWED_FACTS','validated':True}}
    q,calls,ns=load_query(reviewed=bundle,composed=answer)
    seen=[]
    ns['project_reviewed_facts']=lambda supplied:seen.append(supplied) or {'status':'SUPPORTED_REVIEWED_FACTS','facts':[{'fact_id':'fact:synthetic'}]}
    result=asyncio.run(q('Synthetic reviewed definition'))
    assert seen==[bundle]
    invocation=next(c for c in calls if isinstance(c,tuple) and c[0]=='resolve')
    assert invocation[1]==claims and invocation[2]==[bundle]
    assert invocation[3]['status']=='SUPPORTED_REVIEWED_FACTS'
    assert result['claim_evidence_assessment']['complete'] is True
    assert result['claim_evidence_links'][0]['support_status']=='SUPPORTED_REVIEWED_FACTS'
    assert result['timings_ms']['claim_evidence_asset_validation']==3


def test_generated_route_uses_actual_claims_and_context_without_review_or_invented_selection():
    q,calls,ns=load_query(response='- Synthetic claim (Figure B1).')
    claim={'claim':'Synthetic claim (Figure B1).','anchors':['Figure B1']}
    ns['extract_grounded_claims']=lambda text:[claim]
    ns['project_reviewed_facts']=lambda bundle:pytest.fail('Generated evidence cannot grant a privileged reviewed view')
    result=asyncio.run(q('Synthetic query',api_key='fixture'))
    invocation=next(c for c in calls if isinstance(c,tuple) and c[0]=='resolve')
    assert invocation[1]==[claim] and invocation[2]==result['retrieved_evidence']
    assert invocation[3] is None
    assert 'selected_evidence_ids' not in invocation[1][0]
    assert result['answer_assessment']['status']=='UNASSESSED'
    assert result['claim_evidence_links'][0]['support_status']=='UNASSESSED'


@pytest.mark.parametrize('assessment',[{'status':'INSUFFICIENT_EVIDENCE','complete':False},
                                        {'status':'SUPPORTED_REVIEWED_FACTS','complete':False},
                                        {'status':'UNASSESSED','complete':True}])
def test_composed_support_disagreement_is_guarded_without_generation_fallback(assessment):
    answer={'answer':'PRIVATE SOURCE FACT','grounded_claims':[{'claim':'Synthetic fact'}],
            'answer_origin':'composed','answer_outcome':'extractive',
            'answer_assessment':{'status':'SUPPORTED_REVIEWED_FACTS','validated':True}}
    q,calls,ns=load_query(reviewed={'id':'server-reviewed'},composed=answer)
    ns['resolve_claim_evidence']=lambda *a,**k:{'links':[],'assessment':assessment,'timings_ms':{}}
    result=asyncio.run(q('Synthetic definition'))
    assert result['error_code']=='EVIDENCE_BINDING_FAILED'
    assert result['answer']=='' and result['answer_assessment']['validated'] is False
    assert result['claim_evidence_assessment']['status']=='INSUFFICIENT_EVIDENCE'
    assert 'PRIVATE SOURCE FACT' not in json.dumps(result)
    assert calls==['lookup','compose']


def test_empty_claims_do_not_vacuously_preserve_reviewed_badge():
    answer={'answer':'Synthetic reviewed text','grounded_claims':[],
            'answer_origin':'composed','answer_assessment':{'status':'SUPPORTED_REVIEWED_FACTS','validated':True}}
    q,calls,ns=load_query(reviewed={'id':'server-reviewed'},composed=answer)
    result=asyncio.run(q('Synthetic definition'))
    assert result['error_code']=='EVIDENCE_BINDING_FAILED'
    assert calls==['lookup','compose']


@pytest.mark.parametrize('gate,key',[(None,None),({'answer':'Outside the standard.'},None),(None,'fixture')])
def test_empty_claim_routes_expose_unassessed_metadata_without_resolver_io(gate,key):
    q,_,ns=load_query(gate=gate)
    ns['resolve_claim_evidence']=lambda *a,**k:pytest.fail('No claims must not trigger resolver work')
    result=asyncio.run(q('Synthetic request',api_key=key))
    assert result['claim_evidence_links']==[]
    assert result['claim_evidence_assessment']['status']=='UNASSESSED'
    assert result['claim_evidence_assessment']['complete'] is False
    assert 'no_claims_extracted' in result['claim_evidence_assessment']['diagnostics']


def test_resolver_error_is_source_free_and_cannot_leave_a_reviewed_badge():
    answer={'answer':'PRIVATE SOURCE FACT','grounded_claims':[{'claim':'Synthetic fact'}],
            'answer_origin':'composed','answer_assessment':{'status':'SUPPORTED_REVIEWED_FACTS','validated':True}}
    q,calls,ns=load_query(reviewed={'id':'server-reviewed'},composed=answer)
    def bad(*a,**k):raise ValueError('PRIVATE BINDING DETAIL')
    ns['resolve_claim_evidence']=bad
    result=asyncio.run(q('Synthetic definition'))
    assert result['error_code']=='EVIDENCE_BINDING_FAILED'
    assert 'PRIVATE' not in json.dumps(result)


@pytest.mark.parametrize('route',['composed','generated','scope'])
def test_legacy_display_asset_failure_cannot_preempt_explicit_claim_results(route):
    claims=[{'claim_id':'claim:synthetic','claim':'Synthetic fact'}]
    composed={'answer':'Synthetic source answer','grounded_claims':claims,'answer_origin':'composed',
              'answer_assessment':{'status':'SUPPORTED_REVIEWED_FACTS','validated':True}}
    q,_,ns=load_query(reviewed={'id':'reviewed'} if route=='composed' else None,
                     composed=composed if route=='composed' else None,
                     gate={'answer':'Outside scope.'} if route=='scope' else None)
    def unavailable(text):raise ns['ManifestError']('MANIFEST_ASSET_MISSING','Private asset path')
    ns['resolve_multimodal_assets']=unavailable
    result=asyncio.run(q('Synthetic request',api_key='fixture'))
    assert result['resolved_figures']==[] and result['resolved_tables']==[]
    assert result['answer']
    assert 'Private asset path' not in json.dumps(result)
    assert 'claim_evidence_assessment' in result


@pytest.mark.parametrize('label,missing,expected',[('Clause 4',True,'SUPPORTED_REVIEWED_FACTS'),
                                                ('Figure X1',True,'INSUFFICIENT_EVIDENCE'),
                                                ('Figure X1',False,'SUPPORTED_REVIEWED_FACTS')])
def test_actual_resolver_shape_through_query_with_synthetic_native_bindings(tmp_path,monkeypatch,label,missing,expected):
    import importlib.util
    from src.evidence_resolution import resolve_claim_evidence
    spec=importlib.util.spec_from_file_location('query_native_fixture',ROOT/'tests/test_citation_evidence_resolution.py')
    fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    manifest=fixture.FakeManifest(tmp_path)
    claims,view=fixture.reviewed(manifest,(label,))
    if missing:(tmp_path/'parsed/figures/continuation.png').unlink()
    answer={'answer':'Synthetic native source answer','grounded_claims':claims,'answer_origin':'composed',
            'answer_outcome':'extractive','answer_assessment':{'status':'SUPPORTED_REVIEWED_FACTS','validated':True}}
    q,_,ns=load_query(reviewed={'id':'server-bundle'},composed=answer)
    ns['project_reviewed_facts']=lambda bundle:view
    ns['resolve_claim_evidence']=lambda c,e,**kw:resolve_claim_evidence(c,e,manifest=manifest,**kw)
    result=asyncio.run(q('Synthetic definition'))
    assert result['claim_evidence_assessment']['status']==expected
    if expected=='SUPPORTED_REVIEWED_FACTS':
        assert result['answer_origin']=='composed'
        assert result['claim_evidence_links'][0]['ordered_evidence'][0]['element_id']==manifest.element(label)['id']
    else:
        assert result['error_code']=='EVIDENCE_BINDING_FAILED' and result['answer']==''


def _integration_fixture_module(name, filename):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tests' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _reviewed_http_manifest(root, *, source_sha256='a' * 64):
    """Match the explicit document/page identities in reviewed_bundle()."""
    from src.standard_manifest import StandardManifest
    root.mkdir(parents=True, exist_ok=True)
    pages = [{'pdf_index': index, 'printed_label': str(index - 4) if index >= 4 else None}
             for index in range(16)]
    return StandardManifest({
        'document': {'id': 'doc:synthetic', 'sha256': source_sha256, 'pages': pages},
        'sections': [{'id': 'clause:clause_4', 'label': 'Clause 4', 'title': 'Synthetic reviewed entries',
                      'spans': [{'start_pdf_index': 7, 'end_pdf_index': 11}],
                      'normative_status': 'normative', 'verification': {'state': 'verified'}}],
        'figures': [], 'tables': [], 'links': [], 'legacy_aliases': [],
    }, root)


def _coherent_http_query(tmp_path, monkeypatch, *, manifest=None, reviewed=None,
                         response='Synthetic provider simulation.', failure=False):
    """Compose the real HTTP/query/core seams; never start a server or provider.

    The Rag object inherited from load_query is only a synthetic in-memory
    provider simulation. These tests make no model-generation quality claim.
    """
    import re
    from src import standard_manifest
    manifest = manifest or _reviewed_http_manifest(tmp_path / 'manifest')
    monkeypatch.setattr(standard_manifest, 'get_manifest', lambda: manifest)
    from src import citation_checker
    from src.evidence_resolution import qualify_reference_hierarchy, resolve_claim_evidence
    from src.grounded_answer import compose_grounded_answer, project_reviewed_facts
    from src.pre_retrieval import check_early_abstention
    monkeypatch.setattr(citation_checker, 'get_manifest', lambda: manifest)

    query, calls, namespace = load_query(reviewed=reviewed, response=response, failure=failure)
    namespace.update(check_early_abstention=check_early_abstention,
                     get_manifest=lambda: manifest,
                     extract_references=standard_manifest.extract_references,
                     extract_citations=citation_checker.extract_citations,
                     extract_grounded_claims=citation_checker.extract_grounded_claims,
                     extract_reference_records=lambda text:standard_manifest.extract_reference_records(text,manifest=manifest),
        qualify_reference_hierarchy=lambda text,mentions:qualify_reference_hierarchy(text,mentions,manifest=manifest),
                     re=re, Path=Path)

    def actual_compose(question, bundle):
        calls.append('actual_compose')
        return compose_grounded_answer(question, bundle)

    def actual_project(bundle):
        calls.append('actual_project')
        return project_reviewed_facts(bundle)

    def actual_resolve(claims, evidence_context=(), *, reviewed_fact_view=None):
        calls.append('actual_resolve')
        return resolve_claim_evidence(claims, evidence_context, reviewed_fact_view=reviewed_fact_view,
                                      manifest=manifest)

    namespace.update(compose_grounded_answer=actual_compose, project_reviewed_facts=actual_project,
                     resolve_claim_evidence=actual_resolve)
    tree = ast.parse((ROOT / 'src/query.py').read_text(encoding='utf-8'))
    display_functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                         and node.name in {'resolve_multimodal_assets', 'extract_see_also_terms'}]
    exec(compile(ast.Module(body=display_functions, type_ignores=[]), 'actual-query-display', 'exec'), namespace)

    security = _integration_fixture_module('coherent_http_security', 'test_security_boundaries.py')
    web_root = tmp_path / 'http'
    web_root.mkdir()
    fixture = security.web_fixture.__wrapped__(web_root)

    def run_actual_query(question, **kwargs):
        return asyncio.run(query(question, **kwargs))

    monkeypatch.setattr(fixture[0], 'run_query', run_actual_query)

    def post(question, **payload):
        status, headers, body = security.request(fixture, '/api/query', 'POST',
                                                {'query': question, 'engine': 'custom', **payload})
        return status, headers, json.loads(body), body.decode('utf-8')

    return post, calls, namespace, manifest


@pytest.mark.parametrize('question,outcome', [
    ('Define legacy join and its preferred alternatives', 'extractive'),
    ('Which preferred alternative does legacy join mean in my application?', 'clarification'),
])
def test_isolated_http_actual_reviewed_composition_and_binding(tmp_path, monkeypatch, question, outcome):
    source = _integration_fixture_module('coherent_reviewed_bundle', 'test_grounded_answer.py')
    bundle = source.reviewed_bundle()
    post, calls, namespace, _ = _coherent_http_query(tmp_path, monkeypatch, reviewed=bundle)
    namespace['get_rag_instance'] = lambda **kwargs: pytest.fail('Reviewed HTTP route must not initialize a provider')
    namespace['hybrid_retrieve'] = lambda *args, **kwargs: pytest.fail('Reviewed HTTP route must not retrieve again')
    status, headers, result, _ = post(question)
    assert status == 200 and 'application/json' in headers
    assert result['answer_origin'] == 'composed'
    assert result['answer_outcome'] == outcome
    assert result['answer_assessment']['status'] == 'SUPPORTED_REVIEWED_FACTS'
    assert result['claim_evidence_assessment']['status'] == 'SUPPORTED_REVIEWED_FACTS'
    assert result['claim_evidence_assessment']['complete'] is True
    required = result['claim_evidence_assessment']['required_fact_ids']
    assert required == result['claim_evidence_assessment']['observed_fact_ids']
    assert len(required) == len(result['grounded_claims']) == len(result['claim_evidence_links']) == 3
    assert 'target alpha' in result['answer'] and 'target beta' in result['answer']
    assert ('Please provide' in result['answer']) is (outcome == 'clarification')
    assert result['retrieved_evidence'] == [bundle]
    assert calls == ['lookup', 'actual_compose', 'actual_project', 'actual_resolve']
    for link in result['claim_evidence_links']:
        assert link['reference_status'] == 'exact'
        assert link['binding_status'] == 'matched'
        assert link['asset_status'] == 'source_only'
        assert link['support_status'] == 'SUPPORTED_REVIEWED_FACTS'
        assert link['selected_evidence_ids'] == []
        native = link['ordered_evidence'][0]
        assert native['element_id'] == 'clause:clause_4'
        assert native['source_anchors'][0]['source_id'] == 'doc:synthetic'
        assert native['source_anchors'][0]['source_sha256'] == 'a' * 64
        proof = next(item for item in link['binding_evidence'] if item['role'] == 'expected_reviewed')
        assert proof['source_bindings'][0]['binding_sha256']
        assert 'source_text' not in proof['source_bindings'][0]


def test_isolated_http_actual_native_digest_mismatch_is_source_free_503(tmp_path, monkeypatch):
    source = _integration_fixture_module('coherent_mismatch_bundle', 'test_grounded_answer.py')
    bundle = source.reviewed_bundle()
    manifest = _reviewed_http_manifest(tmp_path / 'mismatched_manifest', source_sha256='b' * 64)
    post, calls, namespace, _ = _coherent_http_query(tmp_path, monkeypatch, manifest=manifest, reviewed=bundle)
    namespace['get_rag_instance'] = lambda **kwargs: pytest.fail('Binding failure cannot fall back to a provider')
    status, _, result, encoded = post('Define legacy join')
    assert status == 503
    assert result['error_code'] == 'EVIDENCE_BINDING_FAILED'
    assert result['answer_outcome'] == 'error' and result['answer'] == ''
    assert result['answer_assessment']['validated'] is False
    assert result['grounded_claims'] == result['retrieved_evidence'] == result['claim_evidence_links'] == []
    assert result['claim_evidence_assessment']['status'] == 'INSUFFICIENT_EVIDENCE'
    assert result['claim_evidence_assessment']['complete'] is False
    assert 'legacy join. A nonstandard term' not in encoded
    assert 'synthetic elongated joint' not in encoded
    assert str(manifest.root) not in encoded
    assert calls == ['lookup', 'actual_compose', 'actual_project', 'actual_resolve']


@pytest.mark.parametrize('case,status,code', [
    ('scope', 200, None),
    ('provider_unconfigured', 503, 'MODEL_PROVIDER_UNCONFIGURED'),
    ('retrieval_missing', 503, 'RETRIEVAL_INDEX_MISSING'),
    ('registry_invalid', 503, 'TERMINOLOGY_REGISTRY_INVALID'),
    ('synthetic_provider_failure', 502, 'GENERATION_FAILED'),
])
def test_isolated_http_actual_scope_and_execution_prerequisites(tmp_path, monkeypatch, case, status, code):
    post, calls, namespace, _ = _coherent_http_query(tmp_path, monkeypatch, failure=case == 'synthetic_provider_failure')
    if case == 'retrieval_missing':
        def missing(*args, **kwargs):
            raise namespace['ContextualIndexMissingError']('PRIVATE synthetic index detail')
        namespace['hybrid_retrieve'] = missing
    elif case == 'registry_invalid':
        def invalid(question):
            raise namespace['TerminologyRegistryError']('PRIVATE synthetic registry detail')
        namespace['get_terminology_evidence'] = invalid
    question = 'What are the acceptance criteria?' if case == 'scope' else 'Unrelated synthetic request'
    payload = {'api_key': 'synthetic-test-key'} if case in {'retrieval_missing', 'synthetic_provider_failure'} else {}
    actual_status, _, result, encoded = post(question, **payload)
    assert actual_status == status
    assert result.get('error_code') == code
    assert result['claim_evidence_links'] == []
    assert result['claim_evidence_assessment']['status'] == 'UNASSESSED'
    assert result['claim_evidence_assessment']['complete'] is False
    assert 'PRIVATE' not in encoded and 'synthetic-test-key' not in encoded
    assert 'actual_resolve' not in calls and 'actual_project' not in calls
    if case == 'scope':
        assert result['answer_outcome'] == 'abstention'
        assert result['answer_assessment']['status'] == 'TRUTHFUL_ABSTENTION'
        assert calls == []
    else:
        assert result['answer_outcome'] == 'error' and result['answer'] == ''
        assert result['answer_assessment']['status'] == 'UNASSESSED'
    if case == 'synthetic_provider_failure':
        # This is an in-memory Rag simulation, not a live provider invocation.
        assert calls.count('initialize') == 1
        assert len([item for item in calls if isinstance(item, tuple) and item[0] == 'generate']) == 1
    else:
        assert 'initialize' not in calls
        assert not any(isinstance(item, tuple) and item[0] == 'generate' for item in calls)


def test_isolated_http_generated_fixture_retains_partial_assets_and_distinct_source_identities(tmp_path, monkeypatch):
    fixture = _integration_fixture_module('coherent_visual_manifest', 'test_citation_evidence_resolution.py')
    manifest = fixture.FakeManifest(tmp_path / 'visual_manifest')
    (manifest.root / 'parsed/figures/continuation.png').unlink()
    response = ('- A synthetic diagram assertion cites Figures X2 and X1.\n'
                '- A synthetic source-only assertion cites Table Q1 and Figure X2.')
    post, calls, _, _ = _coherent_http_query(tmp_path, monkeypatch, manifest=manifest, response=response)
    status, _, result, _ = post('Describe the two synthetic citations', api_key='synthetic-test-key')
    assert status == 200
    assert result['answer'] == response and result['answer_origin'] == 'generated', json.dumps(
        result.get('citation_diagnostics', {}), ensure_ascii=False)
    assert result['answer_assessment']['status'] == 'UNASSESSED'
    assert result['claim_evidence_assessment']['status'] == 'UNASSESSED'
    assert result['claim_evidence_assessment']['complete'] is False
    links = result['claim_evidence_links']
    assert [link['claim_id'] for link in links] == ['claim:1', 'claim:2']
    assert all(link['support_status'] == 'UNASSESSED' and link['binding_status'] == 'unavailable' for link in links)
    assert all(link['selected_evidence_ids'] == [] for link in links)
    first = links[0]['ordered_evidence']
    assert [item['element_id'] for item in first] == ['figure:figure_x2', 'figure:figure_x1']
    assert [item['asset_status'] for item in first] == ['complete', 'missing']
    assert [[Path(asset['path']).name for asset in item['assets']] for item in first] == [['shared.png'], ['shared.png']]
    assert first[0]['assets'][0]['path'] == first[1]['assets'][0]['path']
    assert first[0]['source_anchors'][0]['element_id'] != first[1]['source_anchors'][0]['element_id']
    assert [asset['source_anchor_orders'] for asset in first[1]['declared_assets']] == [[2], [0, 1]]
    assert links[0]['asset_status'] == 'missing'
    second = links[1]['ordered_evidence']
    assert [item['element_id'] for item in second] == ['table:table_q1', 'figure:figure_x2', 'figure:figure_x1']
    assert second[0]['relationship'] == 'direct' and second[0]['asset_status'] == 'source_only'
    assert second[0]['assets'] == [] and second[0]['source_anchors']
    assert second[2]['relationship'] == 'navigation_candidate' and second[2]['asset_status'] == 'missing'
    assert links[1]['asset_status'] == 'complete'
    # Display retains healthy required paths and exposes the unavailable member.
    figures = result['resolved_figures']
    assert [item['figure_id'] for item in figures] == ['Figure X1', 'Figure X2']
    assert [item['asset_status'] for item in figures] == ['missing', 'complete']
    assert [[Path(path).name for path in item['image_paths']] for item in figures] == [['shared.png'], ['shared.png']]
    assert all(item['image_path'] == item['image_paths'][0] for item in figures)
    assert figures[0]['source_anchors'] == manifest.source_anchors('Figure X1')
    assert figures[1]['source_anchors'] == manifest.source_anchors('Figure X2')
    tables = result['resolved_tables']
    assert len(tables) == 1 and tables[0]['table_id'] == 'Table Q1'
    assert tables[0]['asset_status'] == 'source_only'
    assert tables[0]['table_path'] is None and tables[0]['image_paths'] == []
    assert tables[0]['source_anchors'] == manifest.source_anchors('Table Q1')
    assert calls.count('actual_resolve') == 1 and 'actual_project' not in calls
    assert calls.count('initialize') == 1
    assert len([item for item in calls if isinstance(item, tuple) and item[0] == 'generate']) == 1


def _actual_navigation_route(manifest):
    """Run actual navigation/metadata functions over an in-memory graph fake."""
    from src.standard_manifest import ManifestError
    assessment = _integration_fixture_module('coherent_navigation_graph', 'test_answer_assessment.py')
    namespace, connections = assessment.fixture_namespace(
        nodes=[('onto:synthetic', 'synthetic navigation', 'Concept', 'standard', 'Synthetic graph hint')],
        bridges=[('ILLUSTRATED_BY', 'figure_reference', 'figure:synthetic', 'Figure',
                  'Figure X1', '999', 'untrusted-graph-path.png', 'Synthetic graph preview')])
    namespace.update(get_manifest=lambda: manifest, FIGURE_INSPECTORS={}, ManifestError=ManifestError, Path=Path)
    assessment.load_definitions('epistemic_verifier.py', {'_decision_status'}, namespace)
    assessment.load_definitions('answer_routes.py',
                                {'EvidenceItem', 'AnswerRoute', '_apply_source_metadata',
                                 '_clean_term_for_fts', 'resolve_answer_route'}, namespace)
    return namespace['resolve_answer_route'], connections


@pytest.mark.parametrize('mutation,asset_status', [('missing', 'missing'), ('corrupt', 'corrupt')])
def test_isolated_http_actual_navigation_asset_failure_preserves_claim_diagnostics(tmp_path, monkeypatch, mutation, asset_status):
    source = _integration_fixture_module('coherent_navigation_manifest', 'test_citation_evidence_resolution.py')
    manifest = source.FakeManifest(tmp_path / 'navigation_manifest')
    continuation = manifest.root / 'parsed/figures/continuation.png'
    if mutation == 'missing':
        continuation.unlink()
    else:
        continuation.write_text('Synthetic corrupt navigation bytes', encoding='utf-8')
    response = '- A synthetic navigation assertion cites Figure X1.'
    post, calls, namespace, _ = _coherent_http_query(tmp_path, monkeypatch, manifest=manifest, response=response)
    navigation, simulated_connections = _actual_navigation_route(manifest)
    namespace['resolve_answer_route'] = navigation
    status, _, result, encoded = post('Describe synthetic navigation in Figure X1', api_key='synthetic-test-key')
    assert status == 200
    assert result['answer'] == response and result['answer_origin'] == 'generated'
    assert result['answer_assessment']['status'] == 'UNASSESSED'
    assert len(simulated_connections) == 1  # A fake connection object, never sqlite3.connect.
    link = result['claim_evidence_links'][0]
    assert link['reference_status'] == 'exact' and link['asset_status'] == asset_status
    assert link['support_status'] == 'UNASSESSED'
    assert [Path(asset['path']).name for asset in link['ordered_evidence'][0]['assets']] == ['shared.png']
    group = result['answer_route']['evidence_group']
    item = next(item for item in group if item['element_id'] == 'Figure X1')
    assert item['metadata']['source_location_verification'] == 'verified'
    assert item['metadata']['source_anchors'] == manifest.source_anchors('Figure X1')
    assert item['metadata']['asset_status'] == asset_status
    assert [asset['status'] for asset in item['metadata']['assets']] == ['complete', asset_status]
    assert [Path(path).name for path in item['metadata']['image_paths']] == ['shared.png']
    assert Path(item['file_path']).name == 'shared.png'
    assert item['page'] == '12-14'
    assert 'untrusted-graph-path.png' not in encoded
    assert calls.count('actual_resolve') == 1


@pytest.mark.parametrize('reference,expected,bulleted', [
    ('Figure X120', 'unknown', True),
    ('Figures X1-X120', 'unknown', True),
    ('Figure X9', 'group', True),
    ('Table Q3', 'unverified', True),
    ('Figure X1(A)', 'unsupported_qualifier', True),
    ('Fig.X120', 'unknown', False),
    ('p. 999', 'unknown', False),
])
def test_isolated_http_generated_unresolved_reference_is_withheld(tmp_path, monkeypatch, reference, expected, bulleted):
    source = _integration_fixture_module('coherent_rejected_manifest', 'test_citation_evidence_resolution.py')
    manifest = source.FakeManifest(tmp_path / 'rejected_manifest')
    assertion = 'A synthetic unsupported assertion cites ' + reference + '.'
    response = '- ' + assertion if bulleted else assertion
    post, _, _, _ = _coherent_http_query(tmp_path, monkeypatch, manifest=manifest, response=response)
    status, _, result, _ = post('Describe a synthetic citation', api_key='synthetic-test-key')
    assert status == 200
    assert result['answer_outcome'] == 'insufficient_evidence'
    assert result['answer_origin'] == 'none'
    assert assertion not in result['answer']
    assert result['grounded_claims'] == []
    assert result['answer_assessment']['status'] == 'INSUFFICIENT_EVIDENCE'
    assert result['answer_assessment']['validated'] is False
    assert result['answer_assessment']['citation_support'] == 'invalid'
    assert result['claim_evidence_assessment']['answer_withheld'] is True
    assert result['claim_evidence_assessment']['complete'] is False
    diagnostics = result['citation_diagnostics']
    assert 'unresolved_generated_reference' in diagnostics['diagnostics']
    records = diagnostics['references']
    assert expected in [record['resolution']['status'] for record in records]
    assert any(reference.casefold() in record['raw'].casefold() for record in records)
    assert all(link['support_status'] == 'UNASSESSED' for link in result['claim_evidence_links'])
    if bulleted:
        assert result['claim_evidence_links']
    else:
        assert result['claim_evidence_links'] == []  # Full-response parsing still enforces the citation boundary.


@pytest.mark.parametrize('bulleted', [True, False])
def test_isolated_http_generated_wrong_parent_is_withheld_including_plain_prose(tmp_path, monkeypatch, bulleted):
    source = _integration_fixture_module('coherent_parent_manifest', 'test_citation_evidence_resolution.py')
    manifest = source.FakeManifest(tmp_path / 'parent_manifest')
    assertion = 'A synthetic unsupported assertion cites Clause 5, Figure X1.'
    response = '- ' + assertion if bulleted else assertion
    post, _, _, _ = _coherent_http_query(tmp_path, monkeypatch, manifest=manifest, response=response)
    status, _, result, _ = post('Describe a synthetic citation', api_key='synthetic-test-key')
    assert status == 200
    assert result['answer_outcome'] == 'insufficient_evidence' and result['answer_origin'] == 'none'
    assert assertion not in result['answer'] and result['grounded_claims'] == []
    assert result['answer_assessment']['status'] == 'INSUFFICIENT_EVIDENCE'
    assert result['claim_evidence_assessment']['answer_withheld'] is True
    assert 'parent_qualifier_mismatch' in result['citation_diagnostics']['diagnostics']
    assert [record['resolution']['status'] for record in result['citation_diagnostics']['references']] == ['exact', 'exact']
    assert all(link['support_status'] != 'SUPPORTED_REVIEWED_FACTS' for link in result['claim_evidence_links'])


@pytest.mark.parametrize('response', [
    'A synthetic plain response has no source citation.',
    '- A synthetic exact assertion cites Figure X2.',
    'A synthetic exact shorthand assertion cites Fig.X2.',
    'A synthetic exact page assertion cites Figure X1, p. 12.',
    'A synthetic valid printed page assertion cites p. 12.',
    '- First assertion cites Figure X1\n- Another assertion cites Figure X2',
    '- Figure X1\n- Figure X2',
])
def test_isolated_http_generated_exact_and_plain_responses_remain_unassessed(tmp_path, monkeypatch, response):
    source = _integration_fixture_module('coherent_valid_manifest', 'test_citation_evidence_resolution.py')
    manifest = source.FakeManifest(tmp_path / 'valid_manifest')
    post, _, _, _ = _coherent_http_query(tmp_path, monkeypatch, manifest=manifest, response=response)
    status, _, result, _ = post('Describe a synthetic citation', api_key='synthetic-test-key')
    assert status == 200
    assert result['answer'] == response
    assert result['answer_outcome'] == 'generated' and result['answer_origin'] == 'generated'
    assert result['answer_assessment']['status'] == 'UNASSESSED'
    assert result['answer_assessment']['validated'] is False
    assert not result['claim_evidence_assessment'].get('answer_withheld', False)
    assert all(link['support_status'] == 'UNASSESSED' for link in result['claim_evidence_links'])


def test_isolated_http_source_only_table_survives_without_extracted_bullet_claims(tmp_path, monkeypatch):
    source = _integration_fixture_module('coherent_source_table_manifest', 'test_citation_evidence_resolution.py')
    manifest = source.FakeManifest(tmp_path / 'source_table_manifest')
    response = 'Synthetic source-only table navigation for Table Q1.'
    post, _, _, _ = _coherent_http_query(tmp_path, monkeypatch, manifest=manifest, response=response)
    status, _, result, _ = post('Show Table Q1', api_key='synthetic-test-key')
    assert status == 200 and result['answer'] == response
    assert result['grounded_claims'] == result['claim_evidence_links'] == []
    assert result['answer_assessment']['status'] == 'UNASSESSED'
    table = next(item for item in result['resolved_tables'] if item['table_id'] == 'Table Q1')
    assert table['table_path'] is None and table['image_paths'] == []
    assert table['source_anchors'] == manifest.source_anchors('Table Q1')


@pytest.mark.parametrize('punctuation', ['.', ''])
def test_multiline_reference_parser_does_not_consume_the_next_bullet(tmp_path, punctuation):
    from src.standard_manifest import extract_reference_records
    source = _integration_fixture_module('coherent_multiline_manifest', 'test_citation_evidence_resolution.py')
    manifest = source.FakeManifest(tmp_path / 'multiline_manifest')
    response = ('- A synthetic diagram assertion cites Figures X2 and X1' + punctuation + '\n'
                '- A synthetic source-only assertion cites Table Q1 and Figure X2.')
    records = extract_reference_records(response, manifest=manifest)
    assert [record['resolution']['status'] for record in records] == ['exact', 'exact', 'exact'], json.dumps(records)
    assert [record['resolution']['target_ids'] for record in records] == [
        ['figure:figure_x2', 'figure:figure_x1'], ['table:table_q1'], ['figure:figure_x2']]
    assert all('\n' not in record['raw'] for record in records)


def test_explicit_range_continuation_remains_distinct_from_a_markdown_bullet(tmp_path):
    from src.standard_manifest import extract_reference_records
    source = _integration_fixture_module('coherent_range_manifest', 'test_citation_evidence_resolution.py')
    manifest = source.FakeManifest(tmp_path / 'range_manifest')
    valid, = extract_reference_records('Figures X1\n-X2', manifest=manifest)
    assert valid['resolution']['status'] == 'exact'
    assert valid['resolution']['target_ids'] == ['figure:figure_x1', 'figure:figure_x2']
    malformed, = extract_reference_records('Figures X1. - X2', manifest=manifest)
    assert malformed['resolution']['status'] == 'unknown'
    unknown, = extract_reference_records('Figures X1\n- X120', manifest=manifest)
    assert unknown['resolution']['status'] == 'unknown'


@pytest.mark.parametrize('page', ['17', '999'])
@pytest.mark.parametrize('bulleted', [True, False])
def test_isolated_http_generated_attached_page_must_belong_to_the_cited_element(tmp_path, monkeypatch, page, bulleted):
    source = _integration_fixture_module('coherent_page_manifest', 'test_citation_evidence_resolution.py')
    manifest = source.FakeManifest(tmp_path / 'page_manifest')
    assertion = 'A synthetic unsupported assertion cites Figure X1, p. ' + page + '.'
    response = '- ' + assertion if bulleted else assertion
    post, _, _, _ = _coherent_http_query(tmp_path, monkeypatch, manifest=manifest, response=response)
    status, _, result, _ = post('Describe a synthetic citation', api_key='synthetic-test-key')
    assert status == 200
    assert result['answer_outcome'] == 'insufficient_evidence' and result['answer_origin'] == 'none'
    assert assertion not in result['answer'] and result['grounded_claims'] == []
    assert result['answer_assessment']['status'] == 'INSUFFICIENT_EVIDENCE'
    assert result['answer_assessment']['validated'] is False
    assert result['claim_evidence_assessment']['answer_withheld'] is True
    diagnostics = result['citation_diagnostics']
    assert 'page_qualifier_mismatch' in diagnostics['diagnostics']
    record = next(record for record in diagnostics['references'] if record['kind'] == 'figure')
    assert record['resolution']['status'] == 'exact'
    assert record['resolution']['target_ids'] == ['figure:figure_x1']
    assert page in record['qualifiers']['page']
    if bulleted:
        assert result['claim_evidence_links'][0]['binding_status'] == 'mismatched'
        assert 'page_qualifier_mismatch' in result['claim_evidence_links'][0]['diagnostics']
    else:
        assert result['claim_evidence_links'] == []


@pytest.mark.parametrize('mutation', ['missing', 'corrupt'])
def test_isolated_http_source_only_table_survives_optional_companion_failure(tmp_path, monkeypatch, mutation):
    source = _integration_fixture_module('coherent_optional_table_manifest', 'test_citation_evidence_resolution.py')
    manifest = source.FakeManifest(tmp_path / 'optional_table_manifest')
    continuation = manifest.root / 'parsed/figures/continuation.png'
    if mutation == 'missing':
        continuation.unlink()
    else:
        continuation.write_text('Synthetic corrupt optional companion bytes', encoding='utf-8')
    response = 'Synthetic source-only table navigation for Table Q1.'
    post, _, _, _ = _coherent_http_query(tmp_path, monkeypatch, manifest=manifest, response=response)
    status, _, result, _ = post('Show Table Q1', api_key='synthetic-test-key')
    assert status == 200 and result['answer'] == response
    assert result['answer_outcome'] == 'generated' and result['answer_origin'] == 'generated'
    assert result['grounded_claims'] == result['claim_evidence_links'] == []
    assert result['answer_assessment']['status'] == 'UNASSESSED'
    table = next(item for item in result['resolved_tables'] if item['table_id'] == 'Table Q1')
    assert table['table_path'] is None and table['image_paths'] == []
    assert table['source_anchors'] == manifest.source_anchors('Table Q1')
