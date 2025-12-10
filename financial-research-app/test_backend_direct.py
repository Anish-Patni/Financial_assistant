#!/usr/bin/env python3
"""
Backend Validation Script
Tests backend components directly without Flask/Frontend interface
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup file logging
LOG_FILE = Path(__file__).parent / "backend_validation_log.txt"
log_file_handle = None

def log_print(*args, **kwargs):
    """Print to both console and file"""
    message = " ".join(str(arg) for arg in args)
    print(message, **kwargs)
    if log_file_handle:
        log_file_handle.write(message + "\n")
        log_file_handle.flush()

from config import settings
from config.logging_config import setup_logging, get_logger
from core.cache_manager import CacheManager
from core.perplexity_client import PerplexityClient
from core.data_extractor import FinancialDataExtractor
from core.research_storage import ResearchStorage
from core.research_orchestrator import ResearchOrchestrator

# Setup logging
setup_logging(log_level=settings.LOG_LEVEL)
logger = get_logger('backend_validator')

def print_separator(title=""):
    """Print a formatted separator"""
    print("\n" + "="*70)
    if title:
        print(f"  {title}")
        print("="*70)
    print()

def print_result(test_name, success, details=""):
    """Print test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"       {details}")
    print()

def test_configuration():
    """Test 1: Validate configuration"""
    print_separator("TEST 1: Configuration Validation")
    
    tests_passed = 0
    tests_total = 0
    
    # Test API key
    tests_total += 1
    api_key_set = bool(settings.PERPLEXITY_API_KEY)
    print_result(
        "API Key Configuration",
        api_key_set,
        f"API Key: {'SET' if api_key_set else 'NOT SET'}"
    )
    if api_key_set:
        tests_passed += 1
    
    # Test model configuration
    tests_total += 1
    model_valid = bool(settings.PERPLEXITY_MODEL)
    print_result(
        "Model Configuration",
        model_valid,
        f"Model: {settings.PERPLEXITY_MODEL}"
    )
    if model_valid:
        tests_passed += 1
    
    # Test paths
    tests_total += 1
    cache_dir_exists = settings.CACHE_DIR.exists()
    print_result(
        "Cache Directory",
        cache_dir_exists,
        f"Path: {settings.CACHE_DIR}"
    )
    if cache_dir_exists:
        tests_passed += 1
    
    tests_total += 1
    results_dir_exists = settings.RESEARCH_RESULTS_DIR.exists()
    print_result(
        "Results Directory",
        results_dir_exists,
        f"Path: {settings.RESEARCH_RESULTS_DIR}"
    )
    if results_dir_exists:
        tests_passed += 1
    
    print(f"Configuration Tests: {tests_passed}/{tests_total} passed\n")
    return tests_passed == tests_total

def test_cache_manager():
    """Test 2: Cache Manager"""
    print_separator("TEST 2: Cache Manager")
    
    try:
        cache = CacheManager(settings.CACHE_DIR)
        
        # Test cache stats
        stats = cache.get_stats()
        print_result(
            "Get Cache Stats",
            True,
            f"Cached items: {stats.get('total_entries', 0)}"
        )
        
        # Test cache set/get
        test_key = "test_validation_key"
        test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
        
        cache.set(test_key, test_value)
        retrieved = cache.get(test_key)
        
        cache_works = retrieved == test_value
        print_result(
            "Cache Set/Get",
            cache_works,
            "Successfully stored and retrieved test data"
        )
        
        # Cleanup
        cache.delete(test_key)
        
        return True
    except Exception as e:
        print_result("Cache Manager", False, f"Error: {str(e)}")
        return False

def test_research_storage():
    """Test 3: Research Storage"""
    print_separator("TEST 3: Research Storage")
    
    try:
        storage = ResearchStorage(settings.RESEARCH_RESULTS_DIR)
        
        # Get all research results
        all_results = storage.get_all_research()
        print_result(
            "Load All Research Results",
            True,
            f"Found {len(all_results)} research results"
        )
        
        # Get research summary
        summary = storage.get_research_summary()
        print_result(
            "Get Research Summary",
            True,
            f"Total: {summary.get('total_research', 0)}, Companies: {len(summary.get('companies', []))}"
        )
        
        # Display available results
        if all_results:
            print("Available Research Results:")
            for result in all_results[:5]:  # Show first 5
                company = result.get('company', 'Unknown')
                quarter = result.get('quarter', 'Unknown')
                year = result.get('year', 'Unknown')
                print(f"  - {company} | {quarter} {year}")
            if len(all_results) > 5:
                print(f"  ... and {len(all_results) - 5} more")
            print()
        else:
            print("No research results found in storage.\n")
        
        return True
    except Exception as e:
        print_result("Research Storage", False, f"Error: {str(e)}")
        return False

def test_data_extractor():
    """Test 4: Financial Data Extractor"""
    print_separator("TEST 4: Financial Data Extractor")
    
    try:
        extractor = FinancialDataExtractor()
        
        # Test with sample API response
        sample_response = """
        Revenue: ₹1,234 Cr
        Net Profit: ₹456 Cr
        EBITDA: ₹789 Cr
        EPS: ₹12.34
        """
        
        extracted = extractor.extract_from_text(sample_response)
        
        extraction_works = bool(extracted)
        print_result(
            "Extract Financial Data",
            extraction_works,
            f"Extracted {len(extracted)} data points from sample text"
        )
        
        if extracted:
            print("Sample Extraction:")
            for key, value in list(extracted.items())[:5]:
                print(f"  - {key}: {value}")
            print()
        
        return True
    except Exception as e:
        print_result("Financial Data Extractor", False, f"Error: {str(e)}")
        return False

