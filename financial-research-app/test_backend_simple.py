#!/usr/bin/env python3
"""
Simple Backend Validation Script - Non-Interactive
Tests backend components directly without Flask/Frontend interface
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

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

def main():
    """Run all validation tests"""
    
    output_file = Path(__file__).parent / "backend_validation_results.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        def log(msg=""):
            """Log to both console and file"""
            print(msg)
            f.write(msg + "\n")
            f.flush()
        
        log("="*70)
        log(" BACKEND VALIDATION - Direct Component Testing")
        log("="*70)
        log(f" Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log("="*70)
        log()
        
        results = {}
        
        # Test 1: Configuration
        log("="*70)
        log(" TEST 1: Configuration Validation")
        log("="*70)
        log()
        
        try:
            api_key_set = bool(settings.PERPLEXITY_API_KEY)
            log(f"{'✓' if api_key_set else '✗'} API Key: {'SET' if api_key_set else 'NOT SET'}")
            
            log(f"✓ Model: {settings.PERPLEXITY_MODEL}")
            log(f"✓ Finance Domain: {settings.PERPLEXITY_USE_FINANCE_DOMAIN}")
            log(f"✓ Rate Limit: {settings.RATE_LIMIT_REQUESTS_PER_MINUTE} RPM")
            
            cache_exists = settings.CACHE_DIR.exists()
            log(f"{'✓' if cache_exists else '✗'} Cache Dir: {settings.CACHE_DIR}")
            
            results_exists = settings.RESEARCH_RESULTS_DIR.exists()
            log(f"{'✓' if results_exists else '✗'} Results Dir: {settings.RESEARCH_RESULTS_DIR}")
            
            results['config'] = api_key_set and cache_exists and results_exists
            log()
        except Exception as e:
            log(f"✗ Configuration Test Failed: {e}")
            results['config'] = False
            log()
        
        # Test 2: Cache Manager
        log("="*70)
        log(" TEST 2: Cache Manager")
        log("="*70)
        log()
        
        try:
            cache = CacheManager(settings.CACHE_DIR)
            stats = cache.get_stats()
            log(f"✓ Cache initialized successfully")
            log(f"✓ Cached items: {stats.get('total_entries', 0)}")
            
            # Test cache operations
            test_key = "validation_test"
            test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
            cache.set(test_key, test_data)
            retrieved = cache.get(test_key)
            cache.delete(test_key)
            
            if retrieved == test_data:
                log(f"✓ Cache set/get/delete operations work correctly")
                results['cache'] = True
            else:
                log(f"✗ Cache operations failed")
                results['cache'] = False
            log()
        except Exception as e:
            log(f"✗ Cache Manager Test Failed: {e}")
            results['cache'] = False
            log()
        
        # Test 3: Research Storage
        log("="*70)
        log(" TEST 3: Research Storage")
        log("="*70)
        log()
        
        try:
            storage = ResearchStorage(settings.RESEARCH_RESULTS_DIR)
            all_results = storage.get_all_research()
            summary = storage.get_research_summary()
            
            log(f"✓ Storage initialized successfully")
            log(f"✓ Total research results: {len(all_results)}")
            log(f"✓ Companies researched: {len(summary.get('companies', []))}")
            log(f"✓ Quarters covered: {summary.get('quarters', [])}")
            log(f"✓ Years covered: {summary.get('years', [])}")
            
            if all_results:
                log()
                log("Sample Results (first 5):")
                for i, res in enumerate(all_results[:5], 1):
                    log(f"  {i}. {res.get('company', 'N/A')} | {res.get('quarter', 'N/A')} {res.get('year', 'N/A')}")
                if len(all_results) > 5:
                    log(f"  ... and {len(all_results) - 5} more")
            else:
                log()
                log("⚠ Warning: No research results found in storage")
            
            results['storage'] = True
            log()
        except Exception as e:
            log(f"✗ Research Storage Test Failed: {e}")
            import traceback
            log(traceback.format_exc())
            results['storage'] = False
            log()
        
        # Test 4: Financial Data Extractor
        log("="*70)
        log(" TEST 4: Financial Data Extractor")
        log("="*70)
        log()
        
        try:
            extractor = FinancialDataExtractor()
            
            # Test with sample text
            sample_text = """
            Revenue: ₹1,234 Cr
            Net Profit: ₹456 Cr
            EBITDA: ₹789 Cr
            EPS: ₹12.34
            Profit Margin: 15.5%
            """
            
            extracted = extractor.extract_from_text(sample_text)
            
            log(f"✓ Extractor initialized successfully")
            log(f"✓ Extracted {len(extracted)} data points from sample text")
            
            if extracted:
                log()
                log("Sample Extraction:")
                for key, value in list(extracted.items())[:5]:
                    log(f"  - {key}: {value}")
            
            results['extractor'] = len(extracted) > 0
            log()
        except Exception as e:
            log(f"✗ Data Extractor Test Failed: {e}")
            import traceback
            log(traceback.format_exc())
            results['extractor'] = False
            log()
        
        # Test 5: Perplexity Client
        log("="*70)
        log(" TEST 5: Perplexity Client (Init Only)")
        log("="*70)
        log()
        
        try:
            cache = CacheManager(settings.CACHE_DIR)
            client = PerplexityClient(
                api_key=settings.PERPLEXITY_API_KEY,
                rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
                cache_manager=cache,
                use_finance_domain=settings.PERPLEXITY_USE_FINANCE_DOMAIN,
                model=settings.PERPLEXITY_MODEL
            )
            
            log(f"✓ Perplexity client initialized successfully")
            log(f"✓ Using model: {settings.PERPLEXITY_MODEL}")
            log(f"✓ Finance domain: {settings.PERPLEXITY_USE_FINANCE_DOMAIN}")
            log()
            log("⚠ Skipping actual API call to avoid rate limits")
            
            results['client'] = True
            log()
        except Exception as e:
            log(f"✗ Perplexity Client Test Failed: {e}")
            import traceback
            log(traceback.format_exc())
            results['client'] = False
            log()
        
        # Test 6: Research Orchestrator
        log("="*70)
        log(" TEST 6: Research Orchestrator")
        log("="*70)
        log()
        
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
            
            log(f"✓ Research Orchestrator initialized successfully")
            log(f"✓ Default companies available: {len(orchestrator.DEFAULT_COMPANIES)}")
            
            log()
            log("Sample Companies (first 10):")
            for i, company in enumerate(orchestrator.DEFAULT_COMPANIES[:10], 1):
                log(f"  {i}. {company}")
            if len(orchestrator.DEFAULT_COMPANIES) > 10:
                log(f"  ... and {len(orchestrator.DEFAULT_COMPANIES) - 10} more")
            
            results['orchestrator'] = True
            log()
        except Exception as e:
            log(f"✗ Research Orchestrator Test Failed: {e}")
            import traceback
            log(traceback.format_exc())
            results['orchestrator'] = False
            log()
        
        # Summary
        log("="*70)
        log(" TEST SUMMARY")
        log("="*70)
        log()
        
        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            log(f"{status} | {test_name.upper()}")
        
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        
        log()
        log("="*70)
        log(f" Total: {passed}/{total} tests passed")
        log("="*70)
        log()
        
        if passed == total:
            log("✓ ALL TESTS PASSED - Backend is working correctly!")
            log()
            log("CONCLUSION:")
            log("  The backend components are functioning properly.")
            log("  Since you're not seeing output in the frontend, the issue is")
            log("  likely in one of these areas:")
            log("    1. Flask route handlers not returning data correctly")
            log("    2. Frontend JavaScript not making API calls correctly")
            log("    3. Frontend JavaScript not handling/displaying responses")
            log("    4. CORS or network issues between frontend and backend")
        else:
            log("✗ SOME TESTS FAILED - Backend has issues!")
            log()
            log("CONCLUSION:")
            log("  The backend has problems that need to be fixed first.")
            log("  Review the failed tests above for details.")
        
        log()
        log(f"Full results saved to: {output_file}")
        log()
    
    # Also print the file location at the end
    print()
    print("="*70)
    print(f"✓ Results saved to: {output_file}")
    print("="*70)
    
    return sum(1 for v in results.values() if v) == len(results)

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
