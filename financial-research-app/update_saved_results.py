#!/usr/bin/env python3
"""Re-extract data from saved research results to get interest and other_income"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from core.data_extractor import FinancialDataExtractor

# Get all research result files
research_dir = Path('data/research_results')
extractor = FinancialDataExtractor()

for json_file in research_dir.glob('*.json'):
    print(f"\nProcessing {json_file.name}...")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    if 'raw_response' not in data:
        print(f"  Skipping - no raw_response")
        continue
    
    # Re-extract
    raw_response = data['raw_response']
    extracted = extractor.extract_all_indicators(raw_response)
    
    # Update extracted_data
    old_data = data.get('extracted_data', {})
    new_data = {}
    
    for key, value in extracted.items():
        new_data[key] = value
    
    # Show what changed
    added_fields = set(new_data.keys()) - set(old_data.keys())
    if added_fields:
        print(f"  ✓ Added fields: {', '.join(added_fields)}")
        for field in added_fields:
            print(f"    {field}: {new_data[field]['value']}")
    
    updated_fields = []
    for key in new_data:
        if key in old_data and old_data[key].get('value') != new_data[key].get('value'):
            updated_fields.append(key)
    
    if updated_fields:
        print(f"  ✓ Updated fields: {', '.join(updated_fields)}")
    
    if not added_fields and not updated_fields:
        print(f"  No changes")
        continue
    
    # Update and save
    data['extracted_data'] = new_data
    
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  ✓ Saved updated data")

print("\n✓ All research results updated!")
