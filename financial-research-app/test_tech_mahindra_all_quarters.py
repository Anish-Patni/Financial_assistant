#!/usr/bin/env python3
"""Test Tech Mahindra for all quarters"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from config.logging_config import setup_logging
from core.perplexity_client import PerplexityClient
from core.cache_manager import CacheManager
from core.hybrid_data_source import HybridDataSource

setup_logging(log_level='WARNING')

print("="*70)
print("  TECH MAHINDRA - ALL QUARTERS TEST")
print("="*70)

cache = CacheManager(settings.CACHE_DIR)
client = PerplexityClient(
    api_key=settings.PERPLEXITY_API_KEY,
    rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    cache_manager=cache,
    model=settings.PERPLEXITY_MODEL
)

hybrid = HybridDataSource(client)

# Test all quarters for 2024 and 2025
test_cases = [
    ('Q1', 2024), ('Q2', 2024), ('Q3', 2024), ('Q4', 2024),
    ('Q1', 2025), ('Q2', 2025)
]

print(f"\nTesting Tech Mahindra across {len(test_cases)} quarters...\n")

results = []
for quarter, year in test_cases:
    print(f"[TEST] Tech Mahindra {quarter} {year}...", end=" ", flush=True)
    try:
        result = hybrid.extract_financial_data('Tech Mahindra', quarter, year)
        indicators = len(result.get('extracted_data', {}))
        source = result.get('source', 'None')
        data = result.get('extracted_data', {})
        
        if indicators > 0:
            print(f"✓ {indicators} indicators")
            # Show key metrics
            keys = list(data.keys())[:3]
            for k in keys:
                v = data[k]
                val = v.get('value', v) if isinstance(v, dict) else v
                print(f"    - {k}: {val}")
            results.append((quarter, year, 'OK', indicators))
        else:
            print(f"✗ No data")
            results.append((quarter, year, 'FAIL', 0))
    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
        results.append((quarter, year, 'ERROR', 0))

print("\n" + "="*70)
print("  SUMMARY - Tech Mahindra")
print("="*70)
print(f"\n{'Quarter':<10} {'Year':<6} {'Status':<8} {'Indicators'}")
print("-"*40)
for quarter, year, status, indicators in results:
    icon = "✓" if status == "OK" else "✗"
    print(f"{quarter:<10} {year:<6} {icon} {status:<6} {indicators}")

success = sum(1 for r in results if r[2] == 'OK')
print(f"\nSuccess: {success}/{len(results)} quarters")
