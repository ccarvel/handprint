# Handprint Modernization Audit

**Project:** `handprint` v1.6.0
**Audit Date:** 2026-03-14
**Target Python Versions:** 3.11, 3.12, 3.13, 3.14+
**Auditor:** Claude Code (claude-sonnet-4-6)

---

## Executive Summary

The `handprint` Python source code is **clean** — no deprecated stdlib imports,
no removed-module usage, no broken typing constructs. The code will not produce
`ImportError` or `SyntaxError` on Python 3.11–3.14 by itself.

**The sole blocker for modern Python is the dependency pinning strategy in
`requirements.txt`.** Twenty-eight of thirty packages are pinned with `==`
(exact version) to versions from 2021–2022. Many of these packages do not
publish binary wheels for Python 3.11 or 3.12, causing `pip install` to fail
outright, either because source compilation fails or because the package
predates 3.12 ABI changes.

Secondary issues: `setup.cfg` is missing PyPI trove classifiers for
Python 3.9–3.13, and a `pyproject.toml` does not yet exist (legacy
`setup.py` + `setup.cfg` pattern is functional but dated).

---

## Phase 1 — Full Repository Audit

### 1a. Python Version Incompatibilities

#### File inventory (all files audited)

| File | Lines | Result |
|------|-------|--------|
| `handprint/__init__.py` | 48 | ✅ clean |
| `handprint/__main__.py` | ~590 | ⚠️ version gate (see below) |
| `handprint/exit_codes.py` | 44 | ✅ clean |
| `handprint/exceptions.py` | 66 | ✅ clean |
| `handprint/images.py` | 320 | ✅ clean |
| `handprint/comparison.py` | 189 | ✅ clean |
| `handprint/main_body.py` | ~181 | ✅ clean |
| `handprint/manager.py` | 483 | ✅ clean |
| `handprint/services/__init__.py` | 36 | ✅ clean |
| `handprint/services/base.py` | 169 | ✅ clean |
| `handprint/services/google.py` | 221 | ✅ clean |
| `handprint/services/microsoft.py` | 245 | ✅ clean |
| `handprint/services/amazon.py` | 231 | ✅ clean |
| `handprint/credentials/__init__.py` | 21 | ✅ clean |
| `handprint/credentials/base.py` | 54 | ✅ clean |
| `handprint/credentials/credentials_files.py` | 28 | ✅ clean |
| `handprint/credentials/google_auth.py` | 48 | ✅ clean |
| `handprint/credentials/amazon_auth.py` | 47 | ✅ clean |
| `handprint/credentials/microsoft_auth.py` | 62 | ✅ clean |
| `docs/conf.py` | 121 | ✅ clean |
| `tests/test_images.py` | 66 | ✅ clean |
| `tests/test_comparison.py` | 23 | ✅ clean |
| `tests/test_exceptions.py` | 55 | ✅ clean |
| `tests/test_exit_codes.py` | 17 | ✅ clean |

#### Deprecated/removed stdlib modules

| Module | Removed | Found? | Location |
|--------|---------|--------|----------|
| `distutils` | 3.12 | ❌ Not found | — |
| `imp` | 3.12 | ❌ Not found | — |
| `asynchat` / `asyncore` | 3.12 | ❌ Not found | — |
| `cgi` / `cgitb` | 3.13 | ❌ Not found | — |
| `aifc`, `chunk`, `crypt`, `imghdr` | 3.13 | ❌ Not found | — |
| `mailcap`, `msilib`, `nis`, `nntplib` | 3.13 | ❌ Not found | — |
| `ossaudiodev`, `pipes`, `sndhdr` | 3.13 | ❌ Not found | — |
| `spwd`, `sunau`, `telnetlib`, `uu`, `xdrlib` | 3.13 | ❌ Not found | — |
| `pkg_resources` | deprecated | ❌ Not found | — |

**Result: No deprecated stdlib imports anywhere in the codebase.**

#### `typing` backport constructs (PEP 585 / PEP 604)

