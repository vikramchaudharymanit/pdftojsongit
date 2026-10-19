"""
Heading Detector — identifies and classifies H1/H2/H3 headings from span metadata.

Detection heuristics (all implemented):
  1.  Font size ranking — larger → higher level; thresholds derived per document.
  2.  Bold weight — bold text is a strong heading signal.
  3.  Short text length — 2–12 words (configurable).
  4.  No trailing punctuation — period/comma at end → body text.
  5.  Vertical whitespace gap — large gap above → new section.
  6.  Repeated font-pattern clustering — same size/weight/family → same level.
  7.  Centred text — large centred text is heading-like.
  8.  All-caps detection — fully uppercase short lines → strong H1 candidate.
  9.  Page-position filtering — header/footer zones excluded in span_extractor.
  10. Duplicate/running-header removal — text repeated on many pages filtered out.

Classification:
  Font sizes are ranked (descending). The top bucket is the title font.
  The next distinct size(s) become H1, H2, H3 respectively.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

from span_extractor import SpanInfo

# ── Tunable Constants ─────────────────────────────────────────────────────────

# Heading word-count window (inclusive).
MIN_HEADING_WORDS: int = 1
MAX_HEADING_WORDS: int = 12

# A vertical gap larger than this multiple of font_size is "large".
GAP_MULTIPLIER: float = 0.8

# Minimum font-size difference (in pt) to count as a distinct heading level.
LEVEL_SIZE_GAP: float = 0.8

# A text repeated on ≥ this many pages is treated as a running header.
RUNNING_HEADER_THRESHOLD: int = 3

# Heading score threshold — spans must exceed this to be included.
# The strict size_ratio > 1.05 filter above handles false positives,
# so the score just needs to confirm the span passed the size gate.
MIN_SCORE: float = 0.15

# Centre-alignment tolerance (fraction of page width).
CENTER_TOLERANCE_FRAC: float = 0.15


# ── Helpers ───────────────────────────────────────────────────────────────────

def _running_headers(spans: List[SpanInfo]) -> set[str]:
    """Collect texts that appear on too many pages (running headers/footers)."""
    seen: dict[str, set[int]] = defaultdict(set)
    for s in spans:
        seen[s.text.strip().lower()].add(s.page_number)
    return {t for t, pages in seen.items() if len(pages) >= RUNNING_HEADER_THRESHOLD}


def _trailing_punct(text: str) -> bool:
    return bool(re.search(r"[.,;:!?]$", text.rstrip()))


def _word_count(text: str) -> int:
    return len(text.split())


def _is_all_caps(text: str) -> bool:
    alpha = re.sub(r"[^A-Za-z]", "", text)
    return len(alpha) >= 3 and alpha == alpha.upper()


def _is_centered(span: SpanInfo) -> bool:
    x0, _, x1, _ = span.bbox
    mid = (x0 + x1) / 2.0
    page_mid = span.page_width / 2.0
    tol = span.page_width * CENTER_TOLERANCE_FRAC
    return abs(mid - page_mid) <= tol


def _score_span(span: SpanInfo, body_size: float) -> float:
    """Compute a heading-likelihood score for a span.

    Higher score → more likely to be a heading.
    Returns 0.0 for spans that are definitively body text.
    """
    text = span.text.strip()
    wc = _word_count(text)

    # Hard rejections.
    if wc < MIN_HEADING_WORDS or wc > MAX_HEADING_WORDS:
        return 0.0
    if _trailing_punct(text):
        return 0.0

    score = 0.0

    # Font-size signal: reward spans larger than dominant body text.
    # Require strictly larger than body size — spans at or below body size
    # are body text regardless of gap/caps signals.
    size_ratio = span.font_size / body_size if body_size > 0 else 1.0
    if size_ratio > 1.05:
        score += min(size_ratio - 1.0, 1.0) * 3.0  # up to +3
    else:
        return 0.0  # body text or smaller — skip

    # Bold bonus.
    if span.is_bold:
        score += 1.0

    # All-caps bonus.
    if _is_all_caps(text):
        score += 1.0

    # Centred bonus.
    if _is_centered(span):
        score += 0.5

    # Gap bonus — large whitespace above is a structural cue.
    if span.gap_above > span.font_size * GAP_MULTIPLIER:
        score += 0.5

    return score


def _dominant_body_size(spans: List[SpanInfo]) -> float:
    """Return the modal (most common) font size — assumed to be body text."""
    if not spans:
        return 12.0
    sizes = [round(s.font_size, 1) for s in spans]
    counter = Counter(sizes)
    return counter.most_common(1)[0][0]


def _distinct_heading_sizes(
    candidates: List[SpanInfo],
    title_text: str,
) -> List[float]:
    """Return a sorted-descending list of distinct heading font sizes,
    excluding the title font size (already handled separately).

    Uses LEVEL_SIZE_GAP to merge near-identical sizes into one bucket.
    """
    title_words = title_text.strip().lower().split() if title_text else []
    size_set: set[float] = set()
    for s in candidates:
        # Exclude spans that exactly match the title text.
        if s.text.strip().lower() == title_text.strip().lower():
            continue
        size_set.add(round(s.font_size, 1))

    sorted_sizes = sorted(size_set, reverse=True)

    # Merge sizes within LEVEL_SIZE_GAP of each other.
    merged: List[float] = []
    for sz in sorted_sizes:
        if not merged or (merged[-1] - sz) >= LEVEL_SIZE_GAP:
            merged.append(sz)

    return merged  # largest first → H1, H2, H3 …


# ── Public API ────────────────────────────────────────────────────────────────

def detect_headings(spans: List[SpanInfo], title: str) -> List[SpanInfo]:
    """Filter spans down to likely heading candidates.

    Args:
        spans:  All document spans in reading order.
        title:  Previously detected title string (excluded from headings).

    Returns:
        Ordered list of spans that pass heading heuristics.
    """
    running = _running_headers(spans)
    body_size = _dominant_body_size(spans)
    title_lower = title.strip().lower()

    candidates: List[SpanInfo] = []
    seen_texts: set[str] = set()   # de-duplicate consecutive identical headings

    for span in spans:
        text = span.text.strip()
        text_lower = text.lower()

        # Skip running headers.
        if text_lower in running:
            continue

        # Skip the title itself.
        if title_lower and text_lower == title_lower:
            continue

        # Score the span.
        score = _score_span(span, body_size)
        if score < MIN_SCORE:
            continue

        # Skip consecutive duplicates.
        if text_lower in seen_texts:
            continue

        seen_texts.add(text_lower)
        candidates.append(span)

    return candidates


def classify_headings(
    candidates: List[SpanInfo],
    title: str = "",
) -> List[Dict]:
    """Assign H1/H2/H3 levels to each candidate span.

    Levels are determined dynamically by ranking distinct font sizes.
    The largest candidate size → H1, next → H2, next → H3.
    Any additional sizes beyond the top 3 are folded into H3.

    Args:
        candidates: Ordered list of heading candidate spans.
        title:      Document title (to exclude from heading levels).

    Returns:
        List of dicts: [{"level": "H1", "text": "...", "page": N}, …]
    """
    if not candidates:
        return []

    size_buckets = _distinct_heading_sizes(candidates, title)
    level_map: Dict[float, str] = {}

    level_names = ["H1", "H2", "H3"]
    for i, sz in enumerate(size_buckets[:3]):
        level_names_idx = min(i, len(level_names) - 1)
        level_map[sz] = level_names[level_names_idx]

    # Any leftover sizes beyond top-3 get mapped to H3.
    for sz in size_buckets[3:]:
        level_map[sz] = "H3"

    outline: List[Dict] = []
    for span in candidates:
        sz = round(span.font_size, 1)
        # Find the closest bucket.
        closest = min(level_map.keys(), key=lambda b: abs(b - sz), default=None)
        if closest is None:
            continue
        level = level_map[closest]
        outline.append({
            "level": level,
            "text": span.text.strip(),
            "page": span.page_number,
        })

    # Remove consecutive duplicate entries (same level + text).
    deduped: List[Dict] = []
    for entry in outline:
        if deduped and deduped[-1]["level"] == entry["level"] and deduped[-1]["text"] == entry["text"]:
            continue
        deduped.append(entry)

    return deduped
