#!/usr/bin/env python3
"""Test Tech Mahindra Data Extraction"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from config.logging_config import setup_logging, get_logger
from config.company_config import company_config
from parsers.moneycontrol_scraper_v2 import MoneycontrolScraperV2
from core.perplexity_client import PerplexityClient
from core.cache_manager import CacheManager
from core.hybrid_data_source import HybridDataSource

setup_logging(log_level='INFO')

def main():
    print("\n" + "="*60)
    print("  TECH MAHINDRA DATA EXTRACTION TEST")
    print("="*60)
    
    # Test 1: Company Config
    print("\n[TEST 1] Company Configuration")
    tm = company_config.get_company('Tech Mahindra')
    if tm:
        print(f"  OK: {tm['slug']}/{tm['code']}")
        print(f"  URL: {company_config.get_moneycontrol_url('Tech Mahindra', 'quarterly')}")
    else:
        print("  FAIL: Tech Mahindra not in config")
        return
    
    # Test 2: Hybrid Source
    print("\n[TEST 2] Hybrid Data Source")
    cache = CacheManager(settings.CACHE_DIR)
    client = PerplexityClient(
        api_key=settings.PERPLEXITY_API_KEY,
        rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        cache_manager=cache,
        model=settings.PERPLEXITY_MODEL
    )
    
    hybrid = HybridDataSource(client)
    
    for quarter in ['Q1', 'Q2']:
        print(f"\n  Extracting Tech Mahindra {quarter} 2024...")
        result = hybrid.extract_financial_data('Tech Mahindra', quarter, 2024)
        
        source = result.get('source', 'None')
        data = result.get('extracted_data', {})
        print(f"    Source: {source}")
        print(f"    Indicators: {len(data)}")
        
        if data:
            for k, v in list(data.items())[:5]:
                val = v.get('value', 'N/A') if isinstance(v, dict) else v
                print(f"      {k}: {val}")
    
    # Test 3: Available Companies
    print("\n[TEST 3] Available Companies")
    companies = hybrid.get_available_companies()
    print(f"  Total: {len(companies)}")
    for c in companies[:5]:
        print(f"    - {c}")
    print(f"    ... and {len(companies)-5} more")
    
    print("\n" + "="*60)
    print("  TEST COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
