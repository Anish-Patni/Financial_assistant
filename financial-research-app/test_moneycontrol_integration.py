#!/usr/bin/env python3
"""
Test Moneycontrol Integration
Comprehensive validation of Moneycontrol scraper and extractor
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from config.logging_config import setup_logging, get_logger
from parsers.moneycontrol_scraper import MoneycontrolScraper
from core.moneycontrol_extractor import MoneycontrolFinancialExtractor
from core.enhanced_orchestrator import EnhancedResearchOrchestrator
from core.research_storage import ResearchStorage

# Setup logging
setup_logging(log_level='INFO')
logger = get_logger('test_integration')

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_subsection(title):
    """Print formatted subsection header"""
    print(f"\n{title}")
    print("-" * 80)

def test_scraper_basic():
    """Test basic scraper functionality"""
    print_section("TEST 1: MONEYCONTROL SCRAPER - BASIC FUNCTIONALITY")
    
    scraper = MoneycontrolScraper()
    
    # Test URL generation
    print_subsection("1.1 URL Generation")
    test_companies = ['Wipro', 'TCS', 'Infosys', 'Persistent Systems']
    
    for company in test_companies:
        url = scraper.get_company_url(company)
        print(f"  ✓ {company:20} → {url}")
    
    # Test page fetch
    print_subsection("1.2 Fetch Moneycontrol Page")
    
    company = 'Wipro'
    url = scraper.get_company_url(company)
    print(f"  Fetching: {url}")
    
    html = scraper.fetch_page(url)
    if html:
        print(f"  ✓ Successfully fetched ({len(html):,} bytes)")
        print(f"  ✓ Contains HTML tables: {'<table' in html}")
        print(f"  ✓ Contains financial data: {'crore' in html.lower() or 'revenue' in html.lower()}")
    else:
        print(f"  ✗ Failed to fetch page")
        return False
    
    return True

def test_scraper_parsing():
    """Test scraper parsing functionality"""
    print_section("TEST 2: MONEYCONTROL SCRAPER - DATA PARSING")
    
    scraper = MoneycontrolScraper()
    
    print_subsection("2.1 Fetch and Parse Quarterly Data")
    
    company = 'Wipro'
    url = scraper.get_company_url(company)
    html = scraper.fetch_page(url)
    
    if not html:
        print(f"  ✗ Failed to fetch page")
        return False
    
    quarterly_data = scraper.parse_quarterly_table(html, company)
    
    if quarterly_data:
        print(f"  ✓ Found data for {len(quarterly_data)} quarters")
        
        for quarter in sorted(quarterly_data.keys()):
            indicators = quarterly_data[quarter]
            print(f"\n  {quarter}:")
            print(f"    Total indicators: {len(indicators)}")
            
            # Show sample indicators
            for indicator, data in list(indicators.items())[:5]:
                value = data.get('value', 'N/A')
                confidence = data.get('confidence', 0)
                print(f"      - {indicator:25} = {value:>12} (conf: {confidence:.2f})")
            
            if len(indicators) > 5:
                print(f"      ... and {len(indicators) - 5} more indicators")
    else:
        print(f"  ✗ No quarterly data found")
        return False
    
    return True

def test_extractor():
    """Test MoneycontrolFinancialExtractor"""
    print_section("TEST 3: MONEYCONTROL FINANCIAL EXTRACTOR")
    
    extractor = MoneycontrolFinancialExtractor()
    
    print_subsection("3.1 Extract from Moneycontrol")
    
    company = 'Wipro'
    quarter = 'Q1'
    year = 2024
    
    print(f"  Extracting: {company} {quarter} {year}")
    
    result = extractor.extract_from_moneycontrol(company, quarter, year)
    
    if result:
        print(f"  ✓ Successfully extracted data")
        print(f"    Source: {result.get('source')}")
        print(f"    Confidence: {result.get('context_confidence'):.2f}")
        
        data = result.get('extracted_data', {})
        print(f"    Indicators found: {len(data)}")
        
        if data:
            print(f"\n    Sample Indicators:")
            for indicator, values in list(data.items())[:10]:
                if isinstance(values, dict):
                    value = values.get('value', 'N/A')
                    confidence = values.get('confidence', 0)
                    print(f"      - {indicator:25} = {value:>12} (conf: {confidence:.2f})")
    else:
        print(f"  ✗ Failed to extract data")
        return False
    
    print_subsection("3.2 Extract All Quarters")
    
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    print(f"  Extracting all quarters for {company}...")
    
    all_quarters = extractor.extract_all_quarters(company, quarters, year)
    
    print(f"  ✓ Processed {len(all_quarters)} quarters")
    
    total_indicators = 0
    for quarter, data in all_quarters.items():
        indicators = len(data.get('extracted_data', {}))
        source = data.get('source', 'Unknown')
        confidence = data.get('context_confidence', 0)
        total_indicators += indicators
        print(f"    {quarter}: {indicators:3} indicators from {source:15} (conf: {confidence:.2f})")
    
    print(f"\n  Total indicators extracted: {total_indicators}")
    
    return True

def test_multiple_companies():
    """Test extraction for multiple companies"""
    print_section("TEST 4: MULTIPLE COMPANIES EXTRACTION")
    
    extractor = MoneycontrolFinancialExtractor()
    
    companies = ['Wipro', 'TCS', 'Infosys']
    quarters = ['Q1', 'Q2']
    year = 2024
    
    print_subsection("4.1 Batch Extraction")
    
    print(f"  Companies: {', '.join(companies)}")
    print(f"  Quarters: {', '.join(quarters)}")
    print(f"  Year: {year}")
    print(f"\n  Processing {len(companies)} companies × {len(quarters)} quarters = {len(companies) * len(quarters)} extractions...")
    
    results = extractor.extract_multiple_companies(companies, quarters, year)
    
    print(f"\n  ✓ Extraction completed for {len(results)} companies")
    
    print_subsection("4.2 Results Summary")
    
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
    
    return True

def test_orchestrator():
    """Test EnhancedResearchOrchestrator"""
    print_section("TEST 5: ENHANCED RESEARCH ORCHESTRATOR")
    
    # Initialize storage
    storage = ResearchStorage(settings.RESEARCH_RESULTS_DIR)
    
    # Initialize orchestrator
    orchestrator = EnhancedResearchOrchestrator(
        storage=storage,
        use_moneycontrol=True
    )
    
    print_subsection("5.1 Single Company Research")
    
    company = 'Wipro'
    quarter = 'Q1'
    year = 2024
    
    print(f"  Researching: {company} {quarter} {year}")
    
    result = orchestrator.research_company_quarter(company, quarter, year)
    
    print(f"  ✓ Research completed")
    print(f"    Status: {result.get('status')}")
    print(f"    Source: {result.get('source')}")
    print(f"    Confidence: {result.get('context_confidence'):.2f}")
    print(f"    Indicators: {len(result.get('extracted_data', {}))}")
    
    print_subsection("5.2 All Quarters for Single Company")
    
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    print(f"  Researching all quarters for {company}...")
    
    all_quarters = orchestrator.research_company_all_quarters(company, quarters, year)
    
    print(f"  ✓ Processed {len(all_quarters)} quarters")
    
    for quarter, data in all_quarters.items():
        indicators = len(data.get('extracted_data', {}))
        source = data.get('source', 'Unknown')
        print(f"    {quarter}: {indicators} indicators from {source}")
    
    return True

def test_data_quality():
    """Test data quality and completeness"""
    print_section("TEST 6: DATA QUALITY ASSESSMENT")
    
    extractor = MoneycontrolFinancialExtractor()
    
    print_subsection("6.1 Key Indicators Coverage")
    
    company = 'Wipro'
    quarter = 'Q1'
    year = 2024
    
    result = extractor.extract_from_moneycontrol(company, quarter, year)
    
    if result:
        data = result.get('extracted_data', {})
        
        key_indicators = [
            'total_income', 'ebitda', 'ebit', 'pbt', 'pat',
            'employee_cost', 'depreciation', 'interest'
        ]
        
        print(f"\n  Key Indicators for {company} {quarter} {year}:")
        
        found_count = 0
        for indicator in key_indicators:
            if indicator in data:
                value = data[indicator].get('value', 'N/A')
                confidence = data[indicator].get('confidence', 0)
                print(f"    ✓ {indicator:20} = {value:>12} (conf: {confidence:.2f})")
                found_count += 1
            else:
                print(f"    ✗ {indicator:20} = NOT FOUND")
        
        coverage = (found_count / len(key_indicators)) * 100
        print(f"\n  Coverage: {found_count}/{len(key_indicators)} ({coverage:.1f}%)")
    
    return True

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "MONEYCONTROL INTEGRATION TEST SUITE".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        ("Scraper Basic", test_scraper_basic),
        ("Scraper Parsing", test_scraper_parsing),
        ("Extractor", test_extractor),
        ("Multiple Companies", test_multiple_companies),
        ("Orchestrator", test_orchestrator),
        ("Data Quality", test_data_quality),
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
    print_section("TEST SUMMARY")
    
    print("\n  Test Results:")
    for test_name, status in results.items():
        symbol = "✓" if status == "PASS" else "✗"
        print(f"    {symbol} {test_name:30} {status}")
    
    passed = sum(1 for s in results.values() if s == "PASS")
    total = len(results)
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    print_section("COMPLETION")
    
    print(f"\n  Timestamp: {datetime.now().isoformat()}")
    print(f"  Status: {'ALL TESTS PASSED ✓' if passed == total else 'SOME TESTS FAILED ✗'}")
    print(f"\n  Check logs for detailed information")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
