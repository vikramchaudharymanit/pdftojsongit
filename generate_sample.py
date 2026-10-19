"""
Generate a sample PDF for testing the PDF → JSON converter.
Creates a multi-page document with a clear title and H1/H2/H3 headings
using PyMuPDF (fitz) — no external dependencies needed.
"""

import fitz


def _add_text(page: fitz.Page, x: float, y: float, text: str,
              fontsize: float = 11.0, bold: bool = False) -> float:
    """Insert a line of text and return the new y position."""
    fontname = "helv"
    page.insert_text(
        (x, y),
        text,
        fontname=fontname,
        fontsize=fontsize,
        color=(0, 0, 0),
    )
    return y + fontsize * 1.5


def _add_paragraph(page: fitz.Page, x: float, y: float, text: str,
                   fontsize: float = 11.0, max_width: float = 475.0) -> float:
    """Word-wrap and insert a paragraph; return y after the paragraph."""
    words = text.split()
    line: list[str] = []
    for word in words:
        test_line = " ".join(line + [word])
        # Rough char-width estimate: fontsize * 0.5 per character
        if len(test_line) * fontsize * 0.5 > max_width and line:
            page.insert_text((x, y), " ".join(line), fontname="helv",
                             fontsize=fontsize, color=(0.15, 0.15, 0.15))
            y += fontsize * 1.6
            line = [word]
        else:
            line.append(word)
    if line:
        page.insert_text((x, y), " ".join(line), fontname="helv",
                         fontsize=fontsize, color=(0.15, 0.15, 0.15))
        y += fontsize * 1.6
    return y + fontsize * 0.5


def make_sample_pdf(path: str) -> None:
    doc = fitz.open()

    # ── Page 1 ────────────────────────────────────────────────────────────────
    page1 = doc.new_page(width=595, height=842)
    y = 80.0

    # Title (24 pt)
    page1.insert_text((130, y), "Machine Learning in Healthcare",
                      fontname="helv", fontsize=24, color=(0, 0, 0))
    y += 50

    # Abstract body text
    y = _add_paragraph(page1, 60, y,
        "This paper presents an overview of machine learning applications in "
        "the healthcare domain, covering diagnosis, prognosis, treatment "
        "recommendation, and clinical workflow optimisation.",
        fontsize=11)
    y += 10

    # H1 — Introduction (18 pt)
    page1.insert_text((60, y), "Introduction", fontname="helv", fontsize=18)
    y += 30

    y = _add_paragraph(page1, 60, y,
        "Machine learning has emerged as a transformative technology in medicine. "
        "From early cancer detection to personalised drug dosing, the potential "
        "applications are vast and growing rapidly.",
        fontsize=11)
    y += 10

    # H2 — Motivation (14 pt)
    page1.insert_text((60, y), "Motivation", fontname="helv", fontsize=14)
    y += 24

    y = _add_paragraph(page1, 60, y,
        "The exponential growth of electronic health records, medical imaging, "
        "and wearable sensor data has created an opportunity for data-driven "
        "decision support systems.",
        fontsize=11)
    y += 10

    # H3 — Data Sources (12 pt)
    page1.insert_text((60, y), "Data Sources", fontname="helv", fontsize=12)
    y += 22

    y = _add_paragraph(page1, 60, y,
        "Primary data sources include EHR systems, PACS imaging archives, "
        "insurance claims databases, and prospective clinical trial datasets.",
        fontsize=11)

    # ── Page 2 ────────────────────────────────────────────────────────────────
    page2 = doc.new_page(width=595, height=842)
    y = 70.0

    # H1 — Dataset Collection
    page2.insert_text((60, y), "Dataset Collection", fontname="helv", fontsize=18)
    y += 30

    y = _add_paragraph(page2, 60, y,
        "We collected data from three hospital systems spanning five years. "
        "All data were de-identified in accordance with HIPAA regulations "
        "before being ingested into the training pipeline.",
        fontsize=11)
    y += 10

    # H2 — Preprocessing
    page2.insert_text((60, y), "Preprocessing", fontname="helv", fontsize=14)
    y += 24

    y = _add_paragraph(page2, 60, y,
        "Raw records were normalised, missing values were imputed using "
        "median substitution for continuous variables and mode imputation "
        "for categorical variables.",
        fontsize=11)
    y += 10

    # H3 — Feature Engineering
    page2.insert_text((60, y), "Feature Engineering", fontname="helv", fontsize=12)
    y += 22

    y = _add_paragraph(page2, 60, y,
        "Temporal features were computed using a sliding window approach. "
        "Demographic variables were one-hot encoded. Lab values were "
        "standardised to z-scores.",
        fontsize=11)

    # ── Page 3 ────────────────────────────────────────────────────────────────
    page3 = doc.new_page(width=595, height=842)
    y = 70.0

    # H1 — Model Architecture
    page3.insert_text((60, y), "Model Architecture", fontname="helv", fontsize=18)
    y += 30

    y = _add_paragraph(page3, 60, y,
        "We evaluated three families of models: gradient-boosted trees, "
        "deep neural networks, and transformer-based architectures applied "
        "to sequential clinical data.",
        fontsize=11)
    y += 10

    # H2 — Transformer Encoder
    page3.insert_text((60, y), "Transformer Encoder", fontname="helv", fontsize=14)
    y += 24

    y = _add_paragraph(page3, 60, y,
        "The transformer encoder processes time-ordered event sequences "
        "with multi-head self-attention, allowing the model to capture "
        "long-range dependencies between clinical events.",
        fontsize=11)
    y += 10

    # H3 — Positional Encoding
    page3.insert_text((60, y), "Positional Encoding", fontname="helv", fontsize=12)
    y += 22

    y = _add_paragraph(page3, 60, y,
        "Time-aware positional encodings encode the actual elapsed time "
        "between events rather than using fixed sinusoidal encodings.",
        fontsize=11)
    y += 10

    # H1 — Results
    page3.insert_text((60, y), "Results", fontname="helv", fontsize=18)
    y += 30

    y = _add_paragraph(page3, 60, y,
        "The transformer model achieved an AUROC of 0.923 on the held-out "
        "test set, outperforming the gradient-boosted baseline by 4.1 "
        "percentage points and the deep neural network by 2.6 points.",
        fontsize=11)
    y += 10

    # H1 — Conclusion
    page3.insert_text((60, y), "Conclusion", fontname="helv", fontsize=18)
    y += 30

    _add_paragraph(page3, 60, y,
        "Transformer-based models show strong promise for clinical risk "
        "stratification. Future work will explore federated learning to "
        "train across institutions without sharing raw patient data.",
        fontsize=11)

    doc.save(path)
    doc.close()
    print(f"[OK] Sample PDF written to: {path}")


if __name__ == "__main__":
    make_sample_pdf("sample.pdf")
