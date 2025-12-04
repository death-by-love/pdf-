# Architecture

This document outlines the high-level architecture for `pdf-topic-scanner`.

TODO: expand with diagrams, data flow, module responsibilities, and interfaces.

- `src/core`: PDF ingestion and raw text extraction
- `src/features`: feature engineering and text preprocessing
- `src/hierarchy`: heading detection and hierarchy reconstruction
- `src/ui`: interactive UI (Streamlit) to run the pipeline
- `outputs/json`: serialized outputs (hierarchies, topics)
- `utils`: helpers for logging and validation
