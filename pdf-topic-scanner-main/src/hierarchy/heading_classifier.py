"""Classifies each block into H1/H2/H3/BODY using engineered features.

Assigns each block a heading_score (float in [0, 1]) and a classification
("H1", "H2", "H3", "BODY") based on feature heuristics.
"""

from typing import List, Dict, Optional
from src.config import HEADING_SCORE_THRESHOLDS

MAX_POSSIBLE_SCORE = 11.0


def classify_headings(
    blocks: List[Dict],
    thresholds: Optional[Dict[str, float]] = None
) -> List[Dict]:
    """For feature-enriched blocks, computes heading_score and classification.

    Args:
        blocks (List[Dict]): feature-enriched blocks.
        thresholds (dict, optional): override for score thresholds.
    Returns:
        List[Dict]: blocks, each with 'heading_score' and 'classification' added.
    """
    if thresholds is None:
        thresholds = HEADING_SCORE_THRESHOLDS

    classified = []
    max_block = None  # Track the highest-scoring non-BODY block on page 1

    for block in blocks:
        features = block.get("features", {})
        raw_score = _compute_raw_score(features)
        heading_score = _normalize_score(raw_score)
        classification = _assign_level(heading_score, thresholds)
        block["heading_score"] = heading_score
        block["classification"] = classification

        # Track best heading on page 1 for promotion to H1
        if block["page"] == 1 and classification != "BODY":
            if max_block is None or heading_score > max_block["heading_score"]:
                max_block = block

        classified.append(block)

    # Promote best heading on first page to H1 (hackathon hack for demo)
    if max_block is not None:
        max_block["classification"] = "H1"

    return classified


def _compute_raw_score(f: Dict) -> float:
    """Compute raw heading score from features dict.

    Sums contributions from font rank, relative size, boldness,
    numbering, casing, and shortness.
    """
    score = 0.0

    # Font rank (1 = largest on page)
    font_rank = f.get("font_rank", 7)
    if font_rank == 1:
        score += 4.0
    elif font_rank == 2:
        score += 3.0
    elif font_rank == 3:
        score += 2.0
    elif font_rank <= 5:
        score += 1.0

    # Relative size (vs body text)
    relative_size = f.get("relative_size", 1.0)
    if relative_size >= 1.6:
        score += 2.0
    elif relative_size >= 1.3:
        score += 1.5
    elif relative_size >= 1.1:
        score += 1.0

    # Bold
    if f.get("is_bold", False):
        score += 1.5

    # Numbering
    if f.get("has_numbering", False):
        score += 1.0

    # Casing
    if f.get("is_all_caps", False):
        score += 1.0
    elif f.get("is_title_case", False):
        score += 0.5

    # Shortness (headings are usually short)
    if f.get("is_short", False):
        score += 1.0

    return score


def _normalize_score(raw_score: float) -> float:
    """Normalize raw score into [0, 1] range."""
    norm = raw_score / MAX_POSSIBLE_SCORE
    norm = min(max(norm, 0.0), 1.0)
    return round(norm, 3)


def _assign_level(score: float, thresholds: Dict[str, float]) -> str:
    """Assign heading level based on score and thresholds."""
    h1 = thresholds.get("H1", 0.8)
    h2 = thresholds.get("H2", 0.6)
    h3 = thresholds.get("H3", 0.4)

    if score >= h1:
        return "H1"
    elif score >= h2:
        return "H2"
    elif score >= h3:
        return "H3"
    return "BODY"


# --- manual test: run on a sample PDF for demonstration ---
if __name__ == "__main__":
    from src.core.pdf_parser import parse_pdf
    from src.features.feature_engineer import enrich_blocks_with_features

    sample_pdf = "tests/sample_pdfs/simple_doc.pdf"
    blocks = parse_pdf(sample_pdf)
    enriched = enrich_blocks_with_features(blocks)
    classified = classify_headings(enriched)

    # Print the first 20 lines with their classification and score
    for b in classified[:20]:
        print(f"[{b['classification']}] {b['heading_score']} -> {b['text']}")
