#!/usr/bin/env python3
"""Check raw Perplexity response for Tech Mahindra Q2 2025"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from config.logging_config import setup_logging
from core.perplexity_client import PerplexityClient
from core.cache_manager import CacheManager

setup_logging(log_level='WARNING')

print("="*70)
print("  RAW PERPLEXITY RESPONSE - Tech Mahindra Q2 2025")
print("="*70)

cache = CacheManager(settings.CACHE_DIR)
client = PerplexityClient(
    api_key=settings.PERPLEXITY_API_KEY,
    rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    cache_manager=cache,
    model=settings.PERPLEXITY_MODEL
)

# Get raw response
result = client.get_company_financials('Tech Mahindra', 'Q2', 2025)

if result:
    print("\n[RAW RESPONSE]")
    print("-"*70)
    raw = result.get('raw_response', '')
    print(raw[:2000] if len(raw) > 2000 else raw)
    print("-"*70)
    print(f"\nResponse length: {len(raw)} chars")
else:
    print("\n[ERROR] No response from Perplexity")
