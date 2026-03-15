# Modernization Changes Summary

Modernizes `handprint` for Python 3.11, 3.12, 3.13, and 3.14+.
All existing CLI interfaces, output formats, file naming conventions,
and service logic are preserved exactly.

---

## Files Changed

### `setup.cfg`

**What:** Added Python 3.9, 3.10, 3.11, 3.12, and 3.13 trove classifiers
to the `[metadata] classifiers` list.

**Why:** The original file only declared `Programming Language :: Python :: 3.8`.
This caused PyPI to show the package as 3.8-only, misleading users on newer
interpreters. The classifiers do not affect install behavior; they are metadata.

---

### `requirements.txt`

**What:** Replaced 28 `==` exact-version pins with `>=` minimum-version pins.
Also removed two entries:
- `google-cloud == 0.34.0` — deprecated meta-package (last release 2018);
  not needed when individual packages are specified directly.
- `wheel == 0.36.2` — build tool; should not appear in `install_requires`.

**Why:** Exact version pins from 2021–2022 do not publish binary wheels for
Python 3.11 or 3.12. When a user runs `pip install handprint` on Python 3.12,
pip either fails outright (no wheel, source compilation broken) or falls back
to building from source, which fails for compiled packages like `numpy`,
`grpcio`, `Pillow`, `PyMuPDF`, and `matplotlib`. The `>=` minimums chosen
are the oldest releases that:

1. Publish binary wheels for Python 3.12 (where applicable)
2. Are free of relevant known CVEs
3. Maintain API compatibility with existing handprint source code

Full per-package rationale is in `MODERNIZATION_AUDIT.md §1b`.

**Critical version bumps:**

| Package | Old | New minimum | Reason |
|---------|-----|-------------|--------|
| `numpy` | `== 1.22.2` | `>= 1.26.0` | 3.12 wheels |
| `matplotlib` | `== 3.4.2` | `>= 3.7.0` | 3.11/3.12 wheels |
| `Pillow` | `== 9.0.1` | `>= 10.0.0` | 3.12 wheels + CVE fixes |
| `grpcio` | `== 1.44.0` | `>= 1.59.0` | 3.12 wheels |
| `google-cloud-vision` | `== 2.3.1` | `>= 3.4.0` | 3.12 wheels; 3.x stable GA |
| `google-api-core` | `== 1.30.0` | `>= 2.11.0` | Required by vision 3.x |
| `google-auth` | `== 1.30.2` | `>= 2.22.0` | Required by api-core 2.x |
| `boto3` | `== 1.17.91` | `>= 1.28.0` | 3.11/3.12 wheels |
| `PyMuPDF` | `== 1.19.6` | `>= 1.23.0` | 3.11/3.12 wheels |
| `psutil` | `== 5.8.0` | `>= 5.9.0` | 3.12 wheels |
| `fastnumbers` | `== 3.1.0` | `>= 3.2.0` | 3.12 wheels |
| `requests` | `== 2.25.0` | `>= 2.31.0` | CVE-2023-32681 |
| `urllib3` | `== 1.26.5` | `>= 1.26.18` | CVE-2023-43804 |

---

### `requirements-dev.txt`

**What:** Changed `pytest-mock == 3.7.0` to `pytest-mock >= 3.12.0`.

**Why:** `pytest-mock 3.7.0` does not publish Python 3.12 wheels and is
incompatible with the latest `pytest` on 3.12+.

---

### `handprint/services/google.py`

**What:** Changed the `TextDetectionParams` constructor call (line 124) from:
```python
params = gv.TextDetectionParams(
    mapping = { 'enable_text_detection_confidence_score': True })
```
to:
```python
params = gv.TextDetectionParams(
    enable_text_detection_confidence_score = True)
```

**Why:** The `mapping=` keyword argument to protobuf-generated classes was a
legacy construction mechanism supported in `google-cloud-vision` 2.x but
removed in 3.x. With `google-cloud-vision >= 3.4.0` (required to install on
Python 3.12), calling `TextDetectionParams(mapping={...})` raises a `TypeError`
at runtime. The direct keyword argument syntax works in both 2.x and 3.x.

---

## Files Added

### `MODERNIZATION_AUDIT.md`

Full audit report covering:
- Python version incompatibility scan (all 24 source files)
- Dependency pinning risk table
- Service SDK/API version inventory
- API enhancement recommendations for all four cloud backends
- Verification checklist with exact commands

### `CHANGES_SUMMARY.md`

This file.

---

## Files Not Changed

All other source files are unchanged. The Python source code itself requires
no modifications for Python 3.11–3.14 compatibility — no deprecated stdlib
imports, no removed-module usage, no broken typing constructs were found.

The `setup.py` legacy entry point is left intact (functional, no errors on
3.11–3.14). Migration to `pyproject.toml` is recommended but deferred —
see `MODERNIZATION_AUDIT.md §Phase 3`.
