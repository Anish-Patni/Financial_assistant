# Financial Data Models
# Comprehensive data models for financial indicators

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List
from datetime import datetime

@dataclass
class FinancialIndicator:
    """Individual financial metric"""
    name: str
    value: Optional[float] = None
    unit: str = "Crores"  # INR Crores
    source: Optional[str] = None
    confidence: float = 1.0  # 0-1 scale
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def is_valid(self) -> bool:
        """Check if indicator has valid data"""
        return self.value is not None and self.confidence > 0.5


@dataclass
class QuarterlyData:
    """Complete quarterly financial snapshot"""
    company: str
    quarter: str  # Q1, Q2, Q3, Q4
    year: int
    
    # Core indicators (INR Crores)
    total_income: Optional[float] = None
    purchase_traded_goods: Optional[float] = None
    stock_change: Optional[float] = None
    employee_cost: Optional[float] = None
    other_expenses: Optional[float] = None
    depreciation: Optional[float] = None
    interest: Optional[float] = None
    other_income: Optional[float] = None
    tax: Optional[float] = None
    
    # Derived metrics (calculated)
    contribution: Optional[float] = None
    op_ebitda: Optional[float] = None
    op_ebit: Optional[float] = None
    op_pbt: Optional[float] = None
    pbt: Optional[float] = None
    pat: Optional[float] = None
    
    # Margin percentages
    op_ebitda_pct: Optional[float] = None
    op_ebit_pct: Optional[float] = None
    op_pbt_pct: Optional[float] = None
    pbt_pct: Optional[float] = None
    
    # Metadata
    data_source: Optional[str] = None
    validation_status: str = "pending"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def calculate_derived_metrics(self):
        """Calculate all derived financial metrics"""
        try:
            # Contribution = Total Income - Purchase of Traded Goods - Stock Change
            if all(x is not None for x in [self.total_income, self.purchase_traded_goods, self.stock_change]):
                self.contribution = self.total_income - self.purchase_traded_goods - self.stock_change
            
            # Op. EBITDA = Contribution - Employee Cost - Other Expenses
            if all(x is not None for x in [self.contribution, self.employee_cost, self.other_expenses]):
                self.op_ebitda = self.contribution - self.employee_cost - self.other_expenses
            
            # Op. EBIT = Op. EBITDA - Depreciation
            if all(x is not None for x in [self.op_ebitda, self.depreciation]):
                self.op_ebit = self.op_ebitda - self.depreciation
            
            # Op. PBT = Op. EBIT - Interest
            if all(x is not None for x in [self.op_ebit, self.interest]):
                self.op_pbt = self.op_ebit - self.interest
            
            # PBT = Op. PBT + Other Income
            if all(x is not None for x in [self.op_pbt, self.other_income]):
                self.pbt = self.op_pbt + self.other_income
            
            # PAT = PBT - Tax
            if all(x is not None for x in [self.pbt, self.tax]):
                self.pat = self.pbt - self.tax
            
            # Calculate margin percentages
            if self.total_income and self.total_income > 0:
                if self.op_ebitda is not None:
                    self.op_ebitda_pct = (self.op_ebitda / self.total_income) * 100
                if self.op_ebit is not None:
                    self.op_ebit_pct = (self.op_ebit / self.total_income) * 100
                if self.op_pbt is not None:
                    self.op_pbt_pct = (self.op_pbt / self.total_income) * 100
                if self.pbt is not None:
                    self.pbt_pct = (self.pbt / self.total_income) * 100
                    
        except Exception as e:
            print(f"Error calculating metrics: {e}")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def completeness_score(self) -> float:
        """Calculate data completeness (0-100%)"""
        total_fields = 9  # Core indicators
        filled_fields = sum([
            self.total_income is not None,
            self.purchase_traded_goods is not None,
            self.stock_change is not None,
            self.employee_cost is not None,
            self.other_expenses is not None,
            self.depreciation is not None,
            self.interest is not None,
            self.other_income is not None,
            self.tax is not None,
        ])
        return (filled_fields / total_fields) * 100


@dataclass
class CompanyFinancials:
    """Multi-quarter financial data for a company"""
    company_name: str
    quarters: List[QuarterlyData] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def add_quarter(self, quarter_data: QuarterlyData):
        """Add quarterly data"""
        self.quarters.append(quarter_data)
    
    def get_quarter(self, quarter: str, year: int) -> Optional[QuarterlyData]:
        """Retrieve specific quarter data"""
        for q in self.quarters:
            if q.quarter == quarter and q.year == year:
                return q
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'company_name': self.company_name,
            'quarters': [q.to_dict() for q in self.quarters],
            'metadata': self.metadata
        }
    
    def average_completeness(self) -> float:
        """Average data completeness across all quarters"""
        if not self.quarters:
            return 0.0
        return sum(q.completeness_score() for q in self.quarters) / len(self.quarters)