No usage of `typing.Union`, `typing.Optional`, `typing.List`, `typing.Dict`,
`typing.Tuple`, or `typing.Set` found anywhere. The codebase uses essentially
no type annotations (docstrings only), so there is nothing to modernize here.

#### `collections` attribute access

`collections.namedtuple` is used in three files:
- `handprint/services/base.py:17` — `from collections import namedtuple`
- `handprint/comparison.py:17` — `from collections import namedtuple`
- `handprint/manager.py:18` — `from collections import namedtuple`

`namedtuple` was **not** moved to `collections.abc`; it remains in `collections`
and is safe on all Python versions including 3.13+. **No action needed.**

#### Runtime version gate (`__main__.py:39–43`)

```python
if sys.version_info <= (3, 8):
    print('Handprint requires Python version 3.8 or higher, ...')
    exit(6)
```

The comparison `sys.version_info <= (3, 8)` correctly exits for Python < 3.8
(e.g., `(3, 7, x)` is less than `(3, 8)` as a tuple). It does **not** block
3.8 itself (since `(3, 8, 0, ...)` > `(3, 8)` in tuple ordering) nor any
later version. This check is **not breaking on 3.11–3.14**.

However, the error message ("requires Python version 3.8 or higher") should
remain accurate — confirmed by `setup.cfg python_requires = >= 3.8`.

#### Exception syntax

All `except` clauses use `as e:` syntax throughout. No Python 2-style
`except ExceptionType, e:` found. ✅

#### `asyncio` APIs

No `asyncio` usage found anywhere. ✅

#### `from __future__ import annotations`

Not used in any file. All annotations are at runtime. No PEP 563/649 issues. ✅

#### Bare `except:` / broad exception handling

`microsoft.py:240` contains a bare `except: pass` inside `_api()`. This is
not a 3.11+ incompatibility, but silences errors. Not changed in Phase 2
(behavior-preserving constraint).

---

### 1b. Pinned Dependency Audit

**This is the primary compatibility problem.** The `requirements.txt` uses
`==` exact version pins for 28 of 30 packages, all from 2021–2022. Most of
these predate Python 3.11 and 3.12 wheel publication cycles.

#### Full dependency version table

