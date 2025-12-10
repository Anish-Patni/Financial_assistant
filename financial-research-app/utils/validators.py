# Data Validators
# Comprehensive validation rules for financial data

from typing import Dict, List, Tuple, Optional
from core.data_models import QuarterlyData
from config.logging_config import get_logger

logger = get_logger('validators')

class FinancialValidator:
    """Validation engine for financial data"""
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_range(self, value: Optional[float], field_name: str, 
                      min_val: float = 0, max_val: float = 100000) -> bool:
        """
        Validate value is within acceptable range
        
        Args:
            value: Value to validate
            field_name: Name of the field
            min_val: Minimum acceptable value
            max_val: Maximum acceptable value
            
        Returns:
            True if valid, False otherwise
        """
        if value is None:
            self.validation_warnings.append(f"{field_name} is missing")
            return False
        
        if not (min_val <= value <= max_val):
            self.validation_errors.append(
                f"{field_name} value {value} out of range [{min_val}, {max_val}]"
            )
            return False
        
        return True
    
    def validate_consistency(self, quarterly_data: QuarterlyData) -> bool:
        """
        Verify component sums match totals
        
        Args:
            quarterly_data: Quarterly financial data
            
        Returns:
            True if consistent, False otherwise
        """
        is_valid = True
        
        # Check if contribution calculation is correct
        if all(x is not None for x in [quarterly_data.total_income, 
                                       quarterly_data.purchase_traded_goods,
                                       quarterly_data.stock_change,
                                       quarterly_data.contribution]):
            expected = (quarterly_data.total_income - 
                       quarterly_data.purchase_traded_goods - 
                       quarterly_data.stock_change)
            if abs(expected - quarterly_data.contribution) > 0.01:  # Allow small rounding
                self.validation_errors.append(
                    f"Contribution calculation mismatch: expected {expected}, got {quarterly_data.contribution}"
                )
                is_valid = False
        
        # Check EBITDA calculation
        if all(x is not None for x in [quarterly_data.contribution,
                                       quarterly_data.employee_cost,
                                       quarterly_data.other_expenses,
                                       quarterly_data.op_ebitda]):
            expected = (quarterly_data.contribution - 
                       quarterly_data.employee_cost - 
                       quarterly_data.other_expenses)
            if abs(expected - quarterly_data.op_ebitda) > 0.01:
                self.validation_errors.append(
                    f"EBITDA calculation mismatch: expected {expected}, got {quarterly_data.op_ebitda}"
                )
                is_valid = False
        
        return is_valid
    
    def validate_margins(self, quarterly_data: QuarterlyData) -> bool:
        """
        Validate margin percentages are reasonable
        
        Args:
            quarterly_data: Quarterly financial data
            
        Returns:
            True if margins are reasonable
        """
        is_valid = True
        
        margins = [
            ('Op. EBITDA %', quarterly_data.op_ebitda_pct),
            ('Op. EBIT %', quarterly_data.op_ebit_pct),
            ('Op. PBT %', quarterly_data.op_pbt_pct),
            ('PBT %', quarterly_data.pbt_pct),
        ]
        
        for margin_name, margin_value in margins:
            if margin_value is not None:
                if margin_value < -50 or margin_value > 100:
                    self.validation_warnings.append(
                        f"{margin_name} is unusual: {margin_value:.2f}%"
                    )
                    is_valid = False
        
        return is_valid
    
    def validate_qoq_change(self, current: QuarterlyData, 
                           previous: Optional[QuarterlyData],
                           threshold: float = 50) -> bool:
        """
        Detect unusual quarter-over-quarter changes
        
        Args:
            current: Current quarter data
            previous: Previous quarter data
            threshold: Percentage change threshold to flag
            
        Returns:
            True if changes are within threshold
        """
        if previous is None:
            return True
        
        is_valid = True
        
        # Check revenue change
        if current.total_income and previous.total_income:
            change_pct = abs((current.total_income - previous.total_income) / 
                           previous.total_income * 100)
            if change_pct > threshold:
                self.validation_warnings.append(
                    f"Large QoQ revenue change: {change_pct:.1f}%"
                )
                is_valid = False
        
        return is_valid
    
    def validate_quarterly_data(self, quarterly_data: QuarterlyData,
                               previous_quarter: Optional[QuarterlyData] = None) -> Tuple[bool, Dict]:
        """
        Comprehensive validation of quarterly data
        
        Args:
            quarterly_data: Data to validate
            previous_quarter: Previous quarter for trend analysis
            
        Returns:
            Tuple of (is_valid, validation_report)
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        # Range validation
        self.validate_range(quarterly_data.total_income, 'Total Income')
        self.validate_range(quarterly_data.employee_cost, 'Employee Cost')
        self.validate_range(quarterly_data.other_expenses, 'Other Expenses')
        
        # Consistency checks
        self.validate_consistency(quarterly_data)
        
        # Margin validation
        self.validate_margins(quarterly_data)
        
        # Trend analysis
        if previous_quarter:
            self.validate_qoq_change(quarterly_data, previous_quarter)
        
        is_valid = len(self.validation_errors) == 0
        
        report = {
            'status': 'valid' if is_valid else 'invalid',
            'errors': self.validation_errors,
            'warnings': self.validation_warnings,
            'completeness': quarterly_data.completeness_score()
        }
        
        if is_valid:
            logger.info(f"Validation passed for {quarterly_data.company} {quarterly_data.quarter} {quarterly_data.year}")
        else:
            logger.warning(f"Validation failed: {len(self.validation_errors)} errors")
        
        return is_valid, report
