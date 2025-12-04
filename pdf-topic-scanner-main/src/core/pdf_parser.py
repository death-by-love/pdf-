"""PDF Parsing: Extracts text, layout, font info using pdfplumber."""

from typing import List, Dict
import pdfplumber

from utils.logger import get_logger

Y_TOLERANCE = 5  # default units for grouping words into lines
CHARACTER_FRAGMENT_THRESHOLD = 1.5  # max width (in points) to consider a word a character fragment

logger = get_logger(__name__)


def _merge_character_fragments(words: List[Dict]) -> str:
    """Intelligently merge words/character fragments into a single text string.

    Detects character fragments (single chars or very short sequences) and merges them
    without spaces. Adds spaces between actual words based on horizontal distance.

    Args:
        words: List of word dicts from pdfplumber (must have 'text', 'x0', 'x1', 'size').
    Returns:
        Merged text string with proper spacing.
    """
    if not words:
        return ""

    result = []
    avg_char_width = words[0].get("size", 12) * 0.5  # Rough estimate: char width ~ font_size/2

    for i, word in enumerate(words):
        text = word["text"]
        
        # Skip empty words
        if not text:
            continue

        # Add space before this word if:
        # 1. Not the first word
        # 2. Previous word doesn't look like a fragment
        # 3. Gap between previous word and this word is significant
        if result and i > 0:
            prev_word = words[i - 1]
            prev_x1 = prev_word.get("x1", 0)
            curr_x0 = word.get("x0", 0)
            gap = curr_x0 - prev_x1

            # Add space if gap is larger than ~40% of average character width
            # This handles proper word separation vs. character fragment sequences
            if gap > avg_char_width * 0.4:
                result.append(" ")

        result.append(text)

    return "".join(result)


def parse_pdf(pdf_path: str, y_tolerance: int = Y_TOLERANCE) -> List[Dict]:
    """Extracts per-line blocks from a PDF, merging words into lines based on y-coordinate proximity.

    Args:
        pdf_path (str): Path to PDF file.
        y_tolerance (int): Max vertical distance for grouping words as a single line.
    Returns:
        List[Dict]: List of line-level blocks with text and layout info.
    Raises:
        Exception: if pdfplumber cannot open or parse the file.
    """
    blocks: List[Dict] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):

                words = page.extract_words(
                    extra_attrs=["fontname", "size", "x0", "x1", "top", "bottom"]
                )
                if not words:
                    continue

                # Sort by vertical position, then horizontal
                words = sorted(words, key=lambda w: (w["top"], w["x0"]))

                # Line grouping
                lines: List[List[Dict]] = []
                current_line: List[Dict] = []
                current_top = None

                for word in words:
                    word_top = word["top"]

                    if current_line and abs(word_top - current_top) > y_tolerance:
                        lines.append(current_line)
                        current_line = []
                        current_top = None

                    if not current_line:
                        current_top = word_top

                    current_line.append(word)

                if current_line:
                    lines.append(current_line)

                # Convert each line to a block
                for line_words in lines:
                    text = _merge_character_fragments(line_words).strip()
                    if not text:
                        continue

                    font_family = line_words[0]["fontname"]
                    font_size = float(line_words[0]["size"])

                    is_bold = "bold" in font_family.lower()
                    is_italic = "italic" in font_family.lower() or "oblique" in font_family.lower()

                    x0 = min(w["x0"] for w in line_words)
                    x1 = max(w["x1"] for w in line_words)
                    y0 = min(w["top"] for w in line_words)
                    y1 = max(w["bottom"] for w in line_words)

                    block = {
                        "text": text,
                        "page": page_num,
                        "font_size": font_size,
                        "font_family": font_family,
                        "is_bold": is_bold,
                        "is_italic": is_italic,
                        "bbox": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
                    }

                    blocks.append(block)

        # Sort final result: page → y → x
        blocks.sort(key=lambda b: (b["page"], b["bbox"]["y0"], b["bbox"]["x0"]))
        return blocks

    except Exception as e:
        logger.error(f"Failed to parse PDF '{pdf_path}': {e}")
        raise Exception(f"PDF parsing failed for {pdf_path}: {e}")


# ---- TESTING SECTION ----
if __name__ == "__main__":
    import sys

    # If user passes a file, use it. Otherwise use your test file.
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "tests/sample_pdfs/simple_doc.pdf"

    print(f"Parsing: {pdf_path}\n")

    try:
        blocks = parse_pdf(pdf_path)
        for block in blocks[:5]:   # print first 5 blocks only
            print(block, "\n")
    except Exception as e:
        print(f"Error: {e}")