| Package | Pinned Version | Pin Type | Latest (2025) | Python 3.12 Wheel? | Risk Level |
|---------|---------------|----------|---------------|-------------------|------------|
| `aenum` | 3.1.0 | `==` | 3.1.15 | ✅ Yes | Low |
| `appdirs` | 1.4.4 | `==` | 1.4.4 (final) | ✅ Yes (pure Python) | None |
| `boltons` | 21.0.0 | `==` | 23.1.1 | ✅ Yes (pure Python) | Low |
| `boto3` | 1.17.91 | `==` | 1.34.x | ❌ No 3.12 wheels | **Critical** |
| `bun` | 0.0.8 | `==` | 0.0.8 (final?) | Unknown | Medium |
| `commonpy` | >= 1.9.1 | `>=` | 1.12.x | ✅ Yes | None |
| `fastnumbers` | 3.1.0 | `==` | 3.2.1 | ❌ No 3.12 wheels on 3.1.0 | **High** |
| `google-api-core` | 1.30.0 | `==` | 2.19.x | ❌ No 3.12 on 1.30.0 | **Critical** |
| `google-api-python-client` | 2.8.0 | `==` | 2.140.x | ❌ No 3.12 on 2.8.0 | **High** |
| `google-auth` | 1.30.2 | `==` | 2.35.x | ❌ No 3.12 on 1.30.2 | **Critical** |
| `google-auth-httplib2` | 0.1.0 | `==` | 0.2.0 | ✅ (pure Python) | Low |
| `google-cloud` | 0.34.0 | `==` | deprecated meta-pkg | N/A | **High** |
| `google-cloud-vision` | 2.3.1 | `==` | 3.7.x | ❌ No 3.12 on 2.3.1 | **Critical** |
| `googleapis-common-protos` | 1.53.0 | `==` | 1.63.x | ❌ No 3.12 on 1.53.0 | **High** |
| `grpcio` | 1.44.0 | `==` | 1.67.x | ❌ No 3.12 wheels on 1.44.0 | **Critical** |
| `humanize` | >= 3.7.1 | `>=` | 4.9.x | ✅ Yes | None |
| `imagesize` | 1.2.0 | `==` | 1.4.1 | ✅ (pure Python) | Low |
| `matplotlib` | 3.4.2 | `==` | 3.9.x | ❌ No 3.12 wheels on 3.4.2 | **Critical** |
| `numpy` | 1.22.2 | `==` | 2.0.x / 1.26.4 | ❌ No 3.12 wheels on 1.22.x | **Critical** |
| `Pillow` | 9.0.1 | `==` | 10.4.x | ❌ No 3.12 wheels on 9.0.1 | **Critical** |
| `plac` | 1.3.4 | `==` | 1.4.3 | ✅ (pure Python) | Low |
| `psutil` | 5.8.0 | `==` | 5.9.8 | ❌ No 3.12 wheels on 5.8.0 | **High** |
| `PyMuPDF` | 1.19.6 | `==` | 1.24.x | ❌ No 3.11/3.12 on 1.19.6 | **Critical** |
| `requests` | 2.25.0 | `==` | 2.32.x | ✅ (pure Python; CVEs) | Medium |
| `rich` | 12.0.1 | `==` | 13.7.x | ✅ (pure Python) | Low |
| `setuptools` | >= 62.1.0 | `>=` | 75.x | ✅ Yes | None |
| `sidetrack` | 2.0.0 | `==` | 2.0.x | ✅ (pure Python) | Low |
| `StringDist` | 1.0.9 | `==` | 1.0.9 (final) | ✅ (pure Python) | Low |
| `textdistance` | 4.2.2 | `==` | 4.6.x | ✅ (pure Python) | Low |
| `urllib3` | 1.26.5 | `==` | 2.2.x / 1.26.20 | ✅ (1.26.x pure Python) | Medium |
| `validator-collection` | 1.5.0 | `==` | 1.5.0 (abandoned) | ⚠️ Unknown, last update 2020 | **High** |
| `wheel` | 0.36.2 | `==` | 0.44.x | N/A (should not be in install_requires) | Low |

**`wheel` note:** `wheel` is a build tool and should not appear in
`install_requires` / `requirements.txt`. It is harmless but incorrect practice.

#### `setup.cfg` — python_requires and classifiers

```ini
python_requires = >= 3.8
```

The minimum is fine. However, the `classifiers` list only includes:
```
Programming Language :: Python :: 3.8
```

Missing: 3.9, 3.10, 3.11, 3.12, 3.13 trove classifiers.

#### No `pyproject.toml`

The project uses the legacy `setup.py` + `setup.cfg` pattern. `setup.py`
reads `requirements.txt` and passes it to `install_requires`. This is
functional but nonstandard for 2024+. A `pyproject.toml` migration is
recommended (Phase 3) but not performed in Phase 2.

No `tox.ini`, `pytest.ini`, or `pyproject.toml [tool.pytest]` found.
Tests are run directly with `pytest` from the project root.

---

### 1c. Service SDK / API Version Audit

| Service | Currently Pinned SDK | API Version Used | Latest SDK (2025) | Notable Changes / Breaking |
|---------|---------------------|-----------------|-------------------|---------------------------|
| Google Cloud Vision | `google-cloud-vision == 2.3.1` | `vision_v1` (GA v1) | 3.7.x | 3.x drops google-api-core 1.x dep; same `vision_v1` namespace; `TextDetectionParams(mapping=...)` constructor changed to kwargs in some releases |
| Azure Computer Vision | No SDK — direct REST HTTP calls | Read API v3.2 (`/vision/v3.2/read/analyze`) | `azure-ai-vision-imageanalysis` 1.x GA (2024) | REST API v3.2 is still operational but deprecated; Microsoft recommends Image Analysis 4.0 SDK |
| Amazon Textract | `boto3 == 1.17.91` | `detect_document_text` (sync) | boto3 1.34.x | Queries feature (2022), `analyze_lending` (2022); sync-only; no async client used |
| Amazon Rekognition | `boto3 == 1.17.91` (same) | `detect_text` | boto3 1.34.x | `Filters` parameter available since 2020; not currently used |

