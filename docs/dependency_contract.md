# Local dependency and build contract

The active source-only Figure A1 setup CLI uses Python standard library plus
the existing **PyMuPDF 1.26.5**, declared as optional extra `a1`. It imports no
provider configuration, credentials, embedding model or LightRAG. No dependency
or model was installed. The normal query/API integration still uses the existing
v1 runtime dependencies. Run `python -B -m src.evidence_a1_cli` for structural
inventory only; owner CQ and answer accuracy remain pending. See the
[A1 setup receipt](evidence_v2_a1_setup.md) for exact active checks.

The bounded v2 core uses Python's standard library. `pyproject.toml` declares the
source-package metadata and a separate optional v1 runtime. `requirements-v1.lock`
records exact **direct** imports observed in the existing environment; its name
does not imply a complete transitive lock, hashes, a platform-independent GPU
installation, available model weights or a reproducible private corpus. No
dependency installation, upgrade, credential change or model download was run.

`requirements-runtime.lock` adds the **observed transitive metadata closure** of
the ten direct v1 dependencies, the pytest test extra and the two build tools on
CPython 3.12.7, Windows/win32, AMD64. Its 86 exact package pins cover 139 active
dependency edges. Package requirements were parsed with `packaging.Requirement`;
environment markers were evaluated against the host, requested extras were
propagated (including `google-auth[requests]`), and each active specifier and
`Requires-Python` bound was checked against installed versions. All checks passed:
zero missing packages, version conflicts, unsupported extras or direct
references. Packages outside this reachable closure were excluded.

This is a platform-specific installed-metadata snapshot, not a new solver result.
It has no wheel hashes or proof that all exact artifacts remain available. In
particular, `torch==2.5.1+cu121` requires the matching approved Windows CUDA wheel;
no index URL, credential or direct-reference URL was added. The closure alone
does not reproduce model weights, caches, the authorized source or the database.
No clean-environment installation was attempted. The local
`runtime-closure.json` receipt records the environment, roots, every active edge,
requested extras and lock SHA-256
`9e5c1cf31157bef13da3e920400d1b14a461ff276a940bb977c4c6fc9ff0c038`.

Tested host: CPython 3.12.7 on Windows, pytest 9.0.2, setuptools 80.9.0,
wheel 0.45.1, Node v25.0.0, pip 26.0.1. Python 3.11+ is declared; other
Python/platform combinations have not been exercised. Build tools are pinned;
installing the source into a prepared environment should use a local editable
checkout (`python -m pip install --no-build-isolation --no-deps -e .`). Only use
`--no-deps` after provisioning/reviewing the declared extras. No install was
performed as part of validation.

An offline build using the pinned installed setuptools backend succeeded against
a temporary source snapshot. All ten direct v1 pins and all three build/test pins
matched installed metadata. The wheel contained only Python modules and package
metadata; no PDF, image, JSON/JSONL, database or environment file was included.
This validates package construction, not fresh dependency resolution or a
standalone installed runtime. The local `build-contract.json` receipt preserves
the input and wheel hashes; this snapshot is separate from final integration.

`src` and `eval` retain the repository's namespace-package layout. A wheel is a
source-code artifact, not a self-contained runtime: manifest configuration,
viewer, authorized source PDF, parsed assets, SQLite registry, vector stores and
model weights remain checkout-relative and must be provisioned separately.
Private PDFs, extracts, runtime stores and `.env` files are not packaged. The v1
LightRAG reader retains its exact 1.5.7 version and executable AST contract guard;
upgrading requires an explicit review and fresh compatibility evidence.

Run bounded checks from the checkout using the existing environment:

```powershell
python -B tests/run_manifest_offline.py
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -B -m pytest -p no:cacheprovider --basetemp "$env:TEMP/a30-native-reader" tests/test_vector_reader_compat.py
node tests/security_settings.test.js
node tests/bbox_validation.test.js
node tests/answer_grounding_ui.test.js
```

The guarded suite disables dotenv reads, models, providers, network and SQLite.
The native-reader suite exercises the installed LightRAG reader and cosine
selector against synthetic vectors. These are software regressions. They do not
establish model answer correctness, table-cell extraction fidelity or visual
understanding. Same-input v1/v2 and live-model evidence must be reported
separately. See `vector_reader_compatibility.md` for the baseline contract and
scope of the previous reader experiment.

Independent baseline on 2026-10-21, before integration of v2 source changes:

| Check | Result |
| --- | --- |
| Guarded offline Python | 827 passed in 23.97 s |
| Installed native reader | 44 passed in 3.07 s |
| Credential settings JavaScript | 4 passed |
| Bounding-box JavaScript | 17 invalid, 4 valid/edge and 1 unloaded-image transition passed |
| Answer grounding UI JavaScript | 42/42 passed |

Logs are local task receipts, not source corpus evidence. This was a bounded
selection of checks, not every historical test and not a cloud/provider benchmark.
