"""
Global configuration and constants for DocTree.AI
"""

# Heading detection thresholds (can be tuned)
HEADING_SCORE_THRESHOLDS = {
    "H1": 0.8,
    "H2": 0.6,
    "H3": 0.4,
    "BODY": 0.0
}

# Maximum word count to consider a line as heading
MAX_HEADING_WORDS = 10

# Default output directory for JSON
OUTPUT_DIR = "outputs/json"

# Logging level
LOG_LEVEL = "INFO"