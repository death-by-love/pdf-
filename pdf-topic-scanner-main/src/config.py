"""Global configuration and constants for pdf-topic-scanner."""

# Heading score thresholds for classification
HEADING_SCORE_THRESHOLDS = {
    "H1": 0.8,
    "H2": 0.6,
    "H3": 0.4,
    "BODY": 0.0
}

# PDF parsing defaults
Y_TOLERANCE = 5  # units for grouping words into lines
PAGE_WIDTH = 612  # standard US Letter width in points
