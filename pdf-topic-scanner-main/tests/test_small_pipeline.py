"""Small pipeline test for pdf-topic-scanner.

This test should remain lightweight and use stubs/mocks. It ensures the
pipeline pieces integrate at a basic level.
"""
import os
import json

from src.core.pdf_parser import PDFParser
from src.features.feature_engineer import FeatureEngineer
from src.hierarchy.tree_builder import TreeBuilder


def test_pipeline_smoke():
    """Basic smoke test that exercises stubs."""
    # create fake text
    text = """
    Introduction
    This is a short document.

    Section One
    Content here.
    """

    # Parser stub isn't implemented; bypass by using text directly
    fe = FeatureEngineer()
    features = fe.extract_features(text)
    assert "word_count" in features

    tb = TreeBuilder()
    headings = [{"title": "Introduction", "level": 1}, {"title": "Section One", "level": 2}]
    root = tb.build_from_headings(headings)
    d = root.to_dict()
    assert d["children"]
