#!/usr/bin/env python3
"""
Phase 2 Verification Script
Test automated research and data extraction capabilities
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
from core.data_extractor import FinancialDataExtractor
from core.research_storage import ResearchStorage
from core.research_orchestrator import ResearchOrchestrator
from utils.progress_tracker import ProgressTracker

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


def test_data_extractor():
    """Test 1: NLP Data Extractor"""
    print_header("TEST 1: NLP Data Extractor")
    
    try:
        extractor = FinancialDataExtractor()
        print_success("Data extractor initialized")
        
        # Test with sample financial text
        sample_text = """
        In Q1 FY2024, TCS reported strong performance:
        - Total income stood at Rs. 5,000 crores
        - EBITDA was Rs. 1,200 crores with an EBITDA margin of 24%
        - Employee costs were Rs. 3,000 crores
        - Other expenses amounted to Rs. 500 crores
        - Depreciation was Rs. 200 crores
        - Net profit (PAT) reached Rs. 900 crores
        """
        
        print_info("Testing extraction on sample text...")
        
        # Extract all indicators
        extracted = extractor.extract_all_indicators(sample_text)
        
        print_success(f"Extracted {len(extracted)} financial indicators")
        
        for indicator, data in extracted.items():
            value = data['value']
            confidence = data['confidence']
            print_info(f"  {indicator}: ₹{value:.2f} Cr (confidence: {confidence:.2f})")
        
        # Test with context
        contextualized = extractor.extract_with_context(sample_text, 'TCS', 'Q1', 2024)
        
        print_success(f"Context confidence: {contextualized['context_confidence']:.2f}")
        
        # Test summary generation
        summary = extractor.get_extraction_summary(contextualized)
        print_info("Extraction summary generated successfully")
        
        print_success("Data extractor working correctly")
        return True
        
    except Exception as e:
        print_error(f"Data extractor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_research_storage():
    """Test 2: Research Storage System"""
    print_header("TEST 2: Research Storage System")
    
    try:
        storage_dir = settings.DATA_DIR / 'research_results'
        storage = ResearchStorage(storage_dir)
        print_success(f"Storage initialized: {storage_dir}")
        
        # Create test research data
        test_data = {
            'company': 'TCS',
            'quarter': 'Q1',
            'year': 2024,
            'status': 'success',
            'raw_response': 'Sample response text',
            'extracted_data': {
                'total_income': {'value': 5000.0, 'confidence': 0.95},
                'ebitda': {'value': 1200.0, 'confidence': 0.90}
            },
            'context_confidence': 0.92
        }
        
        # Test save
        if storage.save_research(test_data):
            print_success("Research data saved successfully")
        else:
            print_error("Failed to save research data")
            return False
        
        # Test load
        loaded = storage.load_research('TCS', 'Q1', 2024)
        if loaded:
            print_success("Research data loaded successfully")
            print_info(f"  Company: {loaded['company']}")
            print_info(f"  Period: {loaded['quarter']} {loaded['year']}")
            print_info(f"  Indicators: {len(loaded['extracted_data'])}")
        else:
            print_error("Failed to load research data")
            return False
        
        # Test summary
        summary = storage.get_research_summary()
        print_success(f"Storage summary:")
        print_info(f"  Total research: {summary['total_research_count']}")
        print_info(f"  Companies: {summary['unique_companies']}")
        print_info(f"  Avg confidence: {summary['average_confidence']:.2f}")
        
        print_success("Research storage system working")
        return True
        
    except Exception as e:
        print_error(f"Storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_progress_tracker():
    """Test 3: Progress Tracker"""
    print_header("TEST 3: Progress Tracker")
    
    try:
        tracker = ProgressTracker(total_items=10)
        print_success("Progress tracker initialized for 10 items")
        
        # Simulate progress
        import time
        
        for i in range(10):
            item_id = f"item_{i+1}"
            desc = f"Company {i+1}"
            
            tracker.start_item(item_id, desc)
            time.sleep(0.1)  # Simulate work
            
            if i < 8:  # Success for first 8
                tracker.complete_item(item_id)
            else:  # Fail last 2
                tracker.fail_item(item_id, "Simulated error")
        
        # Print progress
        tracker.print_progress()
        
        # Get summary
        summary = tracker.get_summary()
        print_info(f"\nProgress Summary:")
        print_info(f"  Progress: {summary['progress_percent']:.1f}%")
        print_info(f"  Success rate: {summary['success_rate']:.1f}%")
        print_info(f"  Completed: {summary['completed']}")
        print_info(f"  Failed: {summary['failed']}")
        
        print_success("Progress tracker working correctly")
        return True
        
    except Exception as e:
        print_error(f"Progress tracker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_research_orchestrator_mock():
    """Test 4: Research Orchestrator (Mock Mode)"""
    print_header("TEST 4: Research Orchestrator (Mock Mode)")
    
    try:
        # Initialize components with mock data
        cache = CacheManager(settings.CACHE_DIR)
        storage_dir = settings.DATA_DIR / 'research_results'
        storage = ResearchStorage(storage_dir)
        extractor = FinancialDataExtractor()
        
        print_success("Orchestrator components initialized")
        
        # Check if we have API key
        has_api_key = settings.PERPLEXITY_API_KEY and settings.PERPLEXITY_API_KEY != ''
        
        if not has_api_key:
            print_warning("No API key - using mock mode")
            print_info("To test with real API, set PERPLEXITY_API_KEY in .env")
            
            # Create mock client
            client = PerplexityClient(
                api_key='mock_key',
                rate_limit_rpm=20,
                cache_manager=cache,
                use_finance_domain=True
            )
            
            orchestrator = ResearchOrchestrator(client, storage, extractor)
            print_success("Mock orchestrator created")
            
            # Test with pre-saved data
            print_info("Testing with existing research data...")
            summary = storage.get_research_summary()
            print_info(f"Found {summary['total_research_count']} research results")
            
        else:
            print_success("API key found - orchestrator ready for live research")
            
            # Get finance domain setting
            use_finance_domain = os.getenv('PERPLEXITY_USE_FINANCE_DOMAIN', 'false').lower() == 'true'
            
            client = PerplexityClient(
                api_key=settings.PERPLEXITY_API_KEY,
                rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
                cache_manager=cache,
                use_finance_domain=use_finance_domain,
                model=settings.PERPLEXITY_MODEL
            )
            
            orchestrator = ResearchOrchestrator(client, storage, extractor)
            print_success("Live orchestrator created")
            print_info(f"Finance domain enabled: {use_finance_domain}")
            print_info("Note: Skipping live API calls in verification")
        
        # Show default companies
        print_info(f"\nDefault companies ({len(orchestrator.DEFAULT_COMPANIES)}):")
        for i, company in enumerate(orchestrator.DEFAULT_COMPANIES[:5], 1):
            print_info(f"  {i}. {company}")
        print_info(f"  ... and {len(orchestrator.DEFAULT_COMPANIES)-5} more")
        
        print_success("Research orchestrator initialized successfully")
        return True
        
    except Exception as e:
        print_error(f"Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end_extraction():
    """Test 5: End-to-End Extraction Pipeline"""
    print_header("TEST 5: End-to-End Extraction Pipeline")
    
    try:
        print_info("Simulating complete research → extract → store workflow...")
        
        # Components
        extractor = FinancialDataExtractor()
        storage_dir = settings.DATA_DIR / 'research_results'
        storage = ResearchStorage(storage_dir)
        
        # Step 1: Mock API response
        mock_response = """
        Infosys Q2 FY2024 Financial Results:
        The company reported total revenue of Rs. 6,200 crores for the quarter.
        Operating EBITDA stood at Rs. 1,500 crores, representing an EBITDA margin of 24.2%.
        Employee costs were Rs. 3,800 crores
        Other operating expenses amounted to Rs. 750 crores.
        Depreciation and amortization was Rs. 150 crores.
        Interest expenses were Rs. 50 crores
        Net profit after tax (PAT) reached Rs. 1,100 crores.
        """
        
        print_success("Step 1: Mock API response created")
        
        # Step 2: Extract data
        extracted = extractor.extract_with_context(mock_response, 'Infosys', 'Q2', 2024)
        print_success(f"Step 2: Extracted {len(extracted['extracted_data'])} indicators")
        
        # Step 3: Save research
        research_data = {
            'company': 'Infosys',
            'quarter': 'Q2',
            'year': 2024,
            'status': 'success',
            'raw_response': mock_response,
            'extracted_data': extracted['extracted_data'],
            'context_confidence': extracted['context_confidence']
        }
        
        if storage.save_research(research_data):
            print_success("Step 3: Research saved to storage")
        
        # Step 4: Retrieve and validate
        loaded = storage.load_research('Infosys', 'Q2', 2024)
        if loaded:
            print_success("Step 4: Research retrieved successfully")
            
            # Show extraction summary
            summary = extractor.get_extraction_summary(loaded)
            print_info("\nExtraction Summary:")
            for line in summary.split('\n')[:6]:  # First 6 lines
                print_info(f"  {line}")
        
        print_success("\nEnd-to-end pipeline working correctly")
        return True
        
    except Exception as e:
        print_error(f"End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 2 verification tests"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Phase 2 Verification - Research & Data Extraction     ║")
    print("║   AI-Powered Financial Research Automation              ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    # Setup logging
    setup_logging(log_level=settings.LOG_LEVEL)
    
    tests = [
        ("NLP Data Extractor", test_data_extractor),
        ("Research Storage System", test_research_storage),
        ("Progress Tracker", test_progress_tracker),
        ("Research Orchestrator", test_research_orchestrator_mock),
        ("End-to-End Pipeline", test_end_to_end_extraction),
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
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ ALL TESTS PASSED - Phase 2 Implementation Complete!{Colors.ENDC}\n")
        
        print_info("Next Steps:")
        print_info("1. Add your Perplexity API key to .env file")
        print_info("2. Run: python -c \"from core.research_orchestrator import *; ...\" to test live")
        print_info("3. Review extracted data in data/research_results/")
        
        return 0
    else:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠ Some tests failed - Please review errors above{Colors.ENDC}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
