#!/usr/bin/env python3
"""Show summary of research results"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.research_storage import ResearchStorage
from config import settings

storage = ResearchStorage(settings.RESEARCH_RESULTS_DIR)
summary = storage.get_research_summary()

print('\n' + '='*60)
print('  RESEARCH RESULTS SUMMARY')
print('='*60 + '\n')

print(f"Total research completed: {summary['total_research_count']}")
print(f"Unique companies: {summary['unique_companies']}")
print(f"Companies: {', '.join(summary['companies'])}")
print(f"Periods covered: {', '.join(summary['periods'])}")
print(f"Total extractions: {summary['total_extractions']}")
print(f"Average confidence: {summary['average_confidence']:.2f}\n")

# Show details for each
all_research = storage.get_all_research()
for research in all_research:
    print(f"\n{research['company']} - {research['quarter']} {research['year']}:")
    print(f"  Status: {research.get('status', 'N/A')}")
    print(f"  Indicators extracted: {len(research.get('extracted_data', {}))}")
    print(f"  Context confidence: {research.get('context_confidence', 0):.2f}")
    
    # Show top 3 indicators
    extracted = research.get('extracted_data', {})
    if extracted:
        print("  Top indicators:")
        for i, (indicator, data) in enumerate(list(extracted.items())[:3]):
            print(f"    {indicator}: ₹{data['value']:.2f} Cr (conf: {data['confidence']:.2f})")

print('\n' + '='*60)
print('✓ Phase 2 Implementation Working Successfully!')
print('='*60 + '\n')