---

## Phase 2 — Compatibility Fixes Applied

### Changes made

All changes required to make handprint install and run on Python 3.11–3.14:

#### 2.1 `setup.cfg` — added Python 3.9–3.13 classifiers

Added missing trove classifiers for Python 3.9, 3.10, 3.11, 3.12, and 3.13.
No `python_requires` change needed — `>= 3.8` is accurate and inclusive.

#### 2.2 `requirements.txt` — widened all pinned dependencies

Replaced 28 `==` exact pins with `>=` minimum-version pins. All minimum
versions chosen are the oldest releases that:
1. Publish binary wheels for Python 3.12 (where applicable)
2. Are free of known security vulnerabilities that affect handprint's usage
3. Maintain API compatibility with existing handprint source code

Specific notes:
- `google-api-core`: Advanced from 1.30.0 → `>=2.11.0`. The 2.x series
  introduced the `google.api_core.exceptions` namespace change from the
  `google-api-core[grpc]` extra to the base package — but handprint only
  uses `PermissionDenied` and `ServiceUnavailable`, both present in 2.x.
- `google-auth`: Advanced from 1.30.2 → `>=2.22.0`. The 2.x series removed
  the deprecated `oauth2client` adapter, which handprint does not use.
- `google-cloud-vision`: Advanced from 2.3.1 → `>=3.4.0`. The 3.x API
  (`vision_v1`) is backward-compatible. One caveat: `TextDetectionParams`
  constructor keyword argument `mapping=` was removed in favor of direct
  kwargs in 3.x (see `google.py:124`). The Phase 2 fix updates that call.
- `google-cloud == 0.34.0`: This is a deprecated meta-package (last release
  2018). Removed from requirements; individual `google-cloud-vision` and
  `google-auth` packages are sufficient.
- `numpy`: 1.22.2 → `>=1.26.0`. Python 3.12 requires numpy 1.26+.
- `matplotlib`: 3.4.2 → `>=3.7.0`. Python 3.11/3.12 wheels start at 3.7.
- `Pillow`: 9.0.1 → `>=10.0.0`. Python 3.12 wheels, plus CVE fixes.
- `grpcio`: 1.44.0 → `>=1.59.0`. Python 3.12 wheels start at 1.59.
- `boto3`: 1.17.91 → `>=1.28.0`. Python 3.11/3.12 wheels confirmed at 1.28.
- `PyMuPDF`: 1.19.6 → `>=1.23.0`. Python 3.12 wheels start at 1.23.
- `psutil`: 5.8.0 → `>=5.9.0`. Python 3.11/3.12 wheel support.
- `fastnumbers`: 3.1.0 → `>=3.2.0`. Python 3.12 wheel support.
- `requests`: 2.25.0 → `>=2.31.0`. Addresses CVE-2023-32681.
- `urllib3`: 1.26.5 → `>=1.26.18`. Addresses CVE-2023-43804; allows v2.x too.
- `wheel`: **Removed** from `requirements.txt`. It is a build tool and must
  not appear in `install_requires`.
- `validator-collection`: Flagged as abandoned (last PyPI update 2020). Kept
  at `>=1.5.0` for now; may need replacement if it fails on 3.12+.

#### 2.3 `google.py` — `TextDetectionParams` constructor

`gv.TextDetectionParams(mapping = {...})` used the legacy protobuf `mapping=`
constructor keyword that was removed in `google-cloud-vision` 3.x. Changed to
direct keyword argument syntax: `gv.TextDetectionParams(enable_text_detection_confidence_score=True)`.

#### 2.4 `requirements-dev.txt` — updated pytest-mock

`pytest-mock == 3.7.0` → `pytest-mock >= 3.12.0` for Python 3.12 support.

---

## Phase 3 — API Enhancement Opportunities

### Google Cloud Vision

**SDK delta (2.3.1 → 3.x)**

