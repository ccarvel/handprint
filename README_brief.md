# Handprint — Brief Overview

## What it does

Handprint sends images of handwritten documents to cloud OCR/HTR services and
collects the results. For each image it can:

- Produce an annotated PNG with the recognized text overlaid on the original
- Draw bounding boxes around recognized words, lines, and paragraphs
- Save the raw service response as a JSON file and the extracted text as a `.txt` file
- Compare recognized text against a ground-truth file and report character error rate (CER)
- Combine results from multiple services into a single side-by-side grid image

Four services are supported:

| Service | What it uses |
|---------|-------------|
| Google | Cloud Vision API — `DOCUMENT_TEXT_DETECTION` (optimized for dense/handwritten text) |
| Microsoft | Azure Computer Vision Read API v3.2 (async REST, polls for result) |
| Amazon Textract | `DetectDocumentText` — document-oriented text extraction |
| Amazon Rekognition | `DetectText` — image-oriented text detection |

## How it works

1. **Input** — accepts image files (JPG, PNG, PDF, TIFF, GIF, BMP), directories, or URLs
2. **Preprocessing** — converts everything to PNG; downsizes to the lowest size limit among the chosen services (e.g., 4 MB when Microsoft is included)
3. **Dispatch** — sends each image to the selected services in parallel threads
4. **Normalization** — maps each service's response into a common structure: a list of `Box` objects (kind, bounding box coordinates, text, confidence score) plus a full-text string
5. **Output** — writes annotated images, optional JSON/text files, optional comparison TSV

## How it was modernized

The original codebase (v1.6.0, last updated June 2024) was constrained to
Python ≤ 3.10 by pinned dependencies, not by the source code itself. Three
changes were needed:

1. **Dependency unpinning** (`requirements.txt`) — 28 packages were pinned to
   2021–2022 exact versions with no Python 3.11/3.12 wheels. Replaced all
   `==` pins with `>=` minimums that support Python 3.12+.

2. **Google SDK constructor fix** (`services/google.py`) — the `mapping=`
   keyword argument to `TextDetectionParams` was removed in
   `google-cloud-vision` 3.x. Updated to direct keyword syntax.

3. **StringDist replacement** (`comparison.py`) — `StringDist 1.0.9` is an
   abandoned package whose C extension crashes on Python 3.12+ with a
   `SystemError`. Replaced with `textdistance` (already a dependency) which
   provides the same integer Levenshtein distance.

No CLI flags, output formats, service logic, or behavioral defaults were changed.

## Quick start

```sh
# Install into a virtual environment
python3 -m venv ~/.venvs/handprint
source ~/.venvs/handprint/bin/activate
pip install -e /path/to/handprint-main

# Add credentials (one time per service)
handprint -a google     mygooglecreds.json
handprint -a microsoft  myazurecreds.json
handprint -a amazon-textract    myawscreds.json
handprint -a amazon-rekognition myawscreds.json

# Run
handprint -s google image.jpg
handprint image.jpg          # all services
```
