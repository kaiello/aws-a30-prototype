"""Bounded offline reader/hybrid evaluation against frozen existing questions.

This is not a full production LightRAG or independent answer-accuracy benchmark.
The reader lane uses the same fixed resident chunk pool before/after. Optional
answers use an installed LOCAL Ollama model, never a cloud model or app API.
All results go to an explicit output directory outside the repository.
"""
import argparse
import asyncio
import datetime
from importlib.metadata import version
import subprocess
from collections import Counter
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
import statistics
import sys
import time
from types import SimpleNamespace
import urllib.request

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_crosswalk(manifest):
    """Use explicit parsed metadata fields, never filenames/content mentions."""
    result = {}
    for relative, field in [('parsed/figures/annex_b_figures.jsonl', 'figure_id'),
                            ('parsed/tables/annex_a_tables.jsonl', 'table_id')]:
        for line in (ROOT / relative).read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            label = row.get(field, '').replace('_', ' ')
            resolution = manifest.resolve(label)
            if resolution['status'] != 'exact':
                continue
            label = resolution['labels'][0]
            if field == 'figure_id' and row.get('pdf_page') not in {a['pdf_index'] for a in manifest.anchors(label)}:
                continue
            result[row['chunk_id']] = {'label': label, 'mapping_source': relative + ':' + field}
    return result


