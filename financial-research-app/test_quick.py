#!/usr/bin/env python3
"""Quick test for hybrid data source"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from config.logging_config import setup_logging
from core.perplexity_client import PerplexityClient
from core.cache_manager import CacheManager
from core.hybrid_data_source import HybridDataSource

setup_logging(log_level='INFO')

print("="*60)
print("  QUICK HYBRID SOURCE TEST")
print("="*60)

# Initialize
cache = CacheManager(settings.CACHE_DIR)
client = PerplexityClient(
    api_key=settings.PERPLEXITY_API_KEY,
    rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    cache_manager=cache,
    model=settings.PERPLEXITY_MODEL
)

hybrid = HybridDataSource(client)

# Test Tech Mahindra Q1 and Q2 2025
for quarter in ['Q1', 'Q2']:
    print(f"\n[TEST] Tech Mahindra {quarter} 2025")
    result = hybrid.extract_financial_data('Tech Mahindra', quarter, 2025)
    
    print(f"  Source: {result.get('source')}")
    print(f"  Confidence: {result.get('context_confidence', 0)}")
    print(f"  Indicators: {len(result.get('extracted_data', {}))}")
    
    if result.get('extracted_data'):
        print("  Extracted Data:")
        for k, v in list(result.get('extracted_data', {}).items())[:5]:
            val = v.get('value', 'N/A') if isinstance(v, dict) else v
            print(f"    {k}: {val}")
    else:
        print("  [ERROR] No data extracted!")
        print(f"  Error: {result.get('error', 'Unknown')}")

print("\n" + "="*60)
print("  TEST COMPLETE")
print("="*60)