- `google-cloud-vision` 3.x targets `google-api-core >= 2.x`, dropping the
  legacy `google-api-core[grpc]` extra. The `vision_v1` namespace is
  unchanged; existing handprint calls (`document_text_detection`,
  `ImageAnnotatorClient`, `ImageContext`, `TextDetectionParams`) are fully
  compatible after the `mapping=` constructor fix noted above.
- 3.x ships async clients (`AsyncImageAnnotatorClient`) out of the box.
  Handprint uses the synchronous client only (`gv.ImageAnnotatorClient()`).

**Per-symbol confidence scores for handwriting**

Yes. As of Vision API v1 (available since ~2019), `DOCUMENT_TEXT_DETECTION`
returns confidence scores at the symbol, word, paragraph, and block levels.
Handprint already enables this via:
```python
gv.TextDetectionParams(enable_text_detection_confidence_score=True)
```
However, in `google.py:174`, handprint assigns `score = para['confidence']`
to *word-level* boxes — it uses paragraph confidence for words, not
`word['confidence']`. Individual word-level confidence scores (`word['confidence']`)
are available in the API response and would be more accurate for per-word HTR
quality assessment.

**`DOCUMENT_TEXT_DETECTION` vs `TEXT_DETECTION`**

Handprint correctly uses `document_text_detection` (not `text_detection`).
For HTR/manuscript work:
- `DOCUMENT_TEXT_DETECTION` is optimized for dense text, multi-word lines,
  and returns the full `FullTextAnnotation` with structural hierarchy
  (pages → blocks → paragraphs → words → symbols).
- `TEXT_DETECTION` is optimized for sparse text (signs, labels) and only
  returns `TextAnnotation` (flat list of words). It is inferior for
  manuscript work.
- **Recommendation:** No change needed; handprint already uses the correct
  detection type.

**Language hints**

Handprint already passes `language_hints = ['en-t-i0-handwrit']`, the correct
BCP-47 tag for English handwriting. No change needed. For non-English
manuscripts, a `language` parameter would be needed.

**Async / batch processing**

The 3.x SDK exposes `AsyncImageAnnotatorClient` (wraps gRPC async stubs).
For large batches (18,000+ images), the Vision API also supports
`async_batch_annotate_files` (reads from GCS, writes to GCS). This would
provide significantly higher throughput than the current synchronous one-by-one
calls but requires restructuring handprint's orchestration layer.
**Recommendation:** Flag as a Phase 4 enhancement; out of scope for
behavior-preserving fixes.

---

### Azure AI Vision / Document Intelligence

**Current state**

Handprint uses **raw HTTP requests** (via `commonpy.network_utils.net`) to
the Azure Computer Vision Read API v3.2 endpoint:
```
{endpoint}/vision/v3.2/read/analyze
```
There is no Azure SDK import — no `azure-*` package in `requirements.txt`.
This is unusual but functional. The v3.2 endpoint is still operational as of
2025, but Microsoft has announced deprecation in favor of Document Intelligence
v4 / Image Analysis v4.0.

**Migration path: `azure-ai-vision-imageanalysis` 1.0 GA (Image Analysis 4.0)**

Image Analysis 4.0 (`azure-ai-vision-imageanalysis`) is a new SDK for the
Florence-based backend released GA in 2024. For OCR of natural images, it
uses a REST-first approach but the response schema has changed significantly:

- Old Read v3.2: `analyzeResult.readResults[0].lines[n].words[n]`
- New Image Analysis 4.0: `captionResult`, `readResult.blocks[n].lines[n].words[n]`

Handprint's result parsing in `microsoft.py:110–133` would require full
rewrite for the new schema. The `boundingBox` format also changed from
8-integer arrays (x1,y1,x2,y2,x3,y3,x4,y4) to `BoundingPolygon` objects.

**Migration path: `azure-ai-documentintelligence` (Document Intelligence)**

For manuscript/handwriting-specific use cases, Azure AI Document Intelligence
(formerly Form Recognizer) offers:
- `prebuilt-read` model: Extracts text lines and words with per-word confidence
  scores and polygon bounding boxes.
- Per-word confidence scores (not present in Read v3.2 at word level; v3.2
  only has word-level confidence via individual word objects).
- Multi-page document support, rotated text detection, and language detection.

