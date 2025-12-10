#!/usr/bin/env python3
"""
Fix Extraction Issues Script
Re-extract data from raw responses for TCS and Tech Mahindra to fix missing Op. PBT and PBT issues
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.data_extractor import FinancialDataExtractor
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger('fix_extraction')

def fix_research_file(file_path: Path, extractor: FinancialDataExtractor):
    """Re-extract data from a research result file"""
    logger.info(f"Processing {file_path.name}")
    
    # Load existing file
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get raw response
    raw_response = data.get('raw_response', '')
    if not raw_response:
        logger.warning(f"No raw response in {file_path.name}")
        return False
    
    company = data.get('company', '')
    quarter = data.get('quarter', '')
    year = data.get('year', 0)
    
    logger.info(f"Re-extracting data for {company} {quarter} {year}")
    
    # Re-extract using improved extractor
    extracted = extractor.extract_with_context(raw_response, company, quarter, year)
    
    # Show comparison
    old_data = data.get('extracted_data', {})
    new_data = extracted['extracted_data']
    
    print(f"\n{'='*60}")
    print(f"File: {file_path.name}")
    print(f"Company: {company} {quarter} {year}")
    print(f"{'='*60}")
    
    print("\nOLD EXTRACTION:")
    for key, val in old_data.items():
        print(f"  {key}: {val['value']} (conf: {val['confidence']})")
    
    print("\nNEW EXTRACTION:")
    for key, val in new_data.items():
        print(f"  {key}: {val['value']} (conf: {val['confidence']})")
    
    print("\nADDED FIELDS:")
    added = set(new_data.keys()) - set(old_data.keys())
    for key in added:
        print(f"  ✓ {key}: {new_data[key]['value']}")
    
    print("\nREMOVED/FIXED FIELDS:")
    removed = set(old_data.keys()) - set(new_data.keys())
    for key in removed:
        print(f"  ✗ {key}: {old_data[key]['value']} (likely incorrect)")
    
    # Update file
    data['extracted_data'] = new_data
    data['context_confidence'] = extracted['context_confidence']
    
    # Backup original
    backup_path = file_path.with_suffix('.json.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Created backup: {backup_path.name}")
    
    # Save updated file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Updated {file_path.name}")
    
    return True

def main():
    """Main execution"""
    extractor = FinancialDataExtractor()
    
    # Target files with known issues
    results_dir = Path(__file__).parent / 'data' / 'research_results'
    
    problem_files = [
        'TCS_Q1_2024.json',
        'TCS_Q2_2024.json',
        'Tech_Mahindra_Q1_2024.json',
        'Tech_Mahindra_Q2_2024.json',
        'Tech_Mahindra_Q3_2024.json',
        'Tech_Mahindra_Q4_2024.json',
    ]
    
    print("\n" + "="*60)
    print("FIXING EXTRACTION ISSUES")
    print("="*60)
    print("\nThis script will re-extract financial data using improved patterns")
    print("to fix missing Op. PBT and PBT values.\n")
    
    fixed_count = 0
    
    for filename in problem_files:
        file_path = results_dir / filename
        if file_path.exists():
            try:
                if fix_research_file(file_path, extractor):
                    fixed_count += 1
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
        else:
            logger.warning(f"File not found: {filename}")
    
    print("\n" + "="*60)
    print(f"SUMMARY: Fixed {fixed_count} files")
    print("="*60)
    print("\nBackup files (.json.backup) have been created.")
    print("If everything looks good, you can delete the backup files.")
    print("\nReload the web application to see the updated data.")

if __name__ == '__main__':
    main()
