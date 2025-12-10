#!/usr/bin/env python3
"""
Live Demo - Test Phase 2 with Real Perplexity API
Tests actual API calls and data extraction
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from config.logging_config import setup_logging
from core.cache_manager import CacheManager
from core.perplexity_client import PerplexityClient
from core.data_extractor import FinancialDataExtractor
from core.research_storage import ResearchStorage
from core.research_orchestrator import ResearchOrchestrator

# Colors
class C:
    H = '\033[95m\033[1m'
    G = '\033[92m'
    Y = '\033[93m'
    B = '\033[94m'
    E = '\033[0m'

def main():
    print(f"\n{C.H}{'='*60}{C.E}")
    print(f"{C.H}  Live Demo - Financial Research with Perplexity API{C.E}")
    print(f"{C.H}{'='*60}{C.E}\n")
    
    # Setup
    setup_logging(log_level='INFO')
    
    # Check API key
    if not settings.PERPLEXITY_API_KEY:
        print(f"{C.Y}⚠ ERROR: PERPLEXITY_API_KEY not set in .env{C.E}")
        print(f"{C.Y}Please add your API key to the .env file{C.E}\n")
        return 1
    
    print(f"{C.G}✓ API key configured{C.E}")
    print(f"{C.B}ℹ Using model: {settings.PERPLEXITY_MODEL}{C.E}")
    print(f"{C.B}ℹ Finance domain: {settings.PERPLEXITY_USE_FINANCE_DOMAIN}{C.E}\n")
    
    # Initialize components
    print(f"{C.H}Initializing components...{C.E}")
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
    print(f"{C.G}✓ All components initialized{C.E}\n")
    
    # Test with TCS Q1 2024
    print(f"{C.H}{'='*60}{C.E}")
    print(f"{C.H}Testing: TCS - Q1 FY2024{C.E}")
    print(f"{C.H}{'='*60}{C.E}\n")
    
    print(f"{C.B}ℹ Querying Perplexity API...{C.E}")
    print(f"{C.Y}  (This may take 10-20 seconds){C.E}\n")
    
    try:
        result = orchestrator.research_company_quarter('TCS', 'Q1', 2024)
        
        if result.get('status') == 'success':
            print(f"{C.G}✓ Research successful!{C.E}\n")
            
            # Show raw response preview
            raw = result.get('raw_response', '')
            print(f"{C.H}API Response Preview:{C.E}")
            print(f"{C.B}{raw[:300]}...{C.E}\n")
            
            # Show extraction summary
            print(f"{C.H}Extraction Results:{C.E}")
            summary = result.get('extraction_summary', '')
            for line in summary.split('\n'):
                if 'Company:' in line or 'Period:' in line or 'Context' in line:
                    print(f"{C.B}{line}{C.E}")
                elif '₹' in line:
                    print(f"{C.G}{line}{C.E}")
                else:
                    print(line)
            
            # Show confidence analysis
            extracted_data = result.get('extracted_data', {})
            if extracted_data:
                print(f"\n{C.H}Confidence Analysis:{C.E}")
                high_conf = sum(1 for v in extracted_data.values() if v['confidence'] >= 0.9)
                med_conf = sum(1 for v in extracted_data.values() if 0.7 <= v['confidence'] < 0.9)
                low_conf = sum(1 for v in extracted_data.values() if v['confidence'] < 0.7)
                
                print(f"{C.G}  High confidence (≥0.9): {high_conf} indicators{C.E}")
                print(f"{C.Y}  Medium confidence (0.7-0.9): {med_conf} indicators{C.E}")
                if low_conf > 0:
                    print(f"  Low confidence (<0.7): {low_conf} indicators")
            
            # Check storage
            print(f"\n{C.H}Storage:{C.E}")
            print(f"{C.G}✓ Research saved to: {settings.RESEARCH_RESULTS_DIR}/TCS_Q1_2024.json{C.E}")
            
            # Show cache stats
            cache_stats = cache.get_stats()
            print(f"\n{C.H}Cache Statistics:{C.E}")
            print(f"{C.B}  Cache hits: {cache_stats['hits']}{C.E}")
            print(f"{C.B}  Cache misses: {cache_stats['misses']}{C.E}")
            print(f"{C.B}  Hit rate: {cache_stats['hit_rate_percent']}%{C.E}")
            
            print(f"\n{C.G}{'='*60}{C.E}")
            print(f"{C.G}✓ LIVE TEST SUCCESSFUL!{C.E}")
            print(f"{C.G}{'='*60}{C.E}\n")
            
            print(f"{C.B}Next steps:{C.E}")
            print(f"{C.B}1. Review extracted data in data/research_results/{C.E}")
            print(f"{C.B}2. Run again to test caching (should be instant){C.E}")
            print(f"{C.B}3. Try other companies: Infosys, Wipro, Tech Mahindra, etc.{C.E}\n")
            
            return 0
            
        else:
            print(f"{C.Y}⚠ Research failed: {result.get('error', 'Unknown error')}{C.E}\n")
            return 1
            
    except Exception as e:
        print(f"{C.Y}✗ Error: {e}{C.E}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
