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
    ns=dict(Optional=Optional,DEFAULT_ENGINE='custom',CUSTOM_API_KEY='',DEEPSEEK_API_KEY='',GEMINI_API_KEY='',
        STORAGE_DIR=Path('unused'),check_early_abstention=lambda q:gate,
        get_terminology_evidence=lookup,compose_grounded_answer=compose,
        hybrid_retrieve=lambda *a,**k:[{'id':'synthetic-chunk','content':'Synthetic source'}],
        ContextualIndexMissingError=Missing,TerminologyRegistryError=Invalid,
        get_rag_instance=lambda **kw:Rag(),QueryParam=lambda **kw:kw,
        extract_citations=lambda text:{},extract_grounded_claims=lambda text:[],
        resolve_multimodal_assets=lambda text:([],[]),extract_see_also_terms=lambda text:[],
        verify_epistemic_provenance=lambda *a,**kw:{'epistemic_status':kw.get('decision',{}).get('status','UNASSESSED'),'provenance_score':None},
        resolve_answer_route=lambda *a,**kw:SimpleNamespace(to_dict=lambda:{'status':'EVIDENCE_LINKS_FOUND'}),
        hashlib=hashlib,json=json,time=time)
    tree=ast.parse((ROOT/'src/query.py').read_text(encoding='utf-8'))
    # Include the shared response helper if introduced by this bounded change.
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in {'async_query','_query_failure','_reviewed_trace','_scope_decision'}]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-query','exec'),ns)
    return ns['async_query'],calls,ns

def test_composed_route_needs_no_key_rag_database_or_second_retrieval():
    answer={'answer':'Reviewed synthetic answer.','citations':{},'grounded_claims':[],
            'answer_origin':'composed','answer_outcome':'extractive',
            'answer_assessment':{'status':'SUPPORTED_REVIEWED_FACTS','validated':True}}
    q,calls,ns=load_query(reviewed={'id':'terminology:synthetic','terminology_resolution':{}},composed=answer)
    ns['hybrid_retrieve']=lambda *a,**k:pytest.fail('Composed route must not add unrestricted retrieval')
    ns['get_rag_instance']=lambda *a,**k:pytest.fail('Composed route must not load a model')
    result=asyncio.run(q('Define synthetic legacy term',engine='custom'))
    assert result['answer']==answer['answer']
    assert result['answer_origin']=='composed'
    assert result['epistemic_trace']['provenance_score'] is None
    assert calls==['lookup','compose']

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

@pytest.mark.parametrize('code,expected', [('MODEL_PROVIDER_UNCONFIGURED',503),('GENERATION_FAILED',502)])
def test_http_reports_structured_execution_failure_without_success_status(code,expected,tmp_path):
    import importlib.util
    spec=importlib.util.spec_from_file_location('grounding_http_fixture',ROOT/'tests/test_security_boundaries.py')
    fixture_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture_module)
    fixture=fixture_module.web_fixture.__wrapped__(tmp_path)
    fixture[0].run_query=lambda *args,**kwargs:{'answer':'','error':'Answer unavailable.','error_code':code,'answer_outcome':'error'}
    status,_,body=fixture_module.request(fixture,'/api/query','POST',{'query':'Synthetic request'})
    assert status==expected
    assert json.loads(body)['error_code']==code
