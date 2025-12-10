#!/usr/bin/env python3
"""
Data Extraction Validator
Validates extracted financial data for common issues and inconsistencies
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.logging_config import get_logger

logger = get_logger('extraction_validator')

class ExtractionValidator:
    """Validates financial data extraction results"""
    
    def __init__(self):
        self.validation_rules = [
            self._validate_pbt_not_total_income,
            self._validate_pat_not_percentage,
            self._validate_reasonable_ranges,
            self._validate_profit_hierarchy,
            self._validate_missing_critical_fields
        ]
    
    def _validate_pbt_not_total_income(self, data: Dict) -> Tuple[bool, str]:
        """Check if PBT incorrectly equals total income"""
        if 'pbt' not in data or 'total_income' not in data:
            return True, ""
        
        pbt = data['pbt']['value']
        income = data['total_income']['value']
        
        if abs(pbt - income) < 1.0:
            return False, f"PBT ({pbt}) equals Total Income ({income}) - likely extraction error"
        
        return True, ""
    
    def _validate_pat_not_percentage(self, data: Dict) -> Tuple[bool, str]:
        """Check if PAT is actually a percentage value"""
        if 'pat' not in data or 'total_income' not in data:
            return True, ""
        
        pat = data['pat']['value']
        income = data['total_income']['value']
        
        # PAT < 100 and income > 10000 suggests PAT is a percentage
        if pat < 100 and income > 10000:
            return False, f"PAT ({pat}) appears to be a percentage, not absolute value (Income: {income})"
        
        return True, ""
    
    def _validate_reasonable_ranges(self, data: Dict) -> Tuple[bool, str]:
        """Check if values are in reasonable ranges"""
        issues = []
        
        # Check for negative profits (can be valid but worth flagging)
        for field in ['ebitda', 'ebit', 'pbt', 'pat']:
            if field in data and data[field]['value'] < 0:
                issues.append(f"{field.upper()} is negative ({data[field]['value']})")
        
        # Check for unreasonably high margins
        if 'ebitda' in data and 'total_income' in data:
            margin = (data['ebitda']['value'] / data['total_income']['value']) * 100
            if margin > 50:
                issues.append(f"EBITDA margin ({margin:.1f}%) seems unreasonably high")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, ""
    
    def _validate_profit_hierarchy(self, data: Dict) -> Tuple[bool, str]:
        """Check if profit metrics follow expected hierarchy: EBITDA > EBIT > PBT > PAT"""
        # Check EBITDA > EBIT
        if 'ebitda' in data and 'ebit' in data:
            if data['ebitda']['value'] < data['ebit']['value']:
                return False, f"EBITDA ({data['ebitda']['value']}) < EBIT ({data['ebit']['value']}) - incorrect hierarchy"
        
        # Check EBIT > PBT (usually, unless there's significant other income)
        if 'ebit' in data and 'pbt' in data:
            # PBT can be higher than EBIT if other income is large, so only flag if much higher
            if data['pbt']['value'] > data['ebit']['value'] * 1.5:
                return False, f"PBT ({data['pbt']['value']}) >> EBIT ({data['ebit']['value']}) - verify other income"
        
        # Check PBT > PAT (always true unless negative)
        if 'pbt' in data and 'pat' in data:
            if data['pbt']['value'] > 0 and data['pat']['value'] > data['pbt']['value']:
                return False, f"PAT ({data['pat']['value']}) > PBT ({data['pbt']['value']}) - impossible"
        
        return True, ""
    
    def _validate_missing_critical_fields(self, data: Dict) -> Tuple[bool, str]:
        """Check for missing critical fields needed for Op. PBT calculation"""
        critical_fields = ['ebit', 'interest', 'other_income']
        missing = [f for f in critical_fields if f not in data]
        
        if missing:
            return False, f"Missing critical fields for Op. PBT calculation: {', '.join(missing)}"
        
        return True, ""
    
    def validate(self, extracted_data: Dict, company: str = "", quarter: str = "", year: int = 0) -> Dict:
        """
        Validate extracted financial data
        
        Args:
            extracted_data: Dictionary of extracted indicators
            company: Company name (for logging)
            quarter: Quarter (for logging)
            year: Year (for logging)
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'company': company,
            'quarter': quarter,
            'year': year
        }
        
        # Run all validation rules
        for rule in self.validation_rules:
            is_valid, message = rule(extracted_data)
            if not is_valid:
                if "Missing critical fields" in message or "impossible" in message:
                    results['errors'].append(message)
                    results['valid'] = False
                else:
                    results['warnings'].append(message)
        
        # Log results
        if results['errors']:
            logger.error(f"Validation failed for {company} {quarter} {year}: {'; '.join(results['errors'])}")
        elif results['warnings']:
            logger.warning(f"Validation warnings for {company} {quarter} {year}: {'; '.join(results['warnings'])}")
        else:
            logger.info(f"Validation passed for {company} {quarter} {year}")
        
        return results
    
    def get_summary(self, validation_result: Dict) -> str:
        """Generate human-readable validation summary"""
        lines = []
        lines.append(f"Validation for {validation_result['company']} {validation_result['quarter']} {validation_result['year']}")
        lines.append(f"Status: {'✓ PASS' if validation_result['valid'] else '✗ FAIL'}")
        
        if validation_result['errors']:
            lines.append("\nErrors:")
            for err in validation_result['errors']:
                lines.append(f"  ✗ {err}")
        
        if validation_result['warnings']:
            lines.append("\nWarnings:")
            for warn in validation_result['warnings']:
                lines.append(f"  ⚠ {warn}")
        
        return '\n'.join(lines)
