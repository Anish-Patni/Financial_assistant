#!/usr/bin/env python3
"""
Test Hybrid Data Source
Validates Perplexity primary + Moneycontrol fallback extraction
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from config.logging_config import setup_logging, get_logger
from core.perplexity_client import PerplexityClient
from core.cache_manager import CacheManager
from core.hybrid_data_source import HybridDataSource

# Setup logging
setup_logging(log_level='INFO')
logger = get_logger('test_hybrid')

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_subheader(title):
    """Print formatted subheader"""
    print(f"\n{title}")
    print("-" * 80)

def test_single_company():
    """Test extraction for single company"""
    print_header("TEST 1: SINGLE COMPANY EXTRACTION")
    
    # Initialize components
    cache = CacheManager(settings.CACHE_DIR)
    client = PerplexityClient(
        api_key=settings.PERPLEXITY_API_KEY,
        rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        cache_manager=cache,
        use_finance_domain=settings.PERPLEXITY_USE_FINANCE_DOMAIN,
        model=settings.PERPLEXITY_MODEL
    )
    
    hybrid_source = HybridDataSource(client)
    
    print_subheader("1.1 Extract Wipro Q1 2024")
    
    company = 'Wipro'
    quarter = 'Q1'
    year = 2024
    
    print(f"  Extracting: {company} {quarter} {year}")
    print(f"  Primary Source: Perplexity AI")
    print(f"  Fallback Source: Moneycontrol")
    
    result = hybrid_source.extract_financial_data(company, quarter, year)
    
    print(f"\n  ✓ Extraction completed")
    print(f"    Source Used: {result.get('source')}")
    print(f"    Confidence: {result.get('context_confidence'):.2f}")
    
    extracted = result.get('extracted_data', {})
    print(f"    Indicators Found: {len(extracted)}")
    
    if extracted:
        print(f"\n    Key Indicators:")
        key_indicators = ['total_income', 'ebitda', 'ebit', 'pbt', 'pat']
        for indicator in key_indicators:
            if indicator in extracted:
                data = extracted[indicator]
                if isinstance(data, dict):
                    value = data.get('value', 'N/A')
                    confidence = data.get('confidence', 0)
                    print(f"      ✓ {indicator:20} = ₹{value:>10.2f} Cr (conf: {confidence:.2f})")
                else:
                    print(f"      ✓ {indicator:20} = {data}")
            else:
                print(f"      ✗ {indicator:20} = NOT FOUND")
    
    # Print full summary
    print(f"\n  Full Summary:")
    summary = hybrid_source.get_data_summary(result)
    for line in summary.split('\n'):
        print(f"    {line}")
    
    return len(extracted) > 0

def test_multiple_quarters():
    """Test extraction for multiple quarters"""
    print_header("TEST 2: MULTIPLE QUARTERS EXTRACTION")
    
    # Initialize components
    cache = CacheManager(settings.CACHE_DIR)
    client = PerplexityClient(
        api_key=settings.PERPLEXITY_API_KEY,
        rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        cache_manager=cache,
        use_finance_domain=settings.PERPLEXITY_USE_FINANCE_DOMAIN,
        model=settings.PERPLEXITY_MODEL
    )
    
    hybrid_source = HybridDataSource(client)
    
    print_subheader("2.1 Extract All Quarters for Wipro")
    
    company = 'Wipro'
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    year = 2024
    
    print(f"  Company: {company}")
    print(f"  Quarters: {', '.join(quarters)}")
    print(f"  Year: {year}")
    print(f"\n  Processing {len(quarters)} quarters...")
    
    total_indicators = 0
    for quarter in quarters:
        result = hybrid_source.extract_financial_data(company, quarter, year)
        indicators = len(result.get('extracted_data', {}))
        source = result.get('source', 'Unknown')
        confidence = result.get('context_confidence', 0)
        total_indicators += indicators
        
        status = "✓" if indicators > 0 else "✗"
        print(f"    {status} {quarter}: {indicators:3} indicators from {source:15} (conf: {confidence:.2f})")
    
    print(f"\n  Total indicators extracted: {total_indicators}")
    
    return total_indicators > 0

def test_multiple_companies():
    """Test extraction for multiple companies"""
    print_header("TEST 3: MULTIPLE COMPANIES EXTRACTION")
    
    # Initialize components
    cache = CacheManager(settings.CACHE_DIR)
    client = PerplexityClient(
        api_key=settings.PERPLEXITY_API_KEY,
        rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        cache_manager=cache,
        use_finance_domain=settings.PERPLEXITY_USE_FINANCE_DOMAIN,
        model=settings.PERPLEXITY_MODEL
    )
    
    hybrid_source = HybridDataSource(client)
    
    print_subheader("3.1 Batch Extraction - Multiple Companies")
    
    companies = ['Wipro', 'TCS', 'Infosys']
    quarters = ['Q1', 'Q2']
    year = 2024
    
    print(f"  Companies: {', '.join(companies)}")
    print(f"  Quarters: {', '.join(quarters)}")
    print(f"  Year: {year}")
    print(f"\n  Processing {len(companies)} companies × {len(quarters)} quarters = {len(companies) * len(quarters)} extractions...")
    
    results = hybrid_source.extract_multiple_companies(companies, quarters, year)
    
    print_subheader("3.2 Results Summary")
    
    total_indicators = 0
    for company in sorted(results.keys()):
        company_data = results[company]
        print(f"\n  {company}:")
        
        for quarter in sorted(company_data.keys()):
            data = company_data[quarter]
            indicators = len(data.get('extracted_data', {}))
            source = data.get('source', 'Unknown')
            confidence = data.get('context_confidence', 0)
            total_indicators += indicators
            
            status = "✓" if indicators > 0 else "✗"
            print(f"    {status} {quarter}: {indicators:3} indicators from {source:15} (conf: {confidence:.2f})")
    
    print(f"\n  Total indicators extracted: {total_indicators}")
    
    return total_indicators > 0

def test_data_accuracy():
    """Test data accuracy and consistency"""
    print_header("TEST 4: DATA ACCURACY & CONSISTENCY")
    
    # Initialize components
    cache = CacheManager(settings.CACHE_DIR)
    client = PerplexityClient(
        api_key=settings.PERPLEXITY_API_KEY,
        rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        cache_manager=cache,
        use_finance_domain=settings.PERPLEXITY_USE_FINANCE_DOMAIN,
        model=settings.PERPLEXITY_MODEL
    )
    
    hybrid_source = HybridDataSource(client)
    
    print_subheader("4.1 Data Validation")
    
    company = 'Wipro'
    quarter = 'Q1'
    year = 2024
    
    result = hybrid_source.extract_financial_data(company, quarter, year)
    
    extracted = result.get('extracted_data', {})
    
    print(f"  Company: {company}")
    print(f"  Period: {quarter} {year}")
    print(f"  Source: {result.get('source')}")
    print(f"  Total Indicators: {len(extracted)}")
    
    # Validate key metrics
    print(f"\n  Key Metrics Validation:")
    
    key_metrics = {
        'total_income': 'Total Income (Revenue)',
        'ebitda': 'EBITDA',
        'ebit': 'EBIT',
        'pbt': 'Profit Before Tax',
        'pat': 'Profit After Tax'
    }
    
    found_count = 0
    for metric_key, metric_name in key_metrics.items():
        if metric_key in extracted:
            data = extracted[metric_key]
            if isinstance(data, dict):
                value = data.get('value', 0)
                confidence = data.get('confidence', 0)
                
                # Validate value is positive
                if value > 0:
                    print(f"    ✓ {metric_name:25} = ₹{value:>10.2f} Cr (conf: {confidence:.2f})")
                    found_count += 1
                else:
                    print(f"    ⚠ {metric_name:25} = {value} (invalid value)")
            else:
                print(f"    ⚠ {metric_name:25} = Invalid format")
        else:
            print(f"    ✗ {metric_name:25} = NOT FOUND")
    
    coverage = (found_count / len(key_metrics)) * 100
    print(f"\n  Coverage: {found_count}/{len(key_metrics)} ({coverage:.1f}%)")
    
    return found_count >= 3  # At least 3 key metrics

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "HYBRID DATA SOURCE TEST SUITE".center(78) + "║")
    print("║" + "(Perplexity Primary + Moneycontrol Fallback)".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        ("Single Company", test_single_company),
        ("Multiple Quarters", test_multiple_quarters),
        ("Multiple Companies", test_multiple_companies),
        ("Data Accuracy", test_data_accuracy),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = "PASS" if success else "FAIL"
        except Exception as e:
            logger.error(f"Test '{test_name}' failed: {e}", exc_info=True)
            results[test_name] = "ERROR"
            print(f"\n  ✗ Test failed with error: {e}")
    
    # Print summary
    print_header("TEST SUMMARY")
    
    print("\n  Test Results:")
    for test_name, status in results.items():
        symbol = "✓" if status == "PASS" else "✗"
        print(f"    {symbol} {test_name:30} {status}")
    
    passed = sum(1 for s in results.values() if s == "PASS")
    total = len(results)
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    print_header("COMPLETION")
    
    print(f"\n  Timestamp: {datetime.now().isoformat()}")
    print(f"  Status: {'ALL TESTS PASSED ✓' if passed == total else 'SOME TESTS FAILED ✗'}")
    print(f"\n  Data Source Priority:")
    print(f"    1. Perplexity AI (Primary)")
    print(f"    2. Moneycontrol (Fallback)")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
