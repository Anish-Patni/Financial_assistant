# Configuration Management
# Centralized settings for the Financial Research Application

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
BASE_DIR = Path(__file__).parent.parent

# API Configuration
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '')
PERPLEXITY_API_URL = 'https://api.perplexity.ai/chat/completions'
PERPLEXITY_MODEL = os.getenv('PERPLEXITY_MODEL', 'sonar')

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv('RATE_LIMIT_RPM', '20'))
RATE_LIMIT_TOKENS_PER_MINUTE = int(os.getenv('RATE_LIMIT_TPM', '10000'))

# Cache Configuration
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '86400'))  # 24 hours default
CACHE_DIR = BASE_DIR / 'data' / 'cache'

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR = BASE_DIR / 'logs'
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# Data Paths
DATA_DIR = BASE_DIR / 'data'
TEMPLATES_DIR = DATA_DIR / 'templates'
RESEARCH_RESULTS_DIR = DATA_DIR / 'research_results'

# Phase 2: Research Configuration
MAX_RESEARCH_WORKERS = int(os.getenv('MAX_RESEARCH_WORKERS', '3'))
RESEARCH_QUARTERS = os.getenv('RESEARCH_QUARTERS', 'Q1,Q2,Q3,Q4').split(',')
RESEARCH_YEAR = int(os.getenv('RESEARCH_YEAR', '2024'))
MIN_CONFIDENCE_THRESHOLD = float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '0.7'))
AUTO_RETRY_FAILED = os.getenv('AUTO_RETRY_FAILED', 'true').lower() == 'true'
PERPLEXITY_USE_FINANCE_DOMAIN = os.getenv('PERPLEXITY_USE_FINANCE_DOMAIN', 'false').lower() == 'true'

# Financial Data Configuration
FINANCIAL_INDICATORS = [
    'Total Income From Operations',
    'Purchase of Traded Goods',
    'Increase/Decrease in Stocks',
    'Contribution',
    'Employee Cost',
    'Other Expenses',
    'Op. EBITDA',
    'Depreciation',
    'Op. EBIT',
    'Interest',
    'Op. PBT',
    'Other Income',
    'PBT',
    'Tax',
    'PAT',
    'Non-Controlling Interest',
    'PAT (After NCI)',
    'Op. EBITDA %',
    'Op. EBIT %',
    'Op. PBT %',
    'PBT %',
]

# Validation Ranges (in Crores)
VALIDATION_RANGES = {
    'revenue_min': 0,
    'revenue_max': 100000,
    'margin_min': -50,
    'margin_max': 100,
    'qoq_change_threshold': 50,  # percentage
}

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    RESEARCH_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

ensure_directories()
