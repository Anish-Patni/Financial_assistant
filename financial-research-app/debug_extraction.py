#!/usr/bin/env python3
"""Debug extraction to see why interest is not being extracted"""

import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.data_extractor import FinancialDataExtractor

# Load the Tech Mahindra Q2 2025 data
with open('data/research_results/Tech_Mahindra_Q2_2025.json', 'r') as f:
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

# Check specifically for interest
print("CHECKING FOR INTEREST:")
print("=" * 80)
interest_result = extractor.extract_indicator(raw_response, 'interest')
if interest_result:
    print(f"Interest extracted: {interest_result}")
else:
    print("Interest NOT extracted")
print()

# Check if interest is in the patterns
print("INTEREST PATTERNS:")
for i, pattern in enumerate(extractor.patterns['interest']):
    print(f"Pattern {i}: {pattern.pattern}")
    match = pattern.search(raw_response)
    if match:
        print(f"  ✓ MATCHES: {match.group()}")
        print(f"  Value would be: {match.group(1)}")
    else:
        print(f"  ✗ No match")
print("=" * 80)
