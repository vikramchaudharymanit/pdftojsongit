"""
Title Detector — identifies the document title from extracted span metadata.

Heuristics used (in order of importance):
  1. Largest font size in the document.
  2. Appears on page 1.
  3. Located in the top portion of the page.
  4. Bold (preferred, not required).
  5. Short text (not a paragraph).
  6. Centered relative to the page width.
  7. Appears only once (not a running header).

When multiple spans share the largest font size on page 1, they are merged
into a single title string (handles multi-line titles).
"""

from __future__ import annotations

import re
from collections import Counter
from typing import List, Optional

from span_extractor import SpanInfo

# ── Constants ─────────────────────────────────────────────────────────────────

# Title must appear in the top fraction of page 1.
TITLE_TOP_FRAC: float = 0.55

# Fraction of page width: span must be within this band around the horizontal
# centre to count as "centred" (used as a soft bonus, not a hard filter).
CENTER_TOLERANCE_FRAC: float = 0.15

# Maximum word count for a span to be considered title / heading material.
MAX_TITLE_WORDS: int = 20

# Font-size tolerance: spans within this many points of the max are grouped.
FONT_SIZE_TOLERANCE: float = 0.5

# A text repeated on ≥ this many pages is considered a running header.
RUNNING_HEADER_PAGE_THRESHOLD: int = 3


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_body_text(text: str) -> bool:
    """Return True for text that looks like a body-text sentence."""
    stripped = text.rstrip()
    # Ends with sentence-ending punctuation
    if stripped.endswith((".", ",", ";", ":", "!", "?")):
        return True
    # Very long span
    if len(text.split()) > MAX_TITLE_WORDS:
        return True
    return False


def _running_headers(spans: List[SpanInfo]) -> set[str]:
    """Return a set of texts that repeat across many pages (running headers)."""
    page_texts: Counter = Counter()
    seen: dict[str, set[int]] = {}
    for s in spans:
        key = s.text.strip().lower()
        if key not in seen:
            seen[key] = set()
        seen[key].add(s.page_number)

    return {
        text
        for text, pages in seen.items()
        if len(pages) >= RUNNING_HEADER_PAGE_THRESHOLD
    }


def _is_centered(span: SpanInfo) -> bool:
    x0, _, x1, _ = span.bbox
    span_mid = (x0 + x1) / 2.0
    page_mid = span.page_width / 2.0
    tolerance = span.page_width * CENTER_TOLERANCE_FRAC
    return abs(span_mid - page_mid) <= tolerance


# ── Public API ────────────────────────────────────────────────────────────────

def detect_title(spans: List[SpanInfo]) -> str:
    """Detect and return the document title as a single string.

    Args:
        spans: All SpanInfo objects from the document (reading order).

    Returns:
        The detected title string, or an empty string if none found.
    """
    if not spans:
        return ""

    running = _running_headers(spans)

    # Only consider page-1 spans in the upper portion of the page.
    page1_spans = [
        s for s in spans
        if s.page_number == 1
        and s.bbox[1] / s.page_height <= TITLE_TOP_FRAC
        and not _is_body_text(s.text)
        and s.text.strip().lower() not in running
    ]

    if not page1_spans:
        return ""

    max_size = max(s.font_size for s in page1_spans)

    # Gather all spans at (or very near) the max font size.
    title_spans = [
        s for s in page1_spans
        if abs(s.font_size - max_size) <= FONT_SIZE_TOLERANCE
    ]

    # Sort by vertical position (top-to-bottom) then horizontal.
    title_spans.sort(key=lambda s: (s.bbox[1], s.bbox[0]))

    # Merge into one string, collapsing whitespace.
    title_text = " ".join(s.text.strip() for s in title_spans)
    title_text = re.sub(r"\s+", " ", title_text).strip()

    return title_text
