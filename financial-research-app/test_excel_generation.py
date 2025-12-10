#!/usr/bin/env python3
"""Test Excel generation with logging"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.logging_config import setup_logging, get_logger
from core.research_storage import ResearchStorage
from core.excel_generator import ExcelGenerator
from config import settings

# Setup logging to see everything
setup_logging(log_level='DEBUG')
logger = get_logger('test_excel')

# Load research results
storage = ResearchStorage(settings.RESEARCH_RESULTS_DIR)
all_results = storage.get_all_research()

print("=" * 80)
print(f"Loaded {len(all_results)} research results:")
for r in all_results:
    print(f"  - {r['company']} {r['quarter']} {r['year']}: {len(r.get('extracted_data', {}))} indicators")
print("=" * 80)

# Get template path (most recent upload)
template_path = 'data/uploads/20251210_180355_Format-NEW.xlsx'
if not Path(template_path).exists():
    print(f"\nTemplate not found: {template_path}")
    template_path = None
else:
    print(f"\nUsing template: {template_path}")

# Generate Excel
generator = ExcelGenerator()
output_path = Path('data/output/test_financial_research.xlsx')
output_path.parent.mkdir(parents=True, exist_ok=True)

print(f"\nGenerating Excel to: {output_path}")
print("=" * 80)

success = generator.generate_excel(all_results, output_path, template_path)

if success:
    print("\n" + "=" * 80)
    print(f"✓ Excel generated successfully!")
    print(f"  File: {output_path}")
    print(f"  Sheets: {generator.workbook.sheetnames if generator.workbook else 'N/A'}")
    print("=" * 80)
else:
    print("\n" + "=" * 80)
    print("✗ Excel generation failed!")
    print("=" * 80)
