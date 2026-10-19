"""
Span Extractor — walks the PyMuPDF block/line/span tree and collects
per-span metadata needed by the detection stages.

Complexity: O(S) where S = total number of text spans in the document.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
import fitz  # PyMuPDF

# ── Constants ─────────────────────────────────────────────────────────────────

# Fraction of page height treated as header/footer dead-zones.
# Spans whose top-edge falls inside these margins are ignored.
# Note: page 1 titles often sit high on the page, so keep this tight.
HEADER_MARGIN_FRAC: float = 0.04   # top 4 % of page
FOOTER_MARGIN_FRAC: float = 0.06   # bottom 6 % of page

# Minimum number of printable characters for a span to be considered.
MIN_SPAN_CHARS: int = 2


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class SpanInfo:
    """All metadata extracted for one text span."""

    text: str
    font_size: float
    font_name: str
    is_bold: bool
    bbox: tuple[float, float, float, float]   # (x0, y0, x1, y1)
    page_number: int                           # 1-indexed
    page_width: float
    page_height: float
    block_index: int
    line_index: int
    # Vertical gap from the previous span on the same page (0 for first span).
    gap_above: float = field(default=0.0, init=False)


# ── Extraction ────────────────────────────────────────────────────────────────

def extract_spans(doc: fitz.Document) -> List[SpanInfo]:
    """Extract all text spans from every page of *doc*.

    Returns a flat list of SpanInfo objects in reading order
    (page-by-page, block-by-block, line-by-line, span-by-span).
    Header/footer zones are filtered out.
    """
    all_spans: List[SpanInfo] = []

    for page_index in range(doc.page_count):
        page = doc[page_index]
        page_number = page_index + 1
        pw = page.rect.width
        ph = page.rect.height
        header_limit = ph * HEADER_MARGIN_FRAC
        footer_limit = ph * (1.0 - FOOTER_MARGIN_FRAC)

        try:
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        except Exception:
            # Scanned / image-only page — skip silently.
            continue

        prev_y1: float = 0.0  # bottom edge of last accepted span on this page

        for b_idx, block in enumerate(blocks):
            if block.get("type") != 0:   # 0 = text block, 1 = image block
                continue

            for l_idx, line in enumerate(block.get("lines", [])):
                for span in line.get("spans", []):
                    raw_text: str = span.get("text", "").strip()
                    if len(raw_text) < MIN_SPAN_CHARS:
                        continue

                    bbox = span.get("bbox", (0, 0, 0, 0))
                    x0, y0, x1, y1 = bbox

                    # Drop header / footer zones.
                    if y0 < header_limit or y1 > footer_limit:
                        continue

                    font_size: float = round(span.get("size", 0.0), 2)
                    font_name: str = span.get("font", "")
                    flags: int = span.get("flags", 0)
                    # PyMuPDF bold flag: bit 4 (value 16) is bold.
                    is_bold: bool = bool(flags & 16)

                    info = SpanInfo(
                        text=raw_text,
                        font_size=font_size,
                        font_name=font_name,
                        is_bold=is_bold,
                        bbox=(x0, y0, x1, y1),
                        page_number=page_number,
                        page_width=pw,
                        page_height=ph,
                        block_index=b_idx,
                        line_index=l_idx,
                    )

                    # Compute vertical gap from previous accepted span.
                    info.gap_above = max(0.0, y0 - prev_y1)
                    prev_y1 = y1

                    all_spans.append(info)

    return all_spans
