#!/usr/bin/env python3
"""
Test Moneycontrol Scraper
Validates data extraction from Moneycontrol portal
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.logging_config import setup_logging, get_logger
from parsers.moneycontrol_scraper import MoneycontrolScraper
from core.moneycontrol_extractor import MoneycontrolFinancialExtractor

# Setup logging
setup_logging(log_level='INFO')
logger = get_logger('test_moneycontrol')

def test_scraper():
    """Test basic scraper functionality"""
    print("\n" + "="*70)
    print("MONEYCONTROL SCRAPER TEST")
    print("="*70)
    
    scraper = MoneycontrolScraper()
    
    # Test 1: URL generation
    print("\n[TEST 1] URL Generation")
    print("-" * 70)
    
    test_companies = ['Wipro', 'TCS', 'Infosys']
    for company in test_companies:
        url = scraper.get_company_url(company)
        print(f"✓ {company}: {url}")
    
    # Test 2: Fetch page
    print("\n[TEST 2] Fetch Moneycontrol Page")
    print("-" * 70)
    
    company = 'Wipro'
    url = scraper.get_company_url(company)
    print(f"Fetching: {url}")
    
    html = scraper.fetch_page(url)
    if html:
        print(f"✓ Successfully fetched page ({len(html)} bytes)")
        print(f"✓ Page contains tables: {'<table' in html}")
    else:
        print("✗ Failed to fetch page")
        return
    
    # Test 3: Parse quarterly data
    print("\n[TEST 3] Parse Quarterly Data")
    print("-" * 70)
    
    quarterly_data = scraper.parse_quarterly_table(html, company)
    
    if quarterly_data:
        print(f"✓ Found data for {len(quarterly_data)} quarters:")
        for quarter, indicators in quarterly_data.items():
            print(f"\n  {quarter}:")
            for indicator, data in list(indicators.items())[:5]:  # Show first 5
                value = data.get('value', 'N/A')
                confidence = data.get('confidence', 0)
                print(f"    - {indicator}: {value} (conf: {confidence:.2f})")
            
            if len(indicators) > 5:
                print(f"    ... and {len(indicators) - 5} more indicators")
    else:
        print("✗ No quarterly data found")
    
    # Test 4: Extract specific quarter
    print("\n[TEST 4] Extract Specific Quarter")
    print("-" * 70)
    
    quarter_data = scraper.extract_specific_quarter('Wipro', 'Q1')
    if quarter_data:
        print(f"✓ Successfully extracted Q1 data ({len(quarter_data)} indicators)")
        for indicator, data in list(quarter_data.items())[:10]:
            print(f"  {indicator}: {data.get('value', 'N/A')}")
    else:
        print("✗ Failed to extract Q1 data")

def test_extractor():
    """Test MoneycontrolFinancialExtractor"""
    print("\n" + "="*70)
    print("MONEYCONTROL FINANCIAL EXTRACTOR TEST")
    print("="*70)
    
    extractor = MoneycontrolFinancialExtractor()
    
    # Test 1: Extract from Moneycontrol
    print("\n[TEST 1] Extract from Moneycontrol")
    print("-" * 70)
    
    company = 'Wipro'
    quarter = 'Q1'
    year = 2024
    
    print(f"Extracting: {company} {quarter} {year}")
    result = extractor.extract_from_moneycontrol(company, quarter, year)
    
    if result:
        print(f"✓ Successfully extracted data")
        print(f"  Source: {result.get('source')}")
        print(f"  Confidence: {result.get('context_confidence'):.2f}")
        print(f"  Indicators: {len(result.get('extracted_data', {}))}")
        
        # Print sample data
        data = result.get('extracted_data', {})
        print("\n  Sample Indicators:")
        for indicator, values in list(data.items())[:5]:
            if isinstance(values, dict):
                print(f"    - {indicator}: {values.get('value', 'N/A')}")
    else:
        print("✗ Failed to extract data")
    
    # Test 2: Extract with fallback
    print("\n[TEST 2] Extract with Fallback")
    print("-" * 70)
    
    result = extractor.extract_with_fallback(company, quarter, year)
    
    print(f"✓ Extraction completed")
    print(f"  Source: {result.get('source')}")
    print(f"  Confidence: {result.get('context_confidence'):.2f}")
    print(f"  Indicators found: {len(result.get('extracted_data', {}))}")
    
    # Print summary
    summary = extractor.get_extraction_summary(result)
    print("\n" + summary)
    
    # Test 3: Extract all quarters
    print("\n[TEST 3] Extract All Quarters")
    print("-" * 70)
    
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    print(f"Extracting all quarters for {company}...")
    
    all_quarters = extractor.extract_all_quarters(company, quarters, year)
    
    print(f"✓ Processed {len(all_quarters)} quarters")
    for quarter, data in all_quarters.items():
        indicators = len(data.get('extracted_data', {}))
        source = data.get('source', 'Unknown')
        print(f"  {quarter}: {indicators} indicators from {source}")

def test_multiple_companies():
    """Test extraction for multiple companies"""
    print("\n" + "="*70)
    print("MULTIPLE COMPANIES TEST")
    print("="*70)
    
    extractor = MoneycontrolFinancialExtractor()
    
    companies = ['Wipro', 'TCS', 'Infosys']
    quarters = ['Q1', 'Q2']
    year = 2024
    
    print(f"\nExtracting data for {len(companies)} companies, {len(quarters)} quarters")
    print("-" * 70)
    
    results = extractor.extract_multiple_companies(companies, quarters, year)
    
    print(f"\n✓ Extraction completed for {len(results)} companies")
    
    for company, company_data in results.items():
        print(f"\n{company}:")
        for quarter, data in company_data.items():
            indicators = len(data.get('extracted_data', {}))
            source = data.get('source', 'Unknown')
            confidence = data.get('context_confidence', 0)
            print(f"  {quarter}: {indicators} indicators (conf: {confidence:.2f}) from {source}")

def main():
    """Run all tests"""
    try:
        test_scraper()
        test_extractor()
        test_multiple_companies()
        
        print("\n" + "="*70)
        print("ALL TESTS COMPLETED")
        print("="*70)
        print(f"\nTimestamp: {datetime.now().isoformat()}")
        print("Check logs for detailed information")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
