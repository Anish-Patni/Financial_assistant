#!/usr/bin/env python3
"""Test all companies for Q2 2025"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from config.logging_config import setup_logging
from core.perplexity_client import PerplexityClient
from core.cache_manager import CacheManager
from core.hybrid_data_source import HybridDataSource
from config.company_config import company_config

setup_logging(log_level='WARNING')  # Reduce noise

print("="*70)
print("  TESTING ALL COMPANIES - Q2 2025")
print("="*70)

# Initialize
cache = CacheManager(settings.CACHE_DIR)
client = PerplexityClient(
    api_key=settings.PERPLEXITY_API_KEY,
    rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    cache_manager=cache,
    model=settings.PERPLEXITY_MODEL
)

hybrid = HybridDataSource(client)

# Get all companies
companies = company_config.get_all_companies()
print(f"\nTesting {len(companies)} companies...\n")

results = []
for company in companies:  # Test all companies
    print(f"[TEST] {company} Q2 2025...", end=" ", flush=True)
    try:
        result = hybrid.extract_financial_data(company, 'Q2', 2025)
        indicators = len(result.get('extracted_data', {}))
        source = result.get('source', 'None')
        
        if indicators > 0:
            print(f"✓ {indicators} indicators from {source}")
            results.append((company, 'OK', indicators, source))
        else:
            print(f"✗ No data - {result.get('error', 'Unknown')[:30]}")
            results.append((company, 'FAIL', 0, source))
    except Exception as e:
        print(f"✗ Error: {str(e)[:40]}")
        results.append((company, 'ERROR', 0, str(e)[:30]))

print("\n" + "="*70)
print("  SUMMARY")
print("="*70)
print(f"\n{'Company':<20} {'Status':<8} {'Indicators':<12} {'Source'}")
print("-"*70)
for company, status, indicators, source in results:
    status_icon = "✓" if status == "OK" else "✗"
    print(f"{company:<20} {status_icon} {status:<6} {indicators:<12} {source}")

success = sum(1 for r in results if r[1] == 'OK')
print(f"\nSuccess: {success}/{len(results)} companies")
