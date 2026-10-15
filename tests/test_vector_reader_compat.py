"""Dual-format vector decoding and real LightRAG reader/ranker regressions."""
import asyncio
import base64
from copy import deepcopy
import importlib
import math
import struct
from types import MethodType, SimpleNamespace
import zlib

import pytest


def encoded(values):
    return base64.b64encode(zlib.compress(struct.pack('=' + 'e' * len(values), *values))).decode('ascii')


def compat():
    return importlib.import_module('src.vector_reader_compat')


def test_numeric_list_preserves_precision_and_encoded_matches_float16():
    decode = compat().decode_vector
    original = [0.10000000149011612, -0.25, 1, 0]
    assert decode(original, 4) == [float(x) for x in original]
    assert decode(encoded(original), 4) == list(struct.unpack('=4e', struct.pack('=4e', *original)))
    assert decode(original, 4)[0] != decode(encoded(original), 4)[0]
    assert original == [0.10000000149011612, -0.25, 1, 0]


@pytest.mark.parametrize('value', [[], [1], [1, 2, 3], [True, 0], ['1', 0], [None, 0],
                                  [[1], 0], [math.nan, 0], [math.inf, 0], [-math.inf, 0],
                                  [10 ** 1000, 0], [1e300, 0], None, (1, 0), {'x': 1}], ids=lambda value: type(value).__name__)
def test_bad_numeric_vectors_are_rejected(value):
    with pytest.raises(compat().VectorFormatError):
        compat().decode_vector(value, 2)


@pytest.mark.parametrize('value', ['%%%=', 'not base64', '\N{SNOWMAN}', '',
                                  encoded([1]), encoded([1, 2, 3]), encoded([math.inf, 0]),
                                  base64.b64encode(b'not zlib').decode(),
                                  base64.b64encode(zlib.compress(b'abc')).decode(),
                                  base64.b64encode(zlib.compress(b'\0' * 100000)).decode(),
                                  base64.b64encode(zlib.compress(struct.pack('=2e', 1, 0)) + b'trailing').decode(),
                                  base64.b64encode(zlib.compress(struct.pack('=2e', 1, 0)) * 2).decode(),
                                  encoded([1, 0])[:-4], encoded([1, 0]) + ' ', 'A' * 100000], ids=lambda value: type(value).__name__)
def test_bad_encoded_vectors_are_rejected(value):
    with pytest.raises(compat().VectorFormatError):
        compat().decode_vector(value, 2)


def native_storage(rows, dimension=3):
    from lightrag.kg.nano_vector_db_impl import NanoVectorDBStorage
    storage = object.__new__(NanoVectorDBStorage)
    storage.embedding_func = SimpleNamespace(embedding_dim=dimension)
    storage._storage_lock = asyncio.Lock()
    storage._pending_upserts = {}
    storage._pending_deletes = set()
    storage._unsaved_upserts = {}
    storage._unsaved_deletes = {}
    async def client():
        return SimpleNamespace(get=lambda ids: [r for r in rows if r['__id__'] in ids])
    storage._get_client = client
    return storage


def test_original_installed_reader_reproduces_reported_failure():
    rows = [{'__id__': 'list-row', 'vector': [1., 0., 0.]}]
    with pytest.raises(TypeError, match='bytes-like object or ASCII string'):
        asyncio.run(native_storage(rows).get_vectors_by_ids(['list-row']))


def test_installed_reader_accepts_mixed_rows_without_mutating_them():
    rows = [{'__id__': 'list-row', 'vector': [1., 0., 0.]},
            {'__id__': 'encoded-row', 'vector': encoded([0, 1, 0])}]
    before = deepcopy(rows)
    storage = native_storage(rows)
    compat().install_vector_reader(storage)
    assert asyncio.run(storage.get_vectors_by_ids(['list-row', 'encoded-row', 'missing'])) == {
        'list-row': [1., 0., 0.], 'encoded-row': [0., 1., 0.]}
    assert rows == before
    method = storage.get_vectors_by_ids
    compat().install_vector_reader(storage)
    assert storage.get_vectors_by_ids is method


