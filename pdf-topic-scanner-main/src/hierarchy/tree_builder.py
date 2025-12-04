"""Tree building utilities for document hierarchy.

Builds nested hierarchy from classified blocks and serializes to JSON-compatible dict.
Implements build_hierarchy(blocks, metadata) that outputs:

{
    "metadata": {...},
    "sections": [
        { "title": ..., "content": [...], "children": [ ... ] },
        ...
    ]
}
using a stack-based algorithm for heading nesting.
"""

from typing import List, Dict, Any


def build_hierarchy(blocks: List[Dict], metadata: Dict) -> Dict:
    """Build nested hierarchy and output JSON serializable dict.

    Args:
        blocks (List[Dict]): classified blocks (must have 'classification').
        metadata (Dict): document-level metadata.

    Returns:
        Dict: {"metadata": ..., "sections": [...]}
    """
    sections: List[Dict] = []
    stack: List[Dict] = []

    # Helper to create a section
    def _new_section(title: str) -> Dict[str, Any]:
        return {"title": title, "content": [], "children": []}

    root_section = None

    for block in blocks:
        cls = block.get("classification", "BODY")
        text = block.get("text", "")
        if cls == "H1":
            section = _new_section(text)
            sections.append(section)
            stack = [section]  # always reset stack to this newest H1
        elif cls == "H2":
            # Attach to most recent H1 (stack[-1])
            if stack:
                parent = stack[-1]
                child = _new_section(text)
                parent["children"].append(child)
                # Stack = [current H1, new H2]
                if len(stack) > 1:
                    stack = stack[:1]
                stack.append(child)
            else:
                section = _new_section(text)
                sections.append(section)
                stack = [section]
        elif cls == "H3":
            # Attach to most recent H2 if it exists, otherwise to the latest H1
            if len(stack) >= 2:
                parent = stack[-1]
            elif stack:
                parent = stack[-1]
            else:
                parent = None

            child = _new_section(text)
            if parent:
                parent["children"].append(child)
                # Stack = [H1, H2, H3] (or just [parent, child])
                while len(stack) > 2:
                    stack.pop()
                stack.append(child)
            else:
                # No parent at all: treat as top-level
                sections.append(child)
                stack = [child]
        elif cls == "BODY":
            if stack:
                stack[-1]["content"].append(text)
            else:
                # No heading seen yet: create an implicit "Document" section
                if not root_section:
                    root_section = _new_section("Document")
                root_section["content"].append(text)
        else:
            # Should never happen, but safeguard: treat as body
            if stack:
                stack[-1]["content"].append(text)
            else:
                if not root_section:
                    root_section = _new_section("Document")
                root_section["content"].append(text)

    # If root_section used, insert it at index 0 so 'Document' is first
    if root_section and root_section["content"]:
        sections.insert(0, root_section)

    return {
        "metadata": metadata,
        "sections": sections,
    }


# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    # Minimal synthetic test
    test_blocks = [
        {"text": "Report Title", "classification": "H1"},
        {"text": "Executive Summary", "classification": "H2"},
        {"text": "This is the summary paragraph.", "classification": "BODY"},
        {"text": "1. Background", "classification": "H2"},
        {"text": "Background paragraph 1.", "classification": "BODY"},
        {"text": "1.1 Industry", "classification": "H3"},
        {"text": "Industry context...", "classification": "BODY"},
        {"text": "General Intro before any heading", "classification": "BODY"},
        {"text": "Methods", "classification": "H1"},
        {"text": "Data Collection", "classification": "H2"},
        {"text": "Collection process details...", "classification": "BODY"},
    ]
    metadata = {"title": "Demo Doc", "total_pages": 3, "generated_at": "2025-12-04T22:00:00Z"}
    tree = build_hierarchy(test_blocks, metadata)

    import json
    print(json.dumps(tree, indent=2))
