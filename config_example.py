"""
Example Configuration File
Copy this to config.local.py and customize for your setup
"""

import os

# NCBI Configuration
NCBI_EMAIL = "your-email@example.com"  # REQUIRED: Your email for NCBI
NCBI_API_KEY = "your-ncbi-api-key"     # OPTIONAL: Get from https://ncbiinsights.ncbi.nlm.nih.gov/

# OpenAI Configuration  
OPENAI_API_KEY = "your-openai-api-key"  # OPTIONAL: For MCQ generation

# Processing Configuration
DEFAULT_MAX_PAPERS = 20          # Default number of papers to retrieve
DEFAULT_DELAY = 1.0              # Delay between requests (seconds)
ENABLE_MCQ_BY_DEFAULT = True     # Enable MCQ generation by default

# Output Configuration
DEFAULT_OUTPUT_DIR = "outputs"   # Default output directory
INCLUDE_DEBUG_INFO = False       # Include debug information in logs

# MCQ Generation Settings
MCQ_MODEL = "gpt-4o-mini"        # OpenAI model for MCQ generation
MCQ_TIMEOUT = 45.0               # Timeout for MCQ generation (seconds)
MIN_CAPTION_LENGTH = 40          # Minimum caption length for MCQ generation

# Advanced Settings
MAX_RETRIES = 3                  # Maximum retries for failed requests
BATCH_SIZE = 100                 # Batch size for processing
ENABLE_CACHING = True            # Enable response caching

# Example usage in code:
# from config.local import NCBI_EMAIL, OPENAI_API_KEY
# config = Config(email=NCBI_EMAIL, openai_api_key=OPENAI_API_KEY)

# Environment variable fallbacks
NCBI_EMAIL = os.getenv('NCBI_EMAIL', NCBI_EMAIL)
NCBI_API_KEY = os.getenv('NCBI_API_KEY', NCBI_API_KEY) 
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', OPENAI_API_KEY)