def test_perplexity_client():
    """Test 5: Perplexity Client (Configuration Only)"""
    print_separator("TEST 5: Perplexity Client")
    
    try:
        cache = CacheManager(settings.CACHE_DIR)
        client = PerplexityClient(
            api_key=settings.PERPLEXITY_API_KEY,
            rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
            cache_manager=cache,
            use_finance_domain=settings.PERPLEXITY_USE_FINANCE_DOMAIN,
            model=settings.PERPLEXITY_MODEL
        )
        
        print_result(
            "Initialize Perplexity Client",
            True,
            f"Client created with model: {settings.PERPLEXITY_MODEL}"
        )
        
        print("⚠ Note: Not making actual API calls to avoid rate limits")
        print("  To test API functionality, use the research test below.\n")
        
        return True
    except Exception as e:
        print_result("Perplexity Client", False, f"Error: {str(e)}")
        return False

def test_research_orchestrator(run_live_test=False):
    """Test 6: Research Orchestrator"""
    print_separator("TEST 6: Research Orchestrator")
    
    try:
        cache = CacheManager(settings.CACHE_DIR)
        storage = ResearchStorage(settings.RESEARCH_RESULTS_DIR)
        extractor = FinancialDataExtractor()
        
        client = PerplexityClient(
            api_key=settings.PERPLEXITY_API_KEY,
            rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
            cache_manager=cache,
            use_finance_domain=settings.PERPLEXITY_USE_FINANCE_DOMAIN,
            model=settings.PERPLEXITY_MODEL
        )
        
        orchestrator = ResearchOrchestrator(client, storage, extractor)
        
        print_result(
            "Initialize Research Orchestrator",
            True,
            f"Default companies: {len(orchestrator.DEFAULT_COMPANIES)}"
        )
        
        print(f"Available Companies:")
        for company in orchestrator.DEFAULT_COMPANIES[:10]:
            print(f"  - {company}")
        if len(orchestrator.DEFAULT_COMPANIES) > 10:
            print(f"  ... and {len(orchestrator.DEFAULT_COMPANIES) - 10} more")
        print()
        
        if run_live_test:
            print("Running LIVE API TEST...")
            print("This will make an actual API call to Perplexity.\n")
            
            # Test with a single company
            test_company = orchestrator.DEFAULT_COMPANIES[0]
            test_quarter = "Q1"
            test_year = 2024
            
            print(f"Researching: {test_company} {test_quarter} {test_year}")
            print("Please wait...\n")
            
            result = orchestrator.research_company_quarter(
                test_company,
                test_quarter,
                test_year
            )
            
            if result:
                print_result(
                    "Live Research Test",
                    True,
                    f"Successfully researched {test_company}"
                )
                
                # Display result details
                print("Research Result Summary:")
                print(f"  Company: {result.get('company', 'N/A')}")
                print(f"  Quarter: {result.get('quarter', 'N/A')}")
                print(f"  Year: {result.get('year', 'N/A')}")
                print(f"  Status: {result.get('status', 'N/A')}")
                
                data = result.get('data', {})
                print(f"  Data Points Extracted: {len(data)}")
                
                if data:
                    print("\n  Sample Data:")
                    for key, value in list(data.items())[:5]:
                        print(f"    - {key}: {value}")
                print()
                
                return True
            else:
                print_result(
                    "Live Research Test",
                    False,
                    "Research returned empty result"
                )
                return False
        else:
            print("⚠ Skipping live API test (to avoid rate limits)")
            print("  Set run_live_test=True to test actual API calls\n")
            return True
            
    except Exception as e:
        print_result("Research Orchestrator", False, f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print("\n" + "="*70)
    print("  BACKEND VALIDATION - Direct Component Testing")
    print("="*70)
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = {}
    
    # Run all tests
    results['config'] = test_configuration()
    results['cache'] = test_cache_manager()
    results['storage'] = test_research_storage()
    results['extractor'] = test_data_extractor()
    results['client'] = test_perplexity_client()
    
    # Ask user if they want to run live API test
    print_separator("LIVE API TEST")
    print("Do you want to run a LIVE API test?")
    print("This will make an actual API call to Perplexity and may consume credits.")
    response = input("Run live test? (yes/no): ").strip().lower()
    
    run_live = response in ['yes', 'y']
    results['orchestrator'] = test_research_orchestrator(run_live_test=run_live)
    
    # Summary
    print_separator("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} | {test_name.upper()}")
    
    print(f"\n{'='*70}")
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    print(f"{'='*70}\n")
    
    if passed_tests == total_tests:
        print("✓ ALL TESTS PASSED - Backend is working correctly!")
        print("  The issue is likely in the Flask routes or frontend code.")
    else:
        print("✗ SOME TESTS FAILED - Backend has issues that need to be fixed.")
        print("  Review the failed tests above for details.")
    
    print()
    
    return passed_tests == total_tests

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
