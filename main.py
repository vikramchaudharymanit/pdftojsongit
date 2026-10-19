"""
PDF to JSON Converter — main entry point.

Modes
-----
Single file:
    python main.py input.pdf output.json

Batch (all PDFs in a folder → output folder):
    python main.py                          # uses ./input/ and ./output/
    python main.py --batch                  # same as above
    python main.py --batch --input-dir path/to/pdfs --output-dir path/to/jsons

Pipeline (per file):
    1. Open PDF with PyMuPDF
    2. Extract per-span metadata (text, font size, bold, bbox, page)
    3. Detect the document title
    4. Detect and classify headings (H1/H2/H3)
    5. Write structured JSON output
"""

import sys
import json
import argparse
from pathlib import Path

from pdf_reader import open_pdf
from span_extractor import extract_spans
from title_detector import detect_title
from heading_detector import detect_headings, classify_headings
from json_writer import build_output, write_json

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_INPUT_DIR  = Path("input")
DEFAULT_OUTPUT_DIR = Path("output")


# ── Core pipeline ─────────────────────────────────────────────────────────────

def run(pdf_path: Path, output_path: Path) -> bool:
    """Run the full PDF → JSON conversion pipeline for one file.

    Returns True on success, False if the file produced no usable output.
    """
    print(f"\n[INFO] -- Processing: {pdf_path.name}")
    doc = open_pdf(pdf_path)

    print(f"[INFO] Extracting text spans ...")
    spans = extract_spans(doc)
    print(f"[INFO] Collected {len(spans)} spans across {doc.page_count} pages.")

    if not spans:
        print("[WARN] No text spans found — the PDF may be scanned/image-only.")
        result = {"title": "", "outline": []}
        write_json(result, output_path)
        print(f"[OK] (empty) Output written to: {output_path}")
        return False

    print("[INFO] Detecting title ...")
    title = detect_title(spans)
    print(f"[INFO] Title: {title!r}")

    print("[INFO] Detecting headings ...")
    candidates = detect_headings(spans, title)
    outline = classify_headings(candidates)
    print(f"[INFO] Found {len(outline)} heading entries.")

    result = build_output(title, outline)
    write_json(result, output_path)
    print(f"[OK] Output written to: {output_path}")
    return True


# ── Batch mode ────────────────────────────────────────────────────────────────

def run_batch(input_dir: Path, output_dir: Path) -> None:
    """Process all PDF files found in *input_dir* and write JSONs to *output_dir*."""
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(input_dir.glob("*.pdf")) + sorted(input_dir.glob("*.PDF"))
    # Deduplicate in case the glob finds the same file twice on case-insensitive FS.
    seen: set[Path] = set()
    pdf_files = [p for p in pdf_files if not (p in seen or seen.add(p))]

    if not pdf_files:
        print(f"[WARN] No PDF files found in: {input_dir.resolve()}")
        print(f"       Drop your PDFs into that folder and re-run.")
        return

    print(f"[INFO] Found {len(pdf_files)} PDF(s) in '{input_dir}'.")
    ok = failed = 0

    for pdf_path in pdf_files:
        output_path = output_dir / (pdf_path.stem + ".json")
        try:
            success = run(pdf_path, output_path)
            if success:
                ok += 1
            else:
                failed += 1
        except Exception as exc:
            print(f"[ERROR] Failed to process {pdf_path.name}: {exc}")
            failed += 1

    print(f"\n{'-'*50}")
    print(f"[DONE] {ok} succeeded, {failed} failed/empty.")
    print(f"       JSON files written to: {output_dir.resolve()}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="PDF to JSON Converter — extracts title and heading hierarchy.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file
  python main.py report.pdf report.json

  # Batch: convert everything in ./input/ → ./output/
  python main.py

  # Batch with custom folders
  python main.py --batch --input-dir my_pdfs/ --output-dir results/
        """,
    )

    # Positional args for single-file mode (both optional so batch is the default).
    parser.add_argument("pdf",  nargs="?", help="Input PDF file path.")
    parser.add_argument("json", nargs="?", help="Output JSON file path.")

    # Batch flags.
    parser.add_argument(
        "--batch", action="store_true",
        help="Batch-process all PDFs in --input-dir (default when no file args given).",
    )
    parser.add_argument(
        "--input-dir", type=Path, default=DEFAULT_INPUT_DIR,
        metavar="DIR", help=f"Folder containing input PDFs (default: {DEFAULT_INPUT_DIR}/).",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        metavar="DIR", help=f"Folder to write JSON output (default: {DEFAULT_OUTPUT_DIR}/).",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # ── Single-file mode: both positional args provided ───────────────────────
    if args.pdf and args.json:
        pdf_path    = Path(args.pdf)
        output_path = Path(args.json)
        if not pdf_path.exists():
            print(f"[ERROR] File not found: {pdf_path}", file=sys.stderr)
            sys.exit(1)
        run(pdf_path, output_path)
        return

    # ── Batch mode: no file args, or --batch flag ─────────────────────────────
    if args.pdf and not args.json:
        # Only one positional arg — ambiguous; treat as error.
        print("[ERROR] Provide both <input.pdf> and <output.json>, or use batch mode.",
              file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Default / explicit batch.
    run_batch(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
