"""Read-only compatibility for the installed LightRAG 1.5.7 chunk vector reader.

The native control flow below is retained so pending/redo/delete precedence and
lock/reload behavior stay intact. Only resident vector decoding is extended.
Source: https://github.com/HKUDS/LightRAG/blob/v1.5.7/lightrag/kg/nano_vector_db_impl.py

Adapted portion: MIT License, Copyright (c) 2025 LightRAG Team.
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import ast
import asyncio
import base64
import binascii
import hashlib
from importlib.metadata import version
import inspect
import math
import struct
import textwrap
from types import MethodType
from typing import Any
import zlib

import numpy as np

SUPPORTED_VERSION = "1.5.7"
NATIVE_READER_AST_SHA256 = "8e93a2534c64faefaa15fd08900b3937a91a8099e9a43cb4b24c3b2e93067aa7"


class VectorFormatError(ValueError):
    """Unsupported or malformed vector; never a successfully decoded result."""


def decode_vector(value, dimension):
    """Keep list precision; decode native base64(zlib(float16)) with strict bounds.

    zlib max_length/eof/tail contract:
    https://docs.python.org/3.12/library/zlib.html#zlib.Decompress.decompress
    Base64 validation:
    https://docs.python.org/3.12/library/base64.html#base64.b64decode
    """
    if type(dimension) is not int or not 0 < dimension <= 65536:
        raise VectorFormatError("VECTOR_FORMAT_INVALID: unsupported dimension")
    if isinstance(value, (str, bytes)):
        expected_bytes = dimension * 2
        # More than the writer's worst-case deflate overhead; bound input too.
        encoded_limit = 4 * ((expected_bytes + 1024 + 2) // 3)
        if len(value) > encoded_limit:
            raise VectorFormatError("VECTOR_FORMAT_INVALID: encoded vector too large")
        try:
            compressed = base64.b64decode(value, validate=True)
            stream = zlib.decompressobj()
            raw = stream.decompress(compressed, expected_bytes + 1)
            if (len(raw) != expected_bytes or not stream.eof
                    or stream.unconsumed_tail or stream.unused_data):
                raise VectorFormatError("VECTOR_FORMAT_INVALID: invalid compressed vector length or framing")
            # Native writer uses numpy.float16 native byte order (no format change).
            value = list(struct.unpack("=" + "e" * dimension, raw))
        except (binascii.Error, UnicodeError, zlib.error, struct.error, ValueError) as exc:
            if isinstance(exc, VectorFormatError):
                raise
            raise VectorFormatError("VECTOR_FORMAT_INVALID: invalid encoded vector") from exc
    if not isinstance(value, list) or len(value) != dimension:
        raise VectorFormatError("VECTOR_FORMAT_INVALID: vector dimension mismatch")
    result = []
    for number in value:
        if type(number) not in {int, float}:
            raise VectorFormatError("VECTOR_FORMAT_INVALID: vector values must be numbers")
        try:
            number = float(number)
        except (OverflowError, ValueError) as exc:
            raise VectorFormatError("VECTOR_FORMAT_INVALID: invalid numeric value") from exc
        if not math.isfinite(number) or abs(number) > 3.4028234663852886e38:
            raise VectorFormatError("VECTOR_FORMAT_INVALID: non-finite or float32-overflow value")
        result.append(number)
    return result


async def read_vectors_compatible(self, ids: list[str]) -> dict[str, list[float]]:
        """Get vectors by their IDs (read-your-writes), returning only ID and vector.

        For buffered upserts the vector is computed lazily (and cached back onto
        the pending doc so the next flush reuses it instead of re-embedding);
        for materialized rows the stored compressed vector is decoded.

        Args:
            ids: List of unique identifiers

        Returns:
            Dictionary mapping IDs to their vector embeddings
            Format: {id: [vector_values], ...}
        """
        if not ids:
            return {}

        vectors_dict: dict[str, list[float]] = {}
        remaining: list[str] = []
        logged: dict[str, str] = {}
        redo_docs: dict[str, Any] = {}
        async with self._storage_lock:
            to_embed: list[tuple[str, Any]] = []
            for requested_id in ids:
                pending = self._pending_upserts.get(requested_id)
                if pending is None:
                    if requested_id in self._pending_deletes:
                        continue  # queued delete, no newer upsert -> absent
                    redo = self._unsaved_upserts.get(requested_id)
                    if redo is not None:
                        # Still queried against the client: the replay only
                        # restores the logged row when no strictly newer row
                        # was committed under the id meanwhile, so the client
                        # is needed to apply the same ordering rule below.
                        # The cached vector is always set once a doc reaches
                        # the log, so the redo branch can always answer.
                        redo_docs[requested_id] = redo
                        remaining.append(requested_id)
                        continue
                    # A logged id still goes to the client: only the removed
                    # row version is hidden, not one written in its place.
                    if requested_id in self._unsaved_deletes:
                        logged[requested_id] = self._unsaved_deletes[requested_id]
                    remaining.append(requested_id)
                elif pending.vector is not None:
                    vectors_dict[requested_id] = pending.vector.astype(
                        np.float32
                    ).tolist()
                else:
                    to_embed.append((requested_id, pending))

            if to_embed:
                contents = [pdoc.record["content"] for _, pdoc in to_embed]
                batches = [
                    contents[i : i + self._max_batch_size]
                    for i in range(0, len(contents), self._max_batch_size)
                ]
                embeddings_list = await asyncio.gather(
                    *[
                        self.embedding_func(batch, context="document")
                        for batch in batches
                    ]
                )
                embeddings = np.concatenate(embeddings_list)
                if len(embeddings) != len(to_embed):
                    raise RuntimeError(
                        f"[{self.workspace}] embedding is not 1-1 with pending data, "
                        f"{len(embeddings)} != {len(to_embed)}"
                    )
                for (requested_id, pdoc), embedding in zip(to_embed, embeddings):
                    # Cache the vector back so the next flush reuses it.
                    pdoc.vector = embedding
                    vectors_dict[requested_id] = embedding.astype(np.float32).tolist()

        if remaining:
            client = await self._get_client()
            resident_map: dict[str, dict[str, Any]] = {}
            for result in client.get(remaining):
                if not result:
                    continue
                doc_id = result.get("__id__")
                if doc_id is not None:
                    resident_map[str(doc_id)] = result
                if doc_id in redo_docs:
                    continue  # resolved against the redo entry below
                if self._matches_redo_entry(result, logged.get(doc_id)):
                    continue
                if "vector" in result and "__id__" in result:
                    # Decompress vector data (Base64 + zlib + Float16 compressed)
                    vectors_dict[result["__id__"]] = decode_vector(
                        result["vector"], self.embedding_func.embedding_dim)
            for requested_id, redo in redo_docs.items():
                resident = resident_map.get(str(requested_id))
                if (
                    self._resident_supersedes_redo(resident, redo.record)
                    and "vector" in resident
                ):
                    vectors_dict[requested_id] = decode_vector(
                        resident["vector"], self.embedding_func.embedding_dim)
                else:
                    vectors_dict[requested_id] = redo.vector.astype(np.float32).tolist()

        return {key: decode_vector(value, self.embedding_func.embedding_dim)
            for key, value in vectors_dict.items()}


def install_vector_reader(storage):
    """Bind only this existing chunk-store instance; never patch global packages.

    Private native buffer semantics are version/source guarded. Re-review this
    adapter when the dependency changes rather than silently guessing its shape.
    """
    if getattr(storage.get_vectors_by_ids, "__func__", None) is read_vectors_compatible:
        return
    native = type(storage).get_vectors_by_ids
    if (version("lightrag-hku") != SUPPORTED_VERSION
            or type(storage).__module__ != "lightrag.kg.nano_vector_db_impl"
            or type(storage).__name__ != "NanoVectorDBStorage"):
        raise RuntimeError("Vector reader compatibility requires reviewed LightRAG 1.5.7 Nano storage")
    try:
        source = ast.parse(textwrap.dedent(inspect.getsource(native)))
        if ast.get_docstring(source.body[0]) is not None:
            source.body[0].body.pop(0)  # Formatting inside docstrings is not code.
        fingerprint = hashlib.sha256(ast.dump(source, include_attributes=False).encode()).hexdigest()
    except (OSError, TypeError, SyntaxError) as exc:
        raise RuntimeError("Cannot verify native vector reader contract") from exc
    if fingerprint != NATIVE_READER_AST_SHA256:
        raise RuntimeError("Native vector reader changed; compatibility adapter needs review")
    storage._a30_original_vector_reader = storage.get_vectors_by_ids
    storage.get_vectors_by_ids = MethodType(read_vectors_compatible, storage)