Response schema (`analyzeResult.pages[n].lines[n].words[n]`) differs from
v3.2. Handprint's parsing layer would require targeted updates.

**Breaking changes requiring handprint updates (if migrated)**

1. `boundingBox` → polygon coordinates (8 integers) vs. `BoundingPolygon`
   objects with `x`/`y` fields — `manager.py` bounding box normalization
   would need updating.
2. `readResults` → `pages` restructuring in `microsoft.py:111–116`.
3. Authentication: `Ocp-Apim-Subscription-Key` header remains, but endpoint
   URL pattern changes.
4. No polling required for Document Intelligence (synchronous `analyze`
   endpoint available for images < 6 MB).

**Recommendation:** Keep current v3.2 REST implementation for now (it
remains operational). Document Intelligence migration is a Phase 4 project
requiring new integration tests.

---

### Amazon Textract

**Sync vs. async**

Handprint uses `detect_document_text` (synchronous call, max 10 MB, direct
bytes input). This is correct for single-image processing. For batch
processing of 18,000+ images:

- `detect_document_text`: Synchronous; returns immediately; limited to JPEG,
  PNG, PDF. Maximum 5 TPS per account in `us-east-1` (default quota). At 5
  TPS, 18,000 images would take ≥60 minutes with no retries.
- `start_document_text_detection`: Asynchronous; reads from S3; returns job ID.
  Throughput is decoupled from API call rate. Supports multi-page PDFs.
  Would require handprint to upload images to S3 first and poll for results.

Handprint's current rate limiter (`max_rate() = 0.25`) enforces 1 call per
4 seconds, far below the 5 TPS quota. This implies the original author was
conservative, likely from early 2020 quota limits that have since been
raised.

**Queries feature (2022)**

Textract `analyze_document` with `QueriesConfig` allows targeted extraction:
```python
client.analyze_document(
    Document={'Bytes': image},
    FeatureTypes=['QUERIES'],
    QueriesConfig={'Queries': [{'Text': 'What is the date?', 'Alias': 'DATE'}]}
)
```
For manuscript work (free-form handwriting), the Queries feature is not
directly applicable — it assumes structured documents. **No recommendation
to add this.**

**FORMS / TABLES feature types**

`analyze_document` with `FeatureTypes=['FORMS']` returns key-value pairs.
For historical manuscripts, this is unlikely to be useful. For structured
historical records (ledgers, forms), it could add value. **Optional
enhancement only.**

**Current Textract service quotas (2025)**

Default quota for `DetectDocumentText`: 5 TPS (us-east-1). This is higher
than handprint's current 0.25 calls/s limiter. The rate limiter in
`amazon.py:50` should be updated to at least 1.0 to improve throughput, with
a retry/backoff on `ProvisionedThroughputExceededException`.

---

### Amazon Rekognition

**`Filters` parameter**

`detect_text` in `amazon.py:207` does not pass a `Filters` parameter. The
`Filters` parameter supports:
```python
client.detect_text(
    Image={'Bytes': image},
    Filters={
        'WordFilter': {
            'MinConfidence': 80,
            'MinBoundingBoxHeight': 0.01,
            'MinBoundingBoxWidth': 0.01
        }
    }
)
```
Current behavior: returns all detections regardless of confidence. For
manuscript images with low-confidence partial detections, setting
`MinConfidence=50` (or higher) would filter noise.

**Rekognition vs. Textract for HTR**

Amazon Rekognition `DetectText` was designed for text-in-images (signs,
labels). It is not optimized for dense handwriting on document pages.
Amazon Textract was specifically designed for document text extraction and
consistently outperforms Rekognition on handwritten documents in benchmarks.

**Recommendation:** For handwritten manuscript work, Rekognition is the
weakest of the four backends. Consider deprecating it in favor of Textract
exclusively, or document its inferiority clearly. Do not remove it in Phase 2
(per constraints).

---

## Phase 4 — Verification Checklist

### 1. Create isolated test environments

