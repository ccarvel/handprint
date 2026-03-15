# Handprint — Modernized for Python 3.11–3.14<img width="12%" align="right" src="https://raw.githubusercontent.com/caltechlibrary/handprint/develop/.graphics/noun_Hand_733265.png">

The _**Hand**written **P**age **R**ecognit**i**o**n** **T**est_ is a command-line program that invokes HTR (handwritten text recognition) services on images of document pages. It can produce annotated images showing the results, compare the recognized text to expected text, save the HTR service results as JSON and text files, and more.

> **This is a modernized fork of [handprint v1.6.0](https://github.com/caltechlibrary/handprint).**
> The original repository targets Python ≤ 3.10 due to pinned dependencies.
> This version runs on **Python 3.8 through 3.14+** with no source-code behavior changes.
> See [What changed](#what-changed) for a full list of modifications.

[![Python](https://img.shields.io/badge/Python-3.8--3.14-brightgreen.svg?style=flat-square)](http://shields.io)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg?style=flat-square)](https://choosealicense.com/licenses/bsd-3-clause)


## Table of Contents

* [What changed](#what-changed)
* [Introduction](#introduction)
* [Image requirements and preprocessing](#image-requirements-and-preprocessing)
  * [Accepted formats](#accepted-formats)
  * [Service limits](#service-limits)
  * [Automatic preprocessing pipeline](#automatic-preprocessing-pipeline)
  * [Effective limits by service combination](#effective-limits-by-service-combination)
  * [Output image characteristics](#output-image-characteristics)
* [Installation and configuration](#installation-and-configuration)
  * [Install from source (recommended for this modernized version)](#install-from-source-recommended-for-this-modernized-version)
  * [Install with pip or pipx](#install-with-pip-or-pipx)
  * [Add cloud service credentials](#-add-cloud-service-credentials)
* [Usage](#usage)
* [Running the test suite](#running-the-test-suite)
* [Getting help](#getting-help)
* [License](#license)
* [Authors and history](#authors-and-history)
* [Acknowledgments](#acknowledgments)


---

## What changed

All existing CLI interfaces, output formats, file naming conventions, and
service logic are preserved exactly. The changes are limited to dependency
pinning and one API constructor call.

### `requirements.txt` — dependency unpinning

The original file pinned 28 packages with `==` exact versions from 2021–2022.
Most of those packages do not publish binary wheels for Python 3.11 or 3.12,
causing `pip install` to fail before any handprint code runs. All `==` pins
have been replaced with `>=` minimum versions chosen to be the oldest release
with Python 3.12 wheel support.

Key version floor changes:

| Package | Was | Now |
|---------|-----|-----|
| `numpy` | `== 1.22.2` | `>= 1.26.0` |
| `matplotlib` | `== 3.4.2` | `>= 3.7.0` |
| `Pillow` | `== 9.0.1` | `>= 10.0.0` |
| `grpcio` | `== 1.44.0` | `>= 1.59.0` |
| `google-cloud-vision` | `== 2.3.1` | `>= 3.4.0` |
| `google-api-core` | `== 1.30.0` | `>= 2.11.0` |
| `google-auth` | `== 1.30.2` | `>= 2.22.0` |
| `boto3` | `== 1.17.91` | `>= 1.28.0` |
| `PyMuPDF` | `== 1.19.6` | `>= 1.23.0` |
| `requests` | `== 2.25.0` | `>= 2.31.0` |

Two entries were removed entirely:
- `google-cloud == 0.34.0` — deprecated meta-package (last release 2018); not needed when individual packages are specified.
- `wheel == 0.36.2` — build tool that must not appear in `install_requires`.

### `handprint/services/google.py` — `TextDetectionParams` constructor

The `mapping=` keyword argument to protobuf-generated classes was removed in
`google-cloud-vision` 3.x. Changed:

```python
# Before (breaks on google-cloud-vision >= 3.0):
params = gv.TextDetectionParams(
    mapping = { 'enable_text_detection_confidence_score': True })

# After:
params = gv.TextDetectionParams(
    enable_text_detection_confidence_score = True)
```

### `handprint/comparison.py` — replaced `StringDist` with `textdistance`

`StringDist 1.0.9` (the sole and final release) contains a C extension that
uses a legacy `PyArg_ParseTuple` format character removed in Python 3.12,
producing `SystemError: argument 1 (impossible<bad format char>)` at runtime.
The package is abandoned (last update 2018) and will never be fixed.

The `textdistance` package — already a handprint dependency, used in the same
file for LCSSEQ scoring — provides an identical integer Levenshtein distance
function. The one `from stringdist import levenshtein` call has been replaced
with `from textdistance import levenshtein as _lev`, and `levenshtein(a, b)`
with `_lev.distance(a, b)`. Results are numerically identical.

### `setup.cfg` — added Python 3.9–3.13 PyPI classifiers

The original file only declared `Programming Language :: Python :: 3.8`.
Added classifiers for 3.9, 3.10, 3.11, 3.12, and 3.13.

### `requirements-dev.txt` — updated `pytest-mock`

`pytest-mock == 3.7.0` → `pytest-mock >= 3.12.0` for Python 3.12 compatibility.

---

## Introduction

Handprint (_**Hand**written **P**age **R**ecognit**i**o**n** **T**est_) is a
tool for comparing alternative services for offline
[handwritten text recognition (HTR)](https://en.wikipedia.org/wiki/Handwriting_recognition).
It was developed for use with documents from the
[Caltech Archives](http://archives.caltech.edu), but it is completely
independent and can be applied to any images of text documents.

Handprint can generate images with recognized text overlaid on them to
visualize results. Among other features, it can also display bounding boxes,
threshold results by confidence values, compare full-text results to
expected/ground-truth results, and output the raw results from an HTR service
as JSON and text files. It can work with individual images, directories of
images, and URLs pointing to images on remote servers. Finally, Handprint can
use multiple processor threads for parallel execution.

Services supported include Google's
[Google Cloud Vision API](https://cloud.google.com/vision/docs/ocr),
Microsoft's Azure [Computer Vision API](https://azure.microsoft.com/en-us/services/cognitive-services/computer-vision/),
and Amazon's [Textract](https://aws.amazon.com/textract/) and
[Rekognition](https://aws.amazon.com/rekognition/).


---

## Image requirements and preprocessing

This section documents what Handprint accepts as input and exactly what it
does to images before sending them to a cloud service. All of this behaviour
is derived directly from the source code (`images.py`, `manager.py`,
`services/*.py`).

### Accepted formats

Handprint accepts the following input file formats:

| Format | Extensions |
|--------|-----------|
| JPEG | `.jpg`, `.jpeg` |
| JPEG 2000 | `.jp2` |
| PNG | `.png` |
| PDF | `.pdf` |
| GIF | `.gif` |
| BMP | `.bmp` |
| TIFF | `.tif`, `.tiff` |

Images can be provided as local file paths, directories of files, or URLs.
For URLs, Handprint checks that the server reports a content-type of
`image/*` before downloading; non-image URLs are skipped with a warning.

**PDF files:** Only the first page is extracted and processed. If a PDF
contains more than one page, all pages beyond the first are silently ignored.
Page extraction uses PyMuPDF.

**Zero-length files** are rejected immediately with a warning.

---

### Service limits

Each cloud service imposes its own constraints. These values are hardcoded in
the service classes and are what Handprint enforces before sending anything:

| Service | Max file size | Max pixel dimensions |
|---------|--------------|---------------------|
| Google Cloud Vision | 10 MB | none |
| Microsoft Azure (Read v3.2) | 4 MB | 10,000 × 10,000 px |
| Amazon Textract | 10 MB | none |
| Amazon Rekognition | 10 MB | none |

**Notes on the limits:**
- Google's documentation states a 20 MB limit, but the JSON-over-gRPC
  transport used by the Python SDK hits a 10 MB ceiling in practice; the
  code caps at 10 MB accordingly.
- Microsoft's documentation states a 6 MB free-tier limit, but the actual
  enforcement threshold is 4 MB; the code uses 4 MB.

---

### Automatic preprocessing pipeline

Before sending any image to a service, Handprint runs it through a fixed
preprocessing pipeline. Steps are applied in this order:

**1. Format conversion to PNG**

All inputs — regardless of original format — are converted to PNG. PNG is
the one format accepted by all four services. The converted file is written
alongside the output as `originalname.handprint.png`.

Conversion uses Pillow for all formats except PDF, which uses PyMuPDF.
Images are converted to RGB colour space during this step.

**2. Dimension reduction (if needed)**

If the image's pixel dimensions exceed the limit for any of the selected
services, the image is proportionally scaled down so that neither width nor
height exceeds the cap. The scaling factor is:

```
ratio = min(max_width / current_width, max_height / current_height)
```

Aspect ratio is always preserved. Resampling uses Pillow's `HAMMING` filter.

**3. File size reduction (if needed)**

If the PNG file is still larger than the file-size cap after dimension
reduction, it is scaled down further. The scaling factor is:

```
ratio = max_allowed_bytes / current_file_size
```

Both width and height are multiplied by `√ratio` (i.e., area is scaled
proportionally to the size ratio). Aspect ratio is preserved. Resampling
again uses the `HAMMING` filter.

**Key point — all services in a run share the same image.** When you invoke
multiple services at once, Handprint calculates the *most restrictive* limit
across all selected services and normalises every image to that single limit
before dispatching. This ensures results are comparable across services, but
means that a service capable of accepting a larger image will receive a
smaller one than it could handle.

**Temporary file handling:**
- The normalized `.handprint.png` file is deleted at the end of the run
  unless `-e` (extended output) mode is active.
- With `-e`, the normalized copy is retained alongside the JSON and text
  output files.
- If a `.handprint.png` file already exists from a previous run and is
  already within the size limits, Handprint reuses it rather than
  regenerating it.

---

### Effective limits by service combination

| Services selected | File size cap | Dimension cap |
|------------------|--------------|---------------|
| Google only | 10 MB | none |
| Microsoft only | 4 MB | 10,000 × 10,000 px |
| Amazon Textract only | 10 MB | none |
| Amazon Rekognition only | 10 MB | none |
| Google + Amazon (either) | 10 MB | none |
| Microsoft + any other | **4 MB** | **10,000 × 10,000 px** |
| All four services | **4 MB** | **10,000 × 10,000 px** |

> **Practical implication:** If you are running all four services and your
> scanned document pages are large high-resolution images (common in archival
> digitisation work), they will be downscaled to fit within Microsoft's 4 MB
> ceiling before being sent to *all* services — including Google and Amazon,
> which could each accept the full-resolution image. If maximum recognition
> quality from Google or Amazon is important, consider running them separately
> (without Microsoft) so the 10 MB limit applies.

---

### Output image characteristics

The annotated result images Handprint produces are generated at:

- **300 DPI**
- **20 × 20 inch figure canvas** (i.e., 6,000 × 6,000 px at 300 DPI before
  tight-cropping)
- **PNG format** (always, regardless of the input format)
- Matplotlib's PDF backend is used internally to avoid threading artefacts;
  the final output is still written as PNG.

When multiple services are run together, a grid image combining all annotated
results is also produced, named `originalname.handprint-all.png`. The grid
layout is approximately square (number of columns ≈ √n where n is the number
of services).


---

## Installation and configuration

### Install from source (recommended for this modernized version)

This approach installs from the local source tree into an isolated virtual
environment, which avoids conflicts with any other Python tools on your system
and ensures you are running the modernized code rather than an older installed
version.

**Step 1 — Create a virtual environment**

Choose the Python version you want to use (3.8 through 3.14 are all supported):

```sh
# Using a pyenv-managed Python (recommended):
~/.pyenv/versions/3.13.3/bin/python -m venv ~/.venvs/handprint

# Or using whatever python3 is on your PATH:
python3 -m venv ~/.venvs/handprint
```

**Step 2 — Activate the environment**

```sh
source ~/.venvs/handprint/bin/activate
```

You can confirm you are in the right environment:

```sh
which handprint
# Should show nothing yet (not installed) or the venv path after install
```

**Step 3 — Install handprint and its dependencies**

```sh
cd /path/to/handprint-main
pip install --upgrade pip
pip install -e .
```

**Step 4 — Verify the installation**

```sh
handprint --help
handprint --version
```

> **Important:** Always activate the virtual environment before running
> handprint. If you have an older standalone `handprint` binary installed
> elsewhere on your system (e.g., in `/usr/local/bin`), it will take
> precedence when the venv is not active. Run `which handprint` to confirm
> you are using the venv's copy.

To deactivate the environment when you are done:

```sh
deactivate
```


### Install with pip or pipx

If you prefer a simpler install and are running Python 3.11 or newer, you
can install directly with pip:

```sh
pip install -e /path/to/handprint-main
```

Or with [pipx](https://pypa.github.io/pipx/) for automatic environment
isolation:

```sh
pipx install /path/to/handprint-main
```


### ⓶ _Add cloud service credentials_

A one-time configuration step is needed for each cloud-based HTR service.
This step supplies Handprint with credentials to access the services. In
each case, the same command format is used:

```sh
handprint -a SERVICENAME CREDENTIALSFILE.json
```

`SERVICENAME` must be one of the service names printed by running
`handprint -l`. When you run this command, Handprint copies
`CREDENTIALSFILE.json` to a private location and thereafter uses the
credentials to access that service. On macOS the private location is
`~/Library/Application Support/Handprint/`.


#### Microsoft

Create a JSON file with the following format:

```json
{
  "subscription_key": "YOURKEYHERE",
  "endpoint": "https://ENDPOINT"
}
```

The subscription key and endpoint URI are obtained from the
[Azure portal](https://portal.azure.com). Notes on obtaining these can be
found in the
[Handprint project Wiki](https://github.com/caltechlibrary/handprint/wiki/Getting-Microsoft-Azure-credentials).

```sh
handprint -a microsoft myazurecredentials.json
```

> **Note:** This modernized version still uses the Azure Computer Vision
> Read API v3.2 REST endpoint. Microsoft has announced eventual deprecation
> of v3.2 in favor of Azure AI Document Intelligence. The v3.2 endpoint
> remains operational as of 2025. See `MODERNIZATION_AUDIT.md` for migration
> guidance when it becomes necessary.


#### Google

Credentials for a Google service account are stored in a JSON file with
this general structure:

```json
{
  "type": "service_account",
  "project_id": "theid",
  "private_key_id": "thekey",
  "private_key": "-----BEGIN PRIVATE KEY-----...-----END PRIVATE KEY-----\n",
  "client_email": "emailaddress",
  "client_id": "id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "someurl"
}
```

Instructions for obtaining this file are in the
[Handprint project Wiki](https://github.com/caltechlibrary/handprint/wiki/Getting-Google-Cloud-credentials).

```sh
handprint -a google mygooglecredentials.json
```


#### Amazon

Amazon credentials require a key ID, a secret access key, and a region name,
stored in a JSON file:

```json
{
    "aws_access_key_id": "YOUR_KEY_ID_HERE",
    "aws_secret_access_key": "YOUR_ACCESS_KEY_HERE",
    "region_name": "YOUR_REGION_NAME_HERE"
}
```

Instructions for obtaining these are in the
[Handprint project Wiki](https://github.com/caltechlibrary/handprint/wiki/Creating-credentials-for-use-with-Amazon-Rekognition).
Use the same credentials file for both Amazon services:

```sh
handprint -a amazon-textract myamazoncredentials.json
handprint -a amazon-rekognition myamazoncredentials.json
```


---

## Usage

Please see the [documentation site](https://caltechlibrary.github.io/handprint)
for detailed documentation.

A brief reference is always available via:

```sh
handprint --help
```

Common invocations:

```sh
# Run all services on a single image
handprint image.jpg

# Run a specific service only
handprint -s google image.jpg
handprint -s microsoft image.jpg
handprint -s amazon-textract image.jpg
handprint -s amazon-rekognition image.jpg

# Run on a directory of images
handprint -s google /path/to/images/

# Produce extended output (JSON + text files in addition to annotated image)
handprint -e -s google image.jpg

# Compare results against ground-truth text
handprint -c -s google image.jpg   # requires image.gt.txt alongside image.jpg

# Show bounding boxes in addition to recognized text
handprint -d text,bb-word -s google image.jpg
```


---

## Running the test suite

With the virtual environment active and the package installed:

```sh
cd /path/to/handprint-main
pytest tests/ -v
```

Expected output: **12 tests passed** across `test_comparison.py`,
`test_exceptions.py`, `test_exit_codes.py`, and `test_images.py`.

To test across multiple Python versions:

```sh
# Python 3.11
source ~/.venvs/handprint-311/bin/activate
pytest tests/ -v
deactivate

# Python 3.12
source ~/.venvs/handprint-312/bin/activate
pytest tests/ -v
deactivate

# Python 3.13
source ~/.venvs/handprint-313/bin/activate
pytest tests/ -v
deactivate
```


---

## Getting help

If you find an issue, please submit it in
[the GitHub issue tracker](https://github.com/caltechlibrary/handprint/issues)
for this repository.


---

## License

Software produced by the Caltech Library is Copyright © 2018–2022 California
Institute of Technology. This software is freely distributed under the
[BSD 3-clause OSI license](https://opensource.org/licenses/BSD-3-Clause).
Please see the [LICENSE](LICENSE) file for more information.


---

## Authors and history

[Mike Hucka](https://github.com/mhucka) designed and implemented Handprint
beginning in mid-2018.

Modernization for Python 3.11–3.14 compatibility was performed in 2026.
See [`MODERNIZATION_AUDIT.md`](MODERNIZATION_AUDIT.md) and
[`CHANGES_SUMMARY.md`](CHANGES_SUMMARY.md) for full details.


---

## Acknowledgments

The [vector artwork](https://thenounproject.com/search/?q=hand&i=733265) of a
hand used as a logo for Handprint was created by
[Kevin](https://thenounproject.com/kevn/) for the
[Noun Project](https://thenounproject.com). It is licensed under the Creative
Commons [CC-BY 3.0](https://creativecommons.org/licenses/by/3.0/) license.

Handprint benefitted from feedback from Tommy Keswick, Mariella Soprano,
Peter Collopy, and Stephen Davison.

Handprint makes use of numerous open-source packages, without which it would
have been effectively impossible to develop. In alphabetical order:

* [aenum](https://pypi.org/project/aenum/) — advanced enumerations for Python
* [appdirs](https://github.com/ActiveState/appdirs) — platform-specific directory resolution
* [boltons](https://github.com/mahmoud/boltons/) — miscellaneous Python utilities
* [boto3](https://github.com/boto/boto3) — Amazon AWS SDK for Python
* [bun](https://github.com/caltechlibrary/bun) — basic user interface classes and functions
* [CommonPy](https://github.com/caltechlibrary/commonpy) — commonly-useful Python functions
* [fastnumbers](https://github.com/SethMMorton/fastnumbers) — number testing and conversion functions
* [google-api-core, google-api-python-client, google-auth, google-auth-httplib2, google-cloud-vision, googleapis-common-protos](https://github.com/googleapis/google-cloud-python) — Google API libraries
* [grpcio](https://grpc.io) — open-source RPC framework
* [humanize](https://github.com/jmoiron/humanize) — human-readable numbers
* [imagesize](https://github.com/shibukawa/imagesize_py) — image dimension detection
* [matplotlib](https://matplotlib.org) — Python 2-D plotting library
* [numpy](https://numpy.org) — scientific computing in Python
* [Pillow](https://github.com/python-pillow/Pillow) — Python Imaging Library fork
* [plac](http://micheles.github.io/plac/) — command-line argument parser
* [psutil](https://github.com/giampaolo/psutil) — process and system monitoring
* [PyMuPDF](https://github.com/pymupdf/PyMuPDF) — Python bindings for MuPDF
* [requests](http://docs.python-requests.org) — HTTP library for Python
* [Rich](https://rich.readthedocs.io/en/latest/) — styled terminal output
* [setuptools](https://github.com/pypa/setuptools) — package build tooling
* [Sidetrack](https://github.com/caltechlibrary/sidetrack) — debug logging/tracing
* [textdistance](https://github.com/orsinium/textdistance) — text sequence distance metrics (replaces StringDist for Python 3.12+ compatibility)
* [urllib3](https://github.com/urllib3/urllib3) — Python HTTP library
* [Validator Collection](https://github.com/insightindustry/validator-collection) — validator functions

Finally, I am grateful for computing &amp; institutional resources made
available by the California Institute of Technology.

<div align="center">
  <a href="https://www.caltech.edu">
    <img width="120px" src="https://raw.githubusercontent.com/caltechlibrary/handprint/master/.graphics/caltech-round.png">
  </a>
</div>