def test_real_similarity_picker_ranks_instead_of_truncating():
    import numpy as np
    from lightrag.utils import pick_by_vector_similarity
    rows = [{'__id__': 'orthogonal', 'vector': encoded([0, 1, 0])},
            {'__id__': 'parallel', 'vector': [1., 0., 0.]},
            {'__id__': 'opposite', 'vector': encoded([-1, 0, 0])}]
    storage = native_storage(rows)
    compat().install_vector_reader(storage)
    async def rank():
        return await pick_by_vector_similarity(
            'synthetic query', None, storage, 3,
            [{'sorted_chunks': ['orthogonal', 'opposite', 'parallel']}], None,
            query_embedding=np.array([1., 0., 0.], dtype=np.float32))
    assert asyncio.run(rank()) == ['parallel', 'orthogonal', 'opposite']


def test_pending_overlay_and_deleted_rows_keep_native_precedence():
    import numpy as np
    rows = [{'__id__': 'updated', 'vector': encoded([-1, 0, 0])},
            {'__id__': 'deleted', 'vector': [1., 0., 0.]}]
    storage = native_storage(rows)
    storage._pending_upserts['updated'] = SimpleNamespace(vector=np.array([0., 1., 0.]))
    storage._pending_deletes.add('deleted')
    compat().install_vector_reader(storage)
    assert asyncio.run(storage.get_vectors_by_ids(['updated', 'deleted'])) == {'updated': [0., 1., 0.]}


def test_lazy_pending_embedding_remains_native_and_cached():
    import numpy as np
    storage = native_storage([])
    storage._max_batch_size = 2
    storage._pending_upserts['lazy'] = SimpleNamespace(vector=None, record={'content': 'synthetic fixture'})
    calls = []
    async def embed(texts, context):
        calls.append((texts, context))
        return np.array([[1., 0., 0.]], dtype=np.float32)
    embed.embedding_dim = 3
    storage.embedding_func = embed
    compat().install_vector_reader(storage)
    async def twice():
        assert await storage.get_vectors_by_ids(['lazy']) == {'lazy': [1., 0., 0.]}
        assert await storage.get_vectors_by_ids(['lazy']) == {'lazy': [1., 0., 0.]}
    asyncio.run(twice())
    assert calls == [(['synthetic fixture'], 'document')]


@pytest.mark.parametrize('resident_time,expected', [(20, [1., 0., 0.]), (5, [0., 1., 0.])])
def test_redo_prefers_only_a_strictly_newer_resident(resident_time, expected):
    import numpy as np
    rows = [{'__id__': 'redo', '__created_at__': resident_time, 'vector': [1., 0., 0.]}]
    storage = native_storage(rows)
    storage._unsaved_upserts['redo'] = SimpleNamespace(record={'__created_at__': 10}, vector=np.array([0., 1., 0.]))
    compat().install_vector_reader(storage)
    assert asyncio.run(storage.get_vectors_by_ids(['redo'])) == {'redo': expected}


def test_logged_delete_hides_only_the_record_that_was_removed():
    row = {'__id__': 'deleted', 'vector': [1., 0., 0.]}
    storage = native_storage([row])
    storage._unsaved_deletes['deleted'] = storage._row_fingerprint(row)
    compat().install_vector_reader(storage)
    assert asyncio.run(storage.get_vectors_by_ids(['deleted'])) == {}


def test_production_dimension_and_unsupported_contract_guard(monkeypatch):
    values = [0.125] * 1024
    assert compat().decode_vector(values, 1024) == values
    assert compat().decode_vector(encoded(values), 1024) == values
    storage = native_storage([])
    original = storage.get_vectors_by_ids
    monkeypatch.setattr(compat(), 'NATIVE_READER_AST_SHA256', '0' * 64)
    with pytest.raises(RuntimeError, match='changed'):
        compat().install_vector_reader(storage)
    assert storage.get_vectors_by_ids == original


@pytest.mark.parametrize('dimension', [0, -1, True, '3'])
def test_invalid_dimensions_are_rejected(dimension):
    with pytest.raises(compat().VectorFormatError):
        compat().decode_vector([1., 0., 0.], dimension)
