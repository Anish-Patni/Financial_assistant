#!/usr/bin/env python3
"""Debug Persistent Q3 extraction"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from core.data_extractor import FinancialDataExtractor

# Load the Persistent Q3 2025 data
with open('data/research_results/Persistent_Q3_2025.json', 'r') as f:
    data = json.load(f)

raw_response = data['raw_response']
print("RAW RESPONSE:")
print("=" * 80)
print(raw_response)
print("=" * 80)
print()

# Try to extract
extractor = FinancialDataExtractor()
extracted = extractor.extract_all_indicators(raw_response)

print("EXTRACTED DATA:")
print("=" * 80)
for key, value in extracted.items():
    print(f"{key}: {value}")
print("=" * 80)
print()

# Check specifically for ebit and interest
for field in ['ebit', 'interest', 'pbt', 'pat']:
    print(f"\nCHECKING FOR {field.upper()}:")
    print("-" * 80)
    result = extractor.extract_indicator(raw_response, field)
    if result:
        print(f"✓ Extracted: {result}")
    else:
        print(f"✗ NOT extracted")
        print(f"\nTrying patterns:")
        for i, pattern in enumerate(extractor.patterns[field]):
            match = pattern.search(raw_response)
            if match:
                print(f"  Pattern {i}: MATCHES - {match.group()}")
            else:
                print(f"  Pattern {i}: No match")
