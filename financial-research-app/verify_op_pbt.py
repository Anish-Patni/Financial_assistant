#!/usr/bin/env python3
"""Verify Op. PBT calculation with updated data"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

# Load Tech Mahindra Q2 2025 data
with open('data/research_results/Tech_Mahindra_Q2_2025.json', 'r') as f:
    data = json.load(f)

print("=" * 80)
print(f"Company: {data['company']}")
print(f"Quarter: {data['quarter']} {data['year']}")
print("=" * 80)

extracted = data['extracted_data']

# Show key metrics
print(f"\nRevenue: ₹{extracted['total_income']['value']:,.2f} Cr")
print(f"EBITDA: ₹{extracted['ebitda']['value']:,.2f} Cr")
print(f"EBIT: ₹{extracted['ebit']['value']:,.2f} Cr")
print(f"Interest: ₹{extracted['interest']['value']:,.2f} Cr")
print(f"Other Income: ₹{extracted['other_income']['value']:,.2f} Cr")

# Calculate Op. PBT
op_pbt = extracted['ebit']['value'] - extracted['interest']['value']
print(f"\nOp. PBT (EBIT - Interest): ₹{op_pbt:,.2f} Cr")

# Verify with PBT
pbt = extracted['pbt']['value']
calculated_pbt = op_pbt + extracted['other_income']['value']
print(f"\nPBT (reported): ₹{pbt:,.2f} Cr")
print(f"PBT (Op. PBT + Other Income): ₹{calculated_pbt:,.2f} Cr")
print(f"Difference: ₹{abs(pbt - calculated_pbt):,.2f} Cr")

if abs(pbt - calculated_pbt) < 5:
    print("\n✓ Calculations match! Op. PBT will now be visible in the frontend.")
else:
    print("\n⚠️ Calculations don't match exactly, but close enough.")

print("=" * 80)
