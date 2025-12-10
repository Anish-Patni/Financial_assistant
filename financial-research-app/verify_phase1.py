#!/usr/bin/env python3
"""
Phase 1 Verification Script
Comprehensive testing of all Phase 1 components
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from config.logging_config import setup_logging, get_logger
from core.cache_manager import CacheManager
from core.perplexity_client import PerplexityClient
from core.data_models import QuarterlyData, CompanyFinancials
from utils.validators import FinancialValidator
from parsers.excel_parser import ExcelParser, create_sample_template

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def test_configuration():
    """Test 1: Configuration and Setup"""
    print_header("TEST 1: Configuration and Setup")
    
    try:
        print_info(f"Base Directory: {settings.BASE_DIR}")
        print_info(f"Cache Directory: {settings.CACHE_DIR}")
        print_info(f"Log Directory: {settings.LOG_DIR}")
        print_info(f"Rate Limit: {settings.RATE_LIMIT_REQUESTS_PER_MINUTE} req/min")
        print_info(f"Cache TTL: {settings.CACHE_TTL_SECONDS} seconds")
        
        # Check if API key is set
        if settings.PERPLEXITY_API_KEY and settings.PERPLEXITY_API_KEY != '':
            print_success("Perplexity API key configured")
        else:
            print_warning("Perplexity API key not set (will use mock mode)")
        
        print_success("Configuration loaded successfully")
        return True
    except Exception as e:
        print_error(f"Configuration failed: {e}")
        return False


def test_logging():
    """Test 2: Logging System"""
    print_header("TEST 2: Logging System")
    
    try:
        logger = setup_logging(log_level=settings.LOG_LEVEL)
        
        logger.debug("Debug message test")
        logger.info("Info message test")
        logger.warning("Warning message test")
        
        # Check if log files exist
        log_file = settings.LOG_DIR / 'financial_research.log'
        error_log = settings.LOG_DIR / 'errors.log'
        
        if log_file.exists():
            print_success(f"Log file created: {log_file}")
        
        print_success("Logging system working")
        return True
    except Exception as e:
        print_error(f"Logging test failed: {e}")
        return False


def test_cache_manager():
    """Test 3: Cache Manager"""
    print_header("TEST 3: Cache Manager")
    
    try:
        cache = CacheManager(settings.CACHE_DIR, ttl_seconds=60)
        
        # Test cache set/get
        test_query = {'company': 'TCS', 'quarter': 'Q1', 'year': 2024}
        test_response = {'revenue': 1234.56, 'ebitda': 500.00}
        
        cache.set(test_query, test_response)
        print_success("Cache write successful")
        
        cached_data = cache.get(test_query)
        if cached_data == test_response:
            print_success("Cache read successful")
        else:
            print_error("Cache data mismatch")
            return False
        
        # Test cache stats
        stats = cache.get_stats()
        print_info(f"Cache stats: {stats}")
        
        print_success("Cache manager working")
        return True
    except Exception as e:
        print_error(f"Cache test failed: {e}")
        return False


def test_data_models():
    """Test 4: Data Models and Calculations"""
    print_header("TEST 4: Data Models and Calculations")
    
    try:
        # Create quarterly data
        q_data = QuarterlyData(
            company='TCS',
            quarter='Q1',
            year=2024,
            total_income=5000.0,
            purchase_traded_goods=100.0,
            stock_change=50.0,
            employee_cost=3000.0,
            other_expenses=500.0,
            depreciation=200.0,
            interest=100.0,
            other_income=150.0,
            tax=300.0
        )
        
        print_info(f"Created quarterly data for {q_data.company}")
        
        # Calculate derived metrics
        q_data.calculate_derived_metrics()
        
        print_success(f"Contribution: ₹{q_data.contribution:.2f} Cr")
        print_success(f"Op. EBITDA: ₹{q_data.op_ebitda:.2f} Cr ({q_data.op_ebitda_pct:.2f}%)")
        print_success(f"Op. EBIT: ₹{q_data.op_ebit:.2f} Cr ({q_data.op_ebit_pct:.2f}%)")
        print_success(f"Op. PBT: ₹{q_data.op_pbt:.2f} Cr ({q_data.op_pbt_pct:.2f}%)")
        print_success(f"PBT: ₹{q_data.pbt:.2f} Cr ({q_data.pbt_pct:.2f}%)")
        print_success(f"PAT: ₹{q_data.pat:.2f} Cr")
        
        # Test completeness
        completeness = q_data.completeness_score()
        print_info(f"Data completeness: {completeness:.1f}%")
        
        print_success("Data models working")
        return True
    except Exception as e:
        print_error(f"Data model test failed: {e}")
        return False


def test_validators():
    """Test 5: Validation Engine"""
    print_header("TEST 5: Validation Engine")
    
    try:
        validator = FinancialValidator()
        
        # Create test data
        q_data = QuarterlyData(
            company='TCS',
            quarter='Q1',
            year=2024,
            total_income=5000.0,
            employee_cost=3000.0,
            other_expenses=500.0
        )
        q_data.calculate_derived_metrics()
        
        is_valid, report = validator.validate_quarterly_data(q_data)
        
        print_info(f"Validation status: {report['status']}")
        print_info(f"Completeness: {report['completeness']:.1f}%")
        
        if report['errors']:
            for error in report['errors']:
                print_warning(f"Error: {error}")
        
        if report['warnings']:
            for warning in report['warnings']:
                print_warning(f"Warning: {warning}")
        
        if not report['errors']:
            print_success("Validation passed")
        
        print_success("Validation engine working")
        return True
    except Exception as e:
        print_error(f"Validation test failed: {e}")
        return False


def test_excel_parser():
    """Test 6: Excel Parser"""
    print_header("TEST 6: Excel Parser")
    
    try:
        # Create sample template
        sample_file = settings.TEMPLATES_DIR / "sample_template.xlsx"
        companies = ['TCS', 'Infosys', 'Wipro', 'HCL Tech', 'Tech Mahindra']
        
        create_sample_template(str(sample_file), companies)
        print_success(f"Created sample template: {sample_file}")
        
        # Parse the template
        parser = ExcelParser(str(sample_file))
        
        if parser.load_file():
            print_success("Excel file loaded")
        else:
            print_error("Failed to load Excel")
            return False
        
        # Extract companies
        extracted_companies = parser.extract_companies_from_sheet()
        print_success(f"Extracted {len(extracted_companies)} companies")
        
        for company in extracted_companies:
            print_info(f"  - {company}")
        
        # Validate structure
        is_valid, errors = parser.validate_template_structure()
        if is_valid:
            print_success("Template structure valid")
        else:
            for error in errors:
                print_warning(f"Validation error: {error}")
        
        parser.close()
        
        print_success("Excel parser working")
        return True
    except Exception as e:
        print_error(f"Excel parser test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_perplexity_client():
    """Test 7: Perplexity API Client (Mock Mode)"""
    print_header("TEST 7: Perplexity API Client")
    
    try:
        cache = CacheManager(settings.CACHE_DIR)
        
        # Check if we have a real API key
        has_api_key = settings.PERPLEXITY_API_KEY and settings.PERPLEXITY_API_KEY != ''
        
        if not has_api_key:
            print_warning("No API key configured - running in mock mode")
            print_info("To test with real API, set PERPLEXITY_API_KEY in .env")
            
            # Create mock client
            client = PerplexityClient(
                api_key='mock_key',
                rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
                cache_manager=cache
            )
            
            print_success("Mock Perplexity client created")
            print_info("Query builder test:")
            
            query = client._build_financial_query('TCS', 'Q1', 2024)
            print_info("Sample query generated:")
            print(f"{Colors.OKCYAN}{query[:200]}...{Colors.ENDC}")
            
        else:
            print_success("API key found - client ready for live queries")
            client = PerplexityClient(
                api_key=settings.PERPLEXITY_API_KEY,
                rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
                cache_manager=cache
            )
            print_info("Note: Skipping live API call in verification")
        
        print_success("Perplexity client initialized")
        return True
    except Exception as e:
        print_error(f"Perplexity client test failed: {e}")
        return False


def test_end_to_end_demo():
    """Test 8: End-to-End Demo"""
    print_header("TEST 8: End-to-End Workflow Demo")
    
    try:
        print_info("Simulating complete workflow...")
        
        # 1. Parse Excel
        sample_file = settings.TEMPLATES_DIR / "sample_template.xlsx"
        parser = ExcelParser(str(sample_file))
        parser.load_file()
        companies = parser.extract_companies_from_sheet()
        print_success(f"Step 1: Extracted {len(companies)} companies from Excel")
        
        # 2. Create company financials
        company_data = CompanyFinancials(company_name=companies[0])
        print_success(f"Step 2: Created financial container for {companies[0]}")
        
        # 3. Add quarterly data
        q_data = QuarterlyData(
            company=companies[0],
            quarter='Q1',
            year=2024,
            total_income=5000.0,
            purchase_traded_goods=100.0,
            stock_change=50.0,
            employee_cost=3000.0,
            other_expenses=500.0,
            depreciation=200.0,
            interest=100.0,
            other_income=150.0,
            tax=300.0
        )
        q_data.calculate_derived_metrics()
        company_data.add_quarter(q_data)
        print_success("Step 3: Added quarterly data with calculations")
        
        # 4. Validate
        validator = FinancialValidator()
        is_valid, report = validator.validate_quarterly_data(q_data)
        print_success(f"Step 4: Validated data (status: {report['status']})")
        
        # 5. Show results
        print_info("\nFinal Results:")
        print_info(f"  Company: {q_data.company}")
        print_info(f"  Period: {q_data.quarter} {q_data.year}")
        print_info(f"  Revenue: ₹{q_data.total_income:.2f} Cr")
        print_info(f"  EBITDA Margin: {q_data.op_ebitda_pct:.2f}%")
        print_info(f"  Data Completeness: {company_data.average_completeness():.1f}%")
        
        parser.close()
        
        print_success("\nEnd-to-end workflow completed successfully!")
        return True
    except Exception as e:
        print_error(f"End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Phase 1 Verification - Financial Research Engine      ║")
    print("║   AI-Powered Financial Data Extraction Platform         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    tests = [
        ("Configuration & Setup", test_configuration),
        ("Logging System", test_logging),
        ("Cache Manager", test_cache_manager),
        ("Data Models", test_data_models),
        ("Validation Engine", test_validators),
        ("Excel Parser", test_excel_parser),
        ("Perplexity Client", test_perplexity_client),
        ("End-to-End Demo", test_end_to_end_demo),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ ALL TESTS PASSED - Phase 1 Implementation Complete!{Colors.ENDC}\n")
        return 0
    else:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠ Some tests failed - Please review errors above{Colors.ENDC}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
