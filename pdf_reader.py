"""
PDF Reader — opens a PDF document via PyMuPDF.
"""

from pathlib import Path
import fitz  # PyMuPDF


def open_pdf(pdf_path: Path) -> fitz.Document:
    """Open and return a PyMuPDF Document object.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        An open fitz.Document instance.

    Raises:
        SystemExit: If the file cannot be opened as a valid PDF.
    """
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:  # fitz raises RuntimeError on bad files
        import sys
        print(f"[ERROR] Cannot open PDF: {exc}", file=sys.stderr)
        sys.exit(1)

    return doc
