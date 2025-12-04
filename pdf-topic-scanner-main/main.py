"""CLI entry point for DocTree.AI PDF Hierarchy Extractor

Usage:
    python main.py <input.pdf> [--out <output.json>] [--stats]
"""

import argparse
import os
import json
import time
from typing import Any

from src.core.pdf_parser import parse_pdf
from src.features.feature_engineer import enrich_blocks_with_features
from src.hierarchy.heading_classifier import classify_headings
from src.hierarchy.tree_builder import build_hierarchy

DEFAULT_OUTPUT_DIR = "outputs/json"


def section_stats(sections):
    """Returns top-level section count and total nested sections recursively."""
    def count_sections(subsections):
        return sum(1 + count_sections(s.get("children", [])) for s in subsections)
    return len(sections), count_sections(sections)


def main():
    parser = argparse.ArgumentParser(description="DocTree.AI PDF Hierarchy Extractor")
    parser.add_argument("pdf_path", help="Input PDF file path")
    parser.add_argument("--out", help="Output JSON path")
    parser.add_argument("--stats", action="store_true", help="Show hierarchy stats")
    args = parser.parse_args()

    pdf_path = args.pdf_path
    out_path = args.out

    if not os.path.exists(pdf_path):
        print(f"[ERROR] File not found -> {pdf_path}")
        return

    basename = os.path.splitext(os.path.basename(pdf_path))[0]
    if not out_path:
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        out_path = os.path.join(DEFAULT_OUTPUT_DIR, f"{basename}.json")

    # Optional: Get input PDF file size
    try:
        size_kb = os.path.getsize(pdf_path) / 1024
    except OSError:
        size_kb = None

    t0 = time.time()
    try:
        blocks = parse_pdf(pdf_path)
        enriched = enrich_blocks_with_features(blocks)
        classified = classify_headings(enriched)

        page_numbers = [b.get("page", 1) for b in classified]
        total_pages = max(page_numbers) if page_numbers else 0
        metadata = {
            "source_file": pdf_path,
            "total_blocks": len(classified),
            "total_pages": total_pages,
        }

        tree = build_hierarchy(classified, metadata)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}")
        return

    num_h1 = sum(1 for b in classified if b.get("classification") == "H1")
    num_h2 = sum(1 for b in classified if b.get("classification") == "H2")
    num_h3 = sum(1 for b in classified if b.get("classification") == "H3")
    elapsed = time.time() - t0

    print("\n[DONE] DocTree.AI Extraction Complete")
    print(f"File:   {pdf_path}")
    if size_kb is not None:
        print(f"File size: {size_kb:.1f} KB")
    print(f"Blocks parsed: {len(classified)}")
    print(f"Pages: {total_pages}")
    print(f"Detected: {num_h1} H1, {num_h2} H2, {num_h3} H3 headings")
    print(f"JSON saved to: {out_path}")
    print(f"Time taken: {elapsed:.2f} seconds\n")

    # Optional: show hierarchy stats
    if args.stats:
        sections = tree.get("sections", [])
        top, total = section_stats(sections)
        print(f"Top-level sections: {top}")
        print(f"Total (nested) sections: {total}")


if __name__ == "__main__":
    main()
