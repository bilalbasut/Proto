import os
import json

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, 'scraped_data.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'rewritten_blogs.json')

# API settings
MAX_TOKENS = 2000  # Maximum number of tokens for each API request
RATE_LIMIT_DELAY = 10  # Delay between API calls in seconds

# Rewriter settings
CHECK_INTERVAL = 600  # Time to wait before checking for new content (in seconds)

def check_file_exists(file_path):
    """Check if a file exists and is readable."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Permission denied: {file_path}")

def validate_json_file(file_path):
    """Validate that a file contains valid JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in file: {file_path}")

def ensure_directory_exists(file_path):
    """Ensure that the directory for a file exists, creating it if necessary."""
    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)