def metrics(rows, lane):
    scored = [r for r in rows if r.get('target_element')]
    ranks = [next((i + 1 for i, c in enumerate(r[lane]['candidates'])
                   if c.get('source_element') == r['target_element']), None) for r in scored]
    return {'denominator': len(scored), 'hit_at_1': sum(x == 1 for x in ranks),
            'hit_at_5': sum(x is not None and x <= 5 for x in ranks),
            'hit_at_10': sum(x is not None and x <= 10 for x in ranks),
            'mrr_at_10': sum(1 / x for x in ranks if x is not None) / len(scored) if scored else None,
            'misses_at_10': [r['id'] for r, rank in zip(scored, ranks) if rank is None],
            'mean_ms': statistics.mean(r[lane]['latency_ms'] for r in rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--answers-model', default='', help='Installed local Ollama model; empty skips answers')
    parser.add_argument('--answer-limit', type=int, default=10, help='Predeclared first N positive questions, each before/after')
    args = parser.parse_args()
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    output = args.output_dir.resolve()
    if output.is_relative_to(ROOT) or output.exists():
        raise ValueError('Use a fresh output directory outside the repository')
    output.mkdir(parents=True)
    import numpy as np
    from lightrag.kg.nano_vector_db_impl import NanoVectorDBStorage
    from lightrag.utils import pick_by_vector_similarity
    from src import hybrid_retriever as hybrid
    from src.pre_retrieval import check_early_abstention
    from src.citation_checker import extract_citations, verify_response
    from src.standard_manifest import get_manifest
    from src.vector_reader_compat import install_vector_reader, decode_vector

    log_handler = logging.FileHandler(output / 'reader.log', encoding='utf-8')
    logging.getLogger('lightrag').addHandler(log_handler)
    benchmark_path = ROOT / 'eval/gold_benchmark.json'
    benchmark = json.loads(benchmark_path.read_text(encoding='utf-8'))
    positive = [q for q in benchmark if not q['must_abstain']]
    manifest = get_manifest()
    crosswalk = source_crosswalk(manifest)
    store_path = ROOT / 'storage/vdb_chunks.json'
    data = json.loads(store_path.read_text(encoding='utf-8'))
    dimension = data['embedding_dim']
    resident = data['data']
    resident_by_id = {r['__id__']: r for r in resident}
    for row in resident:
        decode_vector(row['vector'], dimension)
    ids = list(resident_by_id)
    resident_arrays = {r['__id__']: np.array(decode_vector(r['vector'], dimension), dtype=np.float32) for r in resident}
    resident_matrix = np.array([resident_arrays[cid] for cid in ids])
    resident_norms = np.linalg.norm(resident_matrix, axis=1)
    snapshots = {str(p.relative_to(ROOT)): digest(p) for p in [ROOT / 'eval/vector_compat_evaluation.py',
                 ROOT / 'src/vector_reader_compat.py', ROOT / 'src/indexer.py', ROOT / 'src/hybrid_retriever.py',
                 ROOT / 'config/aws_a30_2020_manifest.json', ROOT / 'config/aws_a30_2020_manifest.receipt.json',
                 ROOT / 'parsed/figures/annex_b_figures.jsonl', ROOT / 'parsed/tables/annex_a_tables.jsonl', store_path,
                 ROOT / 'storage/vdb_chunks_contextual.json', ROOT / 'storage/dual_layer_registry.db',
                 ROOT / 'storage/kv_store_text_chunks.json', benchmark_path]}
    # Real SQLite SELECT paths, with a read-only connection boundary.
    original_connect = sqlite3.connect
    def readonly_connect(path, *a, **kw):
        if Path(path).resolve() != (ROOT / 'storage/dual_layer_registry.db').resolve():
            raise AssertionError('Unexpected database requested')
        return original_connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
    sqlite3.connect = readonly_connect
    started = time.perf_counter()
    model = hybrid.get_dense_model()
    model_load_ms = (time.perf_counter() - started) * 1000
    if model.get_sentence_embedding_dimension() != dimension:
        raise ValueError('Existing embedding model/index dimension mismatch')
    reranker = hybrid.get_reranker_model()

    def storage():
        # Native reader with a read-only resident snapshot; no constructor writes,
        # ingestion, pending embedding, model client or external storage connection.
        instance = object.__new__(NanoVectorDBStorage)
        instance.embedding_func = SimpleNamespace(embedding_dim=dimension)
        instance._storage_lock = asyncio.Lock()
        instance._pending_upserts = {}
        instance._pending_deletes = set()
        instance._unsaved_upserts = {}
        instance._unsaved_deletes = {}
        async def client():
            return SimpleNamespace(get=lambda requested: [r for r in resident if r['__id__'] in requested])
        instance._get_client = client
        return instance
    native, fixed = storage(), storage()
    install_vector_reader(fixed)
    reader_errors = {'before': [], 'after': []}
    def observe_reader(instance, lane):
        read = instance.get_vectors_by_ids
        async def observed(ids):
            try:
                return await read(ids)
            except Exception as exc:
                reader_errors[lane].append(type(exc).__name__)
                raise
        instance.get_vectors_by_ids = observed
    observe_reader(native, 'before')
    observe_reader(fixed, 'after')
    def candidate(row, score=None):
        doc = row.get('full_doc_id', '')
        return {'id': row.get('__id__', row.get('id')), 'full_doc_id': doc,
                'source_element': crosswalk.get(doc, {}).get('label'),
                'mapping_source': crosswalk.get(doc, {}).get('mapping_source'), 'score': score}
    results = []
    vectors = {}
    for index, item in enumerate(positive):
        query = item['query']
        start = time.perf_counter()
        vector = model.encode([query], normalize_embeddings=True)[0]
        embedding_ms = (time.perf_counter() - start) * 1000
        vectors[item['id']] = vector
        row = {'id': item['id'], 'modality': item['modality'], 'query': query,
               'gold_citation': item['gold_citation'], 'embedding_ms': embedding_ms}
        gold = item['gold_citation']['element_id']
        canonical = manifest.resolve(gold)
        declared = item['gold_citation']['element_type'] in {'figure', 'table', 'cross_modal'}
        row['target_element'] = canonical['labels'][0] if declared and canonical['status'] == 'exact' else gold if declared else None
        row['target_resolution'] = canonical['status'] if declared else 'text target ungraded'
        row['resident_target_candidate_ids'] = [cid for cid, r in resident_by_id.items() if crosswalk.get(r.get('full_doc_id'), {}).get('label') == row['target_element']] if declared else []
        row['target_source_anchors'] = manifest.source_anchors(gold) if row['target_element'] else []
        for name, instance in [('before', native), ('after', fixed)]:
            start = time.perf_counter()
            errors_before = len(reader_errors[name])
            selected = asyncio.run(pick_by_vector_similarity(query, None, instance, 10,
                [{'sorted_chunks': ids}], None, query_embedding=vector))
            elapsed = (time.perf_counter() - start) * 1000
            scored = []
            for cid in selected:
                record = resident_by_id[cid]
                values = resident_arrays[cid]
                score = float(np.dot(vector, values) / (np.linalg.norm(vector) * np.linalg.norm(values)))
                scored.append(candidate(record, score))
            row[name] = {'candidates': scored, 'latency_ms': elapsed,
                         'fallback': len(reader_errors[name]) > errors_before,
                         'reader_errors': reader_errors[name][errors_before:]}
            if name == 'after':
                oracle_scores = resident_matrix @ vector / (resident_norms * np.linalg.norm(vector))
                expected_scores = sorted(oracle_scores, reverse=True)[:10]
                assert np.allclose([c['score'] for c in scored], expected_scores, rtol=1e-5, atol=1e-6), item['id']
                row[name]['cosine_rank_order_verified'] = True
        start = time.perf_counter()
        hits = hybrid.hybrid_retrieve(query, top_k=10)
        row['hybrid'] = {'cross_encoder_scored_candidates': sum('cross_encoder_score' in hit for hit in hits), 'candidates': [dict(candidate(c, c.get('cross_encoder_score', c.get('rrf_score'))),
                    raw_score=c.get('score'), rrf_score=c.get('rrf_score'), cross_encoder_score=c.get('cross_encoder_score')) for c in hits],
                    'latency_ms': (time.perf_counter() - start) * 1000}
        results.append(row)
        (output / 'retrieval-progress.json').write_text(json.dumps(results, indent=2) + '\n')
        print(f'Retrieval {index+1}/{len(positive)} {item["id"]}', flush=True)

    gates = [{'id': q['id'], 'must_abstain': q['must_abstain'], 'abstained': check_early_abstention(q['query']) is not None} for q in benchmark]
    answers = []
    if args.answers_model:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open('http://127.0.0.1:11434/api/tags', timeout=10) as response:
            models = json.load(response)['models']
        local_model = next(m for m in models if m['name'] == args.answers_model)
        if local_model.get('remote_host') or local_model.get('remote_model') or local_model['details'].get('format') != 'gguf':
            raise ValueError('Answer evaluation requires an already installed local GGUF model')
        for row in results[:max(0, args.answer_limit)]:
            item = next(q for q in benchmark if q['id'] == row['id'])
            for lane in ['before', 'after']:
                selected = row[lane]['candidates'][:5]
                context = '\n\n'.join('[' + c['id'] + ' | ' + c['full_doc_id'] + ']\n' + resident_by_id[c['id']]['content'] for c in selected)
                prompt = 'Use only this retrieved evidence. Cite its IDs. If insufficient, explicitly abstain. Do not invent citations.\nQUESTION: ' + row['query'] + '\nEVIDENCE:\n' + context
                request = {'model': args.answers_model, 'messages': [{'role': 'user', 'content': prompt}], 'stream': False,
                           'options': {'temperature': 0, 'seed': 0, 'num_predict': 384, 'num_ctx': 8192}}
                start = time.perf_counter()
                req = urllib.request.Request('http://127.0.0.1:11434/api/chat', data=json.dumps(request).encode(), headers={'Content-Type': 'application/json'})
                with opener.open(req, timeout=180) as response:
                    generated = json.load(response)
                request_ms = (time.perf_counter() - start) * 1000
                text = generated['message']['content']
                citations = extract_citations(text)
                answers.append({'id': row['id'], 'lane': lane, 'model': args.answers_model, 'model_digest': local_model['digest'],
                    'answer': text, 'candidate_ids': [c['id'] for c in selected], 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                    'request_latency_ms': request_ms, 'cached_answer': False, 'options': request['options'],
                    'done_reason': generated.get('done_reason'), 'done': generated.get('done'),
                    'server_load_duration_ns': generated.get('load_duration'), 'server_eval_duration_ns': generated.get('eval_duration'),
                    'server_prompt_eval_duration_ns': generated.get('prompt_eval_duration'), 'prompt_characters': len(prompt),
                    'eval_count': generated.get('eval_count'), 'prompt_eval_count': generated.get('prompt_eval_count'),
                    'citations': citations, 'legacy_heuristic': verify_response(item, text),
                    'factual_correctness': 'ungraded; no independent entailment/source adjudication'})
                (output / 'answers.json').write_text(json.dumps(answers, indent=2) + '\n')
                print(f'Local answer {row["id"]} {lane}', flush=True)
    unchanged = {name: digest(ROOT / name) == value for name, value in snapshots.items()}
    assert all(unchanged.values()), unchanged
    assert sum(bool(r['target_element']) for r in results) == 28, 'Frozen target denominator changed'
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty_diff = subprocess.check_output(['git', 'diff', '--binary', 'HEAD', '--', 'src', 'eval', 'tests', 'docs', 'README.md'], cwd=ROOT)
        diff_hash = hashlib.sha256(dirty_diff).hexdigest()
    except (subprocess.CalledProcessError, OSError):
        commit, diff_hash = 'unavailable', None
    report = {'started_utc': started_utc, 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'commit': commit, 'tracked_dirty_diff_sha256': diff_hash,
        'package_versions': {name: version(name) for name in ['lightrag-hku', 'nano-vectordb', 'numpy', 'sentence-transformers']},
        'embedding_device': str(model.device),
        'embedding_revision': getattr(model[0].auto_model.config, '_commit_hash', None),
        'arguments': {'answer_model': args.answers_model, 'answer_limit': args.answer_limit, 'K': 10},
        'latency_scope': 'Reader excludes embedding/model load; hybrid includes expansion/search/rerank. Single pass before-first/after-second; no speedup inference.',
        'oracle_scope': 'Independent NumPy cosine selection conditional on shared strict decoder; decoder separately tested against struct fixtures.',
        'scope': 'reader component fixed-universe comparison plus current hybrid retrieval; not full graph candidate selection or factual answer accuracy',
        'benchmark_sha256': digest(benchmark_path), 'store_fingerprints': snapshots, 'stores_unchanged': unchanged,
        'positive_questions': len(positive), 'negative_questions': len(benchmark)-len(positive), 'resident_chunks': len(resident),
        'embedding_model': hybrid.EMBEDDING_MODEL, 'embedding_dimension': dimension, 'model_load_ms': model_load_ms,
        'reranker_model_loaded': reranker is not None, 'python_hash_seed': os.getenv('PYTHONHASHSEED'),
        'strict_element_target_questions': sum(bool(r['target_element']) for r in results),
        'text_target_questions_not_strictly_scored': [r['id'] for r in results if not r['target_element']],
        'before': metrics(results, 'before'), 'after': metrics(results, 'after'), 'current_hybrid': metrics(results, 'hybrid'),
        'before_fallbacks': sum(r['before']['fallback'] for r in results), 'after_reader_errors': reader_errors['after'], 'after_cosine_ranking_verified': len(results),
        'gates': gates, 'retrieval_results': results, 'answers_generated': len(answers),
        'accuracy_limit': 'Target-ID hits measure metadata retrieval; keywords, mentions, HTTP200 and local model outputs do not independently establish answer truth.'}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'retrieval_results', 'gates'}}, indent=2), flush=True)


if __name__ == '__main__':
    main()
