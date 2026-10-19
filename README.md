# PDF to JSON Converter

A fully offline, production-quality tool that extracts a PDF document's **title** and **heading hierarchy** (H1 / H2 / H3) and writes them to a structured JSON file.

No LLMs, no OCR services, no external API calls — pure heuristic/rule-based extraction powered by **PyMuPDF (`fitz`)**.

---

## Features

| Feature | Detail |
|---|---|
| Title detection | Largest font on page 1, top half, not repeated across pages |
| Heading detection | 10 heuristics: font size, bold, word count, punctuation, gap, caps, centering, clustering, position, deduplication |
| Dynamic thresholds | All font-size levels derived per document — no hardcoded pt values |
| Scanned PDF safety | Falls back to empty outline instead of crashing |
| Running header removal | Text repeated on ≥ 3 pages is automatically filtered out |
| O(S) complexity | Linear scan over spans — scales to large PDFs |

---

## Requirements

- Python 3.10+
- [PyMuPDF](https://pymupdf.readthedocs.io/) (`pip install PyMuPDF`)

---

## Local Setup

```bash
# 1. Clone / download the source
cd pdf2json

# 2. Create a virtual environment (recommended)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## CLI Usage

```bash
python main.py <input.pdf> <output.json>
```

### Example

```bash
python main.py sample.pdf output.json
```

Console output:

```
[INFO] Opening PDF: sample.pdf
[INFO] Extracting text spans …
[INFO] Collected 1423 spans across 22 pages.
[INFO] Detecting title …
[INFO] Title: 'Attention Is All You Need'
[INFO] Detecting headings …
[INFO] Found 18 heading entries.
[OK] Output written to: output.json
```

Resulting `output.json`:

```json
{
  "title": "Attention Is All You Need",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H1", "text": "Background", "page": 2 },
    { "level": "H2", "text": "Encoder and Decoder Stacks", "page": 3 },
    { "level": "H2", "text": "Attention", "page": 3 },
    { "level": "H3", "text": "Scaled Dot-Product Attention", "page": 4 },
    { "level": "H3", "text": "Multi-Head Attention", "page": 4 },
    { "level": "H1", "text": "Training", "page": 6 },
    { "level": "H2", "text": "Training Data and Batching", "page": 6 },
    { "level": "H2", "text": "Hardware and Schedule", "page": 6 },
    { "level": "H1", "text": "Results", "page": 7 }
  ]
}
```

---

## Docker Usage

### Build

```bash
docker build -t pdf2json .
```

### Run

```bash
# Linux / macOS
docker run --rm -v $(pwd):/data pdf2json /data/input.pdf /data/output.json

# Windows (PowerShell)
docker run --rm -v ${PWD}:/data pdf2json /data/input.pdf /data/output.json
```

The container reads from and writes to `/data` inside the container, which is mounted from your current working directory.

---

## Project Structure

```
pdf2json/
├── main.py             # CLI entry point & pipeline orchestrator
├── pdf_reader.py       # Opens the PDF via PyMuPDF
├── span_extractor.py   # Walks block/line/span tree, collects metadata
├── title_detector.py   # Detects the document title
├── heading_detector.py # Detects & classifies H1/H2/H3 headings
├── json_writer.py      # Builds and writes the JSON output
├── requirements.txt    # PyMuPDF dependency
├── Dockerfile          # Multi-stage container image
└── README.md           # This file
```

---

## Heuristic Rules Explained

### Title Detection

| Rule | Logic |
|---|---|
| Largest font | Max `font_size` across all page-1 spans |
| Page position | Span must be in the top 55 % of page 1 |
| Not a running header | Text must not repeat on ≥ 3 pages |
| Short text | Must not look like a paragraph (no trailing `.`, ≤ 20 words) |
| Multi-line merge | Multiple spans at the same max size are joined into one string |

### Heading Detection & Classification

| Heuristic | Implementation |
|---|---|
| **1. Font size ranking** | Body size = modal font size; candidates must be ≥ body size |
| **2. Bold weight** | +1.0 score if `flags & 16` (PyMuPDF bold bit) |
| **3. Short text** | 1–12 words; longer spans are rejected |
| **4. No trailing punctuation** | Regex check for `. , ; : ! ?` at end |
| **5. Vertical gap** | +0.5 score if `gap_above > font_size × 1.2` |
| **6. Font pattern clustering** | Distinct sizes ranked → H1 / H2 / H3 buckets |
| **7. Centred text** | +0.5 if span midpoint within 15 % of page centre |
| **8. All-caps** | +1.0 if all alphabetic chars are uppercase |
| **9. Page-position filter** | Top 7 % / bottom 7 % of each page excluded in extractor |
| **10. Running-header removal** | Text on ≥ 3 pages → filtered before scoring |

Level assignment is dynamic: the three largest distinct font-size buckets among all candidates become H1, H2, and H3 respectively. Any additional sizes collapse into H3.

---

## Tunable Constants

All thresholds live as named constants at the top of each module — easy to adjust for specific document styles:

| Constant | File | Default | Purpose |
|---|---|---|---|
| `HEADER_MARGIN_FRAC` | `span_extractor.py` | 0.07 | Top/bottom dead-zone fraction |
| `TITLE_TOP_FRAC` | `title_detector.py` | 0.55 | Title must be in top 55 % of page 1 |
| `MAX_HEADING_WORDS` | `heading_detector.py` | 12 | Max words for a heading candidate |
| `GAP_MULTIPLIER` | `heading_detector.py` | 1.2 | Gap threshold multiplier |
| `LEVEL_SIZE_GAP` | `heading_detector.py` | 0.8 pt | Min pt difference for separate heading levels |
| `MIN_SCORE` | `heading_detector.py` | 1.5 | Minimum score to include a candidate |
| `RUNNING_HEADER_THRESHOLD` | `heading_detector.py` | 3 | Pages threshold for running-header detection |

---

## Stretch Goals (Future Work)

The following were intentionally not implemented but are documented here for reference:

- **ML-based heading classification** — use font size, position, boldness, spacing, length as features for a lightweight classifier
- **Layout-aware models** — LayoutLM / DocFormer for complex two-column or magazine-style layouts
- **OCR integration** — Tesseract for scanned PDFs with no embedded text
- **Table extraction** — Camelot / Tabula
- **Figure/image detection** with caption extraction
- **Named Entity Recognition** on headings/body text
- **REST API wrapper** — FastAPI/Flask
- **Web UI** — upload PDF, preview/edit headings, download JSON

---

## License

MIT
"# pdftojsongit" 
