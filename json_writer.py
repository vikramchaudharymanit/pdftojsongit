"""
JSON Writer — assembles the final output structure and writes it to disk.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def build_output(title: str, outline: List[Dict]) -> Dict:
    """Build the top-level output dictionary.

    Args:
        title:   Detected document title string.
        outline: List of heading dicts with keys level/text/page.

    Returns:
        Dict matching the required JSON schema.
    """
    return {
        "title": title,
        "outline": outline,
    }


def write_json(data: Dict, output_path: Path) -> None:
    """Serialise *data* to a pretty-printed JSON file.

    Creates parent directories if they do not exist.

    Args:
        data:        The dictionary to serialise.
        output_path: Destination file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
