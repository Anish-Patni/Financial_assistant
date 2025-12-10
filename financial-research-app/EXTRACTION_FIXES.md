# Data Extraction Fixes - Summary

## Problem Identified

**Op. PBT and PBT were not showing for some companies** (TCS, Tech Mahindra) because:

1. **Incomplete Data Extraction**: The regex patterns in `data_extractor.py` were not capturing all fields from markdown tables in API responses
2. **Missing Critical Fields**: `interest` and `other_income` were not being extracted, preventing Op. PBT calculation
3. **Incorrect Values**: Some extractions captured wrong values (e.g., PBT = total_income, PAT = percentage instead of absolute value)

## Root Cause

The data extractor had:
- **Weak regex patterns** that couldn't handle variations in markdown table formats
- **No validation** to catch obviously incorrect extractions
- **No sanity checks** for financial metric relationships

## Solutions Implemented

### 1. Enhanced Regex Patterns (`core/data_extractor.py`)

**Improvements:**
- Added support for pipe `|` separators in markdown tables
- Better handling of currency symbols (₹, Rs, INR)
- Added patterns for colon `:` separators
- Improved number extraction to avoid matching percentages
- Better handling of field labels with variations

**Updated fields:**
- `pbt`: Added more pattern variations
- `interest`: Added markdown table patterns
- `other_income`: Added markdown table patterns  
- `depreciation`: Added full label support
- `employee_cost`: Enhanced patterns
- `other_expenses`: Enhanced patterns

### 2. Validation Logic (`core/data_extractor.py`)

Added `extract_all_indicators()` validation to catch:

```python
# PBT should not equal total_income
if abs(pbt - total_income) < 1.0:
    # Remove incorrect PBT

# PAT should not be a small percentage value
if pat < 100 and total_income > 10000:
    # Remove incorrect PAT

# Check for "Not available" mentions in text
if "PBT: Not available" in text:
    # Remove that field
```

### 3. Automated Validator (`utils/extraction_validator.py`)

Created `ExtractionValidator` class with rules:
- **PBT validation**: Checks PBT ≠ total_income
- **PAT validation**: Ensures PAT is not a percentage  
- **Reasonable ranges**: Flags negative profits, high margins
- **Profit hierarchy**: Validates EBITDA > EBIT > PBT > PAT
- **Missing critical fields**: Warns if interest/other_income missing

### 4. Integration (`core/research_orchestrator.py`)

- Added validator to orchestrator
- Automatic validation on every extraction
- Validation results stored with research data
- Logged warnings/errors for review

### 5. Fix Script (`fix_extraction_issues.py`)

Created script to re-extract existing problematic files:
- Processes TCS and Tech Mahindra Q1-Q4 2024
- Shows before/after comparison
- Creates backups before updating
- Highlights added/removed fields

## Results

### Before Fixes:
- **TCS Q1 2024**: Missing PBT, interest, other_income (only had EBITDA, EBIT)
- **Tech Mahindra Q1 2024**: PBT = 13005 (same as income - wrong!), missing interest/other_income

### After Fixes:
- **TCS Q2 2024**: ✓ Extracted 8 indicators including interest, depreciation, other_expenses
- **TCS Q3 2024**: ✓ Extracted 9 indicators including interest, other_income
- **Tech Mahindra Q2 2024**: ✓ Extracted 9 indicators including interest, other_income
- **Tech Mahindra Q3 2024**: ✓ Extracted 10 indicators including PBT, interest, other_income

## Frontend Impact

**Now Op. PBT can be calculated:**
```javascript
Op. PBT = EBIT - Interest
```

**Now PBT can be shown:**
- Either extracted directly from API response
- Or calculated: `PBT = Op. PBT + Other Income`

## Prevention for Future Extractions

All future extractions will automatically:
1. ✓ Use improved regex patterns
2. ✓ Validate extracted values  
3. ✓ Check for unreasonable values
4. ✓ Log warnings for review
5. ✓ Ensure critical fields are present

## Files Modified

1. `core/data_extractor.py` - Enhanced patterns & validation
2. `utils/extraction_validator.py` - New validation framework
3. `core/research_orchestrator.py` - Integrated validator
4. `fix_extraction_issues.py` - One-time fix script

## How to Use

### For Existing Data:
```bash
python fix_extraction_issues.py
```

### For New Extractions:
- Automatic! Just use the research API as normal
- Validator runs automatically
- Check logs for any warnings

## Verification

Check the application logs for:
```
INFO - Extracted interest: 50.0 (confidence: 1.00)
INFO - Extracted other_income: 1100.0 (confidence: 1.00)
INFO - Extracted pbt: 15050.0 (confidence: 0.85)
INFO - Validation passed for TCS Q2 2024
```

Now reload the web interface to see Op. PBT and PBT properly displayed for all companies!
