"""Streamlit UI for DocTree.AI - PDF Hierarchy Extractor"""

import streamlit as st
import tempfile
import os
import json
import time

from src.core.pdf_parser import parse_pdf
from src.features.feature_engineer import enrich_blocks_with_features
from src.hierarchy.heading_classifier import classify_headings
from src.hierarchy.tree_builder import build_hierarchy

st.set_page_config(page_title="DocTree.AI - PDF Hierarchy Extractor", page_icon="🌳", layout="wide")

# ---- Sidebar info ----
st.sidebar.header("🌳 DocTree.AI")
st.sidebar.markdown(
    """
    **PDF Hierarchy Extractor**

    - Upload a PDF
    - Click "Run Extraction"
    - View the section tree & download the results

    ---
    **How it works:**
    1. Extracts lines and layout from PDF
    2. Detects section headings using font/style/numbering
    3. Builds a nested tree of document hierarchy
    4. Outputs clean JSON
    """
)


def sidebar_toc(tree):
    """Display table of contents in sidebar"""
    if not tree:
        return
    st.sidebar.subheader("🔖 Document TOC")
    for section in tree.get("sections", []):
        _toc_section(section, indent=0)


def _toc_section(section, indent=0):
    """Recursively render TOC sections"""
    st.sidebar.write(" " * indent + f"- {section['title']}")
    for child in section.get("children", []):
        _toc_section(child, indent=indent + 2)


st.title("🌳 DocTree.AI PDF Hierarchy Extractor")

# ---- File Upload ----
uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])

if "tree" not in st.session_state:
    st.session_state.tree = None
    st.session_state.stats = None
    st.session_state.base_name = None
    st.session_state.error = None
    st.session_state.duration = None
    st.session_state.temp_file_path = None


def section_stats(sections):
    """Count top-level and total nested sections"""
    def count_sections(subsections):
        return sum(1 + count_sections(s.get("children", [])) for s in subsections)
    return len(sections), count_sections(sections)


def render_section(section, level=1):
    """Recursively render section hierarchy using expanders"""
    expanded_default = (level == 1)
    with st.expander(f"{'  ' * (level - 1)}{section['title']}", expanded=expanded_default):
        if section.get("content"):
            for para in section["content"]:
                st.write(para)
        for child in section.get("children", []):
            render_section(child, level=level + 1)


# ---- Process PDF ----
if uploaded_file:
    st.info(f"📄 Uploaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

    # Create temp file only once per upload
    if st.session_state.base_name != os.path.splitext(uploaded_file.name)[0]:
        st.session_state.base_name = os.path.splitext(uploaded_file.name)[0]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            st.session_state.temp_file_path = tmp_file.name

    # ---- Controls (Run + Reset grouped visually) ----
    col_run, col_reset = st.columns(2)
    with col_run:
        run_clicked = st.button("▶️ Run Extraction")
    with col_reset:
        reset_clicked = st.button("🔄 Refresh / Reset")

    # Reset logic first (so doesn't interfere with Run)
    if reset_clicked:
        for k in ["tree", "stats", "base_name", "error", "duration", "temp_file_path"]:
            st.session_state.pop(k, None)
        st.rerun()

    # ---- Run Extraction Button ----
    if run_clicked:
        try:
            t0 = time.time()
            # Show just one spinner for the whole pipeline, to reduce visual noise
            with st.spinner("Running full extraction pipeline..."):
                blocks = parse_pdf(st.session_state.temp_file_path)
                enriched = enrich_blocks_with_features(blocks)
                classified = classify_headings(enriched)
                total_pages = max((b.get("page", 1) for b in classified), default=1)
                num_h1 = sum(1 for b in classified if b.get("classification") == "H1")
                num_h2 = sum(1 for b in classified if b.get("classification") == "H2")
                num_h3 = sum(1 for b in classified if b.get("classification") == "H3")

                metadata = {
                    "source_file": uploaded_file.name,
                    "total_blocks": len(classified),
                    "total_pages": total_pages,
                }
                tree = build_hierarchy(classified, metadata)
                st.session_state.tree = tree
                top_sec, total_sec = section_stats(tree.get("sections", []))
                st.session_state.stats = {
                    "blocks": len(classified),
                    "pages": total_pages,
                    "h1": num_h1,
                    "h2": num_h2,
                    "h3": num_h3,
                    "top_sections": top_sec,
                    "total_sections": total_sec,
                }
                st.session_state.duration = time.time() - t0
                st.session_state.error = None
            st.success("✅ Extraction complete!")
        except Exception as e:
            st.session_state.tree = None
            st.session_state.stats = None
            st.session_state.duration = None
            st.session_state.error = f"Extraction failed: {str(e)}"

    # ---- Show Results ----
    if st.session_state.error:
        st.error(st.session_state.error)

    elif st.session_state.tree:
        # Sidebar TOC
        sidebar_toc(st.session_state.tree)

        stats = st.session_state.stats
        st.subheader("🧮 Document Stats")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Pages", stats["pages"])
        col2.metric("Blocks", stats["blocks"])
        col3.metric("H1 Headings", stats["h1"])
        col4.metric("H2 Headings", stats["h2"])
        col5.metric("H3 Headings", stats["h3"])
        col6.metric("Top Sections", stats["top_sections"])
        st.write(f"Total nested sections: **{stats['total_sections']}**")

        if st.session_state.duration is not None:
            st.write(f"⏱️ Time taken: **{st.session_state.duration:.2f} seconds**")

        st.subheader("🌲 Document Hierarchy")
        for section in st.session_state.tree.get("sections", []):
            render_section(section, level=1)

        st.subheader("📦 JSON Output")
        with st.expander("Show Raw JSON", expanded=False):
            st.json(st.session_state.tree)

        json_bytes = json.dumps(st.session_state.tree, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            label="💾 Download JSON",
            data=json_bytes,
            file_name=f"{st.session_state.base_name}_hierarchy.json",
            mime="application/json",
        )
else:
    st.info("📄 Please upload a PDF document to begin.")