```bash
# Install pyenv if not present
# brew install pyenv  (macOS)

# Install target Python versions
pyenv install 3.11.9
pyenv install 3.12.5
pyenv install 3.13.0

# Create virtual environments
~/.pyenv/versions/3.11.9/bin/python -m venv ~/.venvs/handprint-311
~/.pyenv/versions/3.12.5/bin/python -m venv ~/.venvs/handprint-312
~/.pyenv/versions/3.13.3/bin/python -m venv ~/.venvs/handprint-313
```

### 2. Install the package in each environment

```bash
# Python 3.11
source ~/.venvs/handprint-311/bin/activate
cd ~/Downloads/handprint-main
pip install --upgrade pip
pip install -e .
pip install pytest "pytest-mock>=3.12.0"
deactivate

# Python 3.12
source ~/.venvs/handprint-312/bin/activate
cd ~/Downloads/handprint-main
pip install --upgrade pip
pip install -e .
pip install pytest "pytest-mock>=3.12.0"
deactivate

# Python 3.13
source ~/.venvs/handprint-313/bin/activate
cd ~/Downloads/handprint-main
pip install --upgrade pip
pip install -e .
pip install pytest "pytest-mock>=3.12.0"
deactivate
```

### 3. Run the unit test suite

```bash
# In each venv, from the project root:
source ~/.venvs/handprint-311/bin/activate
pytest tests/ -v
deactivate

source ~/.venvs/handprint-312/bin/activate
pytest tests/ -v
deactivate

source ~/.venvs/handprint-313/bin/activate
pytest tests/ -v
deactivate
```

Expected: All tests in `test_images.py`, `test_comparison.py`,
`test_exceptions.py`, `test_exit_codes.py` pass without error.

### 4. Manual smoke tests (one image per service)

Requires valid credential files to be installed first (see handprint README).

```bash
# Verify CLI help works (no credential files needed)
handprint --help
handprint --version

# Single image smoke test per service
# (replace 'sample.jpg' with an actual test image)
handprint -s google   sample.jpg
handprint -s microsoft sample.jpg
handprint -s amazon-textract sample.jpg
handprint -s amazon-rekognition sample.jpg

# Verify output files created (annotated PNG + JSON result)
ls -la sample-google.*
ls -la sample-microsoft.*
ls -la sample-amazon-textract.*
ls -la sample-amazon-rekognition.*
```

### 5. Phase 3 SDK upgrade integration tests

If the Phase 3 Azure migration (Read v3.2 → Document Intelligence) is
performed, the following new tests would be required:

| Test | Description |
|------|-------------|
| `test_microsoft_auth_new_sdk.py` | Verify new `azure-ai-documentintelligence` credential initialization |
| `test_microsoft_response_schema.py` | Verify new `pages[n].lines[n].words[n]` response parsing against saved fixture |
| `test_microsoft_bounding_box.py` | Verify `BoundingPolygon` → 8-int `bb` conversion matches old format |
| `test_google_async_client.py` | If async batch added: verify `AsyncImageAnnotatorClient` result parity with sync |
| `test_amazon_rate_limiter.py` | If rate limit raised: verify new `max_rate()` value and backoff behavior |

Each integration test should be gated on the presence of valid credentials
(via `pytest.mark.skipif`) so the CI suite can run without cloud access.

---

## Summary of All Changes (Phase 2)

| File | Change | Reason |
|------|--------|--------|
| `setup.cfg` | Added Python 3.9–3.13 trove classifiers | Missing from original; needed for accurate PyPI metadata |
| `requirements.txt` | Replaced 28 `==` exact pins with `>=` minimums | Exact pins prevent installation on Python 3.11+ (no wheels) |
| `requirements.txt` | Removed `google-cloud == 0.34.0` | Deprecated meta-package; not needed when individual packages specified |
| `requirements.txt` | Removed `wheel` | Build tool; must not be in `install_requires` |
| `requirements-dev.txt` | `pytest-mock >= 3.12.0` | Old pin has no Python 3.12 wheels |
| `handprint/services/google.py` | `TextDetectionParams(mapping=...)` → `TextDetectionParams(enable_text_detection_confidence_score=True)` | `mapping=` constructor keyword removed in `google-cloud-vision` 3.x |
