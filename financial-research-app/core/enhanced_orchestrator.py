# Enhanced Research Orchestrator
# Coordinate research with Moneycontrol as primary source

import time
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.perplexity_client import PerplexityClient
from core.data_extractor import FinancialDataExtractor
from core.moneycontrol_extractor import MoneycontrolFinancialExtractor
from core.research_storage import ResearchStorage
from core.data_models import QuarterlyData
from utils.progress_tracker import ProgressTracker
from config.logging_config import get_logger

logger = get_logger('enhanced_orchestrator')

class EnhancedResearchOrchestrator:
    """Orchestrate financial research with Moneycontrol primary source"""
    
    # 13 target IT service companies
    DEFAULT_COMPANIES = [
        'TCS', 'Persistent Systems', 'Tech Mahindra', 'Cyient',
        'Infosys', 'LTIMindtree', 'Wipro', 'LT Technology Services',
        'Coforge', 'MPHASIS', 'Zensar', 'Hexaware', 'Birlasoft'
    ]
    
    def __init__(self, perplexity_client: Optional[PerplexityClient] = None,
                 storage: Optional[ResearchStorage] = None,
                 use_moneycontrol: bool = True):
        """
        Initialize enhanced research orchestrator
        
        Args:
            perplexity_client: Optional Perplexity API client for fallback
            storage: Research storage instance
            use_moneycontrol: Use Moneycontrol as primary source
        """
        self.perplexity_client = perplexity_client
        self.storage = storage
        self.use_moneycontrol = use_moneycontrol
        
        # Initialize extractors
        if use_moneycontrol:
            self.extractor = MoneycontrolFinancialExtractor(perplexity_client)
        else:
            self.extractor = FinancialDataExtractor()
        
        self.progress_tracker = None
    
    def research_company_quarter(self, company: str, quarter: str, year: int) -> Dict:
        """
        Research single company for one quarter
        
        Args:
            company: Company name
            quarter: Quarter (Q1, Q2, Q3, Q4)
            year: Financial year
            
        Returns:
            Research results dictionary
        """
        logger.info(f"Researching {company} - {quarter} {year}")
        
        # Check if already researched
        if self.storage:
            existing = self.storage.load_research(company, quarter, year)
            if existing:
                logger.info(f"Found existing research for {company} {quarter} {year}")
                return existing
        
        # Extract financial data
        if isinstance(self.extractor, MoneycontrolFinancialExtractor):
            result = self.extractor.extract_with_fallback(company, quarter, year)
        else:
            # Fallback to Perplexity if not using Moneycontrol
            if self.perplexity_client:
                api_result = self.perplexity_client.get_company_financials(company, quarter, year)
                if api_result:
                    raw_text = api_result.get('raw_response', '')
                    result = self.extractor.extract_with_context(raw_text, company, quarter, year)
                else:
                    result = {
                        'company': company,
                        'quarter': quarter,
                        'year': year,
                        'status': 'failed',
                        'error': 'API query failed'
                    }
            else:
                result = {
                    'company': company,
                    'quarter': quarter,
                    'year': year,
                    'status': 'failed',
                    'error': 'No extractor available'
                }
        
        # Prepare research data
        research_data = {
            'company': company,
            'quarter': quarter,
            'year': year,
            'status': 'success' if result.get('extracted_data') else 'partial',
            'source': result.get('source', 'Unknown'),
            'extracted_data': result.get('extracted_data', {}),
            'context_confidence': result.get('context_confidence', 0),
            'extraction_summary': self._get_summary(result)
        }
        
        # Save to storage if available
        if self.storage:
            self.storage.save_research(research_data)
        
        logger.info(f"Successfully researched {company} {quarter} {year}")
        return research_data
    
    def research_company_all_quarters(self, company: str, 
                                     quarters: List[str], 
                                     year: int) -> Dict[str, Dict]:
        """
        Research all quarters for a single company
        
        Args:
            company: Company name
            quarters: List of quarters (e.g., ['Q1', 'Q2', 'Q3', 'Q4'])
            year: Financial year
            
        Returns:
            Dictionary mapping quarter to research results
        """
        results = {}
        
        for quarter in quarters:
            try:
                result = self.research_company_quarter(company, quarter, year)
                results[quarter] = result
                
                if self.progress_tracker:
                    if result.get('extracted_data'):
                        self.progress_tracker.complete_item(f"{company}_{quarter}")
                    else:
                        self.progress_tracker.fail_item(f"{company}_{quarter}", 
                                                       result.get('error', 'No data'))
                
                # Small delay to respect rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error researching {company} {quarter}: {e}")
                results[quarter] = {
                    'status': 'failed',
                    'error': str(e),
                    'extracted_data': {}
                }
                if self.progress_tracker:
                    self.progress_tracker.fail_item(f"{company}_{quarter}", str(e))
        
        return results
    
    def research_all_companies(self, 
                              companies: Optional[List[str]] = None,
                              quarters: List[str] = ['Q1', 'Q2', 'Q3', 'Q4'],
                              year: int = 2024,
                              parallel: bool = False,
                              max_workers: int = 3,
                              progress_callback: Optional[Callable] = None) -> Dict:
        """
        Research all companies for specified quarters
        
        Args:
            companies: List of company names (uses default if None)
            quarters: List of quarters to research
            year: Financial year
            parallel: Whether to use parallel processing
            max_workers: Maximum parallel workers
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary mapping company to research results
        """
        if companies is None:
            companies = self.DEFAULT_COMPANIES
        
        total_items = len(companies) * len(quarters)
        self.progress_tracker = ProgressTracker(total_items)
        
        logger.info(f"Starting research for {len(companies)} companies, {len(quarters)} quarters")
        
        # Initialize all items in progress tracker
        for company in companies:
            for quarter in quarters:
                item_id = f"{company}_{quarter}"
                self.progress_tracker.start_item(item_id, f"{company} - {quarter} {year}")
        
        all_results = {}
        
        if parallel:
            all_results = self._research_parallel(companies, quarters, year, max_workers)
        else:
            all_results = self._research_sequential(companies, quarters, year, progress_callback)
        
        logger.info("Research complete")
        if self.progress_tracker:
            self.progress_tracker.print_progress()
        
        return all_results
    
    def _research_sequential(self, companies: List[str], quarters: List[str], 
                            year: int, progress_callback: Optional[Callable]) -> Dict:
        """Research companies sequentially"""
        results = {}
        
        for company in companies:
            logger.info(f"Processing {company}...")
            results[company] = self.research_company_all_quarters(company, quarters, year)
            
            if progress_callback and self.progress_tracker:
                progress_callback(self.progress_tracker.get_summary())
            
            if self.progress_tracker:
                self.progress_tracker.print_progress()
        
        return results
    
    def _research_parallel(self, companies: List[str], quarters: List[str],
                          year: int, max_workers: int) -> Dict:
        """Research companies in parallel"""
        results = {}
        
        def research_task(company):
            return company, self.research_company_all_quarters(company, quarters, year)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(research_task, company): company 
                      for company in companies}
            
            for future in as_completed(futures):
                try:
                    company, research_results = future.result()
                    results[company] = research_results
                    
                    if self.progress_tracker:
                        self.progress_tracker.print_progress()
                        
                except Exception as e:
                    company = futures[future]
                    logger.error(f"Error processing {company}: {e}")
                    results[company] = {'status': 'failed', 'error': str(e)}
        
        return results
    
    def get_research_statistics(self) -> Dict:
        """Get comprehensive statistics on research results"""
        summary = {}
        
        if self.storage:
            summary = self.storage.get_research_summary()
        
        if self.progress_tracker:
            progress_summary = self.progress_tracker.get_summary()
            summary.update(progress_summary)
        
        return summary
    
    def export_to_quarterly_data(self, company: str, quarter: str, year: int) -> Optional[QuarterlyData]:
        """
        Convert research results to QuarterlyData model
        
        Args:
            company: Company name
            quarter: Quarter
            year: Year
            
        Returns:
            QuarterlyData instance or None
        """
        if not self.storage:
            return None
        
        research = self.storage.load_research(company, quarter, year)
        
        if not research or not research.get('extracted_data'):
            return None
        
        extracted = research.get('extracted_data', {})
        
        # Map extracted data to QuarterlyData fields
        q_data = QuarterlyData(
            company=company,
            quarter=quarter,
            year=year,
            data_source=research.get('source', 'Unknown')
        )
        
        # Map extracted indicators
        field_mapping = {
            'total_income': 'total_income',
            'employee_cost': 'employee_cost',
            'other_expenses': 'other_expenses',
            'depreciation': 'depreciation',
            'interest': 'interest',
            'other_income': 'other_income',
            'tax': 'tax',
        }
        
        for extracted_key, model_field in field_mapping.items():
            if extracted_key in extracted:
                value_data = extracted[extracted_key]
                if isinstance(value_data, dict):
                    value = value_data.get('value')
                else:
                    value = value_data
                
                if value:
                    setattr(q_data, model_field, value)
        
        # Calculate derived metrics
        q_data.calculate_derived_metrics()
        
        return q_data
    
    def _get_summary(self, result: Dict) -> str:
        """Generate summary of extraction result"""
        if isinstance(self.extractor, MoneycontrolFinancialExtractor):
            return self.extractor.get_extraction_summary(result)
        else:
            return str(result)
