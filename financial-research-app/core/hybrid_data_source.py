# Hybrid Data Source
# Primary: Perplexity AI (comprehensive multi-source research)
# Secondary: Moneycontrol (fallback direct source for Indian companies)

from typing import Dict, Optional, List
from core.perplexity_client import PerplexityClient
from core.data_extractor import FinancialDataExtractor
from parsers.moneycontrol_scraper_v2 import MoneycontrolScraperV2
from config.logging_config import get_logger

logger = get_logger('hybrid_data_source')

class HybridDataSource:
    """
    Hybrid data source that prioritizes comprehensive data:
    1. Primary: Perplexity AI (comprehensive multi-source research)
    2. Secondary: Moneycontrol (fallback direct source for Indian companies)
    """
    
    def __init__(self, perplexity_client: Optional[PerplexityClient] = None):
        """
        Initialize hybrid data source
        
        Args:
            perplexity_client: Optional Perplexity API client for fallback
        """
        self.perplexity_client = perplexity_client
        self.nlp_extractor = FinancialDataExtractor()
        self.moneycontrol_scraper = MoneycontrolScraperV2()
    
    def extract_financial_data(self, company: str, quarter: str, year: int) -> Dict:
        """
        Extract financial data with Perplexity primary, Moneycontrol fallback
        
        Args:
            company: Company name
            quarter: Quarter (Q1, Q2, Q3, Q4)
            year: Financial year
            
        Returns:
            Dictionary with extracted financial data
        """
        logger.info(f"Extracting {company} {quarter} {year} - Perplexity Primary")
        
        # Try Perplexity first (comprehensive multi-source research)
        if self.perplexity_client:
            perplexity_result = self._extract_from_perplexity(company, quarter, year)
            
            if perplexity_result and perplexity_result.get('extracted_data'):
                logger.info(f"[OK] Got data from Perplexity for {company} {quarter}")
                return perplexity_result
        
        # Fallback to Moneycontrol if Perplexity fails
        logger.info(f"Perplexity data incomplete, trying Moneycontrol fallback...")
        moneycontrol_result = self._extract_from_moneycontrol(company, quarter, year)
        
        if moneycontrol_result and moneycontrol_result.get('extracted_data'):
            logger.info(f"[OK] Got data from Moneycontrol (fallback) for {company} {quarter}")
            # Mark that this is fallback data
            moneycontrol_result['is_fallback'] = True
            moneycontrol_result['primary_source_failed'] = 'Perplexity'
            # Include display message for frontend
            moneycontrol_result['fallback_message'] = f"Using Moneycontrol data (Perplexity unavailable)"
            return moneycontrol_result
        
        # Return empty result if both fail
        logger.warning(f"[FAIL] No data available from Perplexity or Moneycontrol for {company} {quarter}")
        return {
            'company': company,
            'quarter': quarter,
            'year': year,
            'source': 'None',
            'extracted_data': {},
            'context_confidence': 0.0,
            'error': 'No data available from any source'
        }
    
    def _extract_from_perplexity(self, company: str, quarter: str, year: int) -> Optional[Dict]:
        """
        Extract financial data from Perplexity AI
        
        Args:
            company: Company name
            quarter: Quarter (Q1, Q2, Q3, Q4)
            year: Financial year
            
        Returns:
            Extracted data dictionary or None
        """
        try:
            logger.debug(f"Querying Perplexity for {company} {quarter} {year}")
            
            # Get data from Perplexity
            result = self.perplexity_client.get_company_financials(company, quarter, year)
            
            if not result:
                logger.warning(f"Perplexity returned no data for {company}")
                return None
            
            raw_text = result.get('raw_response', '')
            
            # Extract indicators using NLP
            extracted = self.nlp_extractor.extract_with_context(raw_text, company, quarter, year)
            
            return {
                'company': company,
                'quarter': quarter,
                'year': year,
                'source': 'Perplexity AI',
                'extracted_data': extracted['extracted_data'],
                'context_confidence': extracted['context_confidence'],
                'raw_response': raw_text
            }
            
        except Exception as e:
            logger.error(f"Perplexity extraction failed: {e}")
            return None
    
    def _extract_from_moneycontrol(self, company: str, quarter: str, year: int) -> Optional[Dict]:
        """
        Extract financial data from Moneycontrol
        
        Args:
            company: Company name
            quarter: Quarter (Q1, Q2, Q3, Q4)
            year: Financial year
            
        Returns:
            Extracted data dictionary or None
        """
        try:
            logger.debug(f"Scraping Moneycontrol for {company} {quarter} {year}")
            
            # Scrape Moneycontrol
            quarterly_data = self.moneycontrol_scraper.extract_specific_quarter(company, quarter, year)
            
            if not quarterly_data:
                logger.warning(f"Moneycontrol returned no data for {company}")
                return None
            
            return {
                'company': company,
                'quarter': quarter,
                'year': year,
                'source': 'Moneycontrol',
                'extracted_data': quarterly_data,
                'context_confidence': 0.95
            }
            
        except Exception as e:
            logger.error(f"Moneycontrol extraction failed: {e}")
            return None
    
    def extract_multiple_companies(self, companies: List[str], quarters: List[str], year: int) -> Dict[str, Dict]:
        """
        Extract data for multiple companies
        
        Args:
            companies: List of company names
            quarters: List of quarters
            year: Financial year
            
        Returns:
            Dictionary mapping company to quarterly data
        """
        all_results = {}
        
        for company in companies:
            logger.info(f"Processing {company}...")
            company_data = {}
            
            for quarter in quarters:
                try:
                    result = self.extract_financial_data(company, quarter, year)
                    company_data[quarter] = result
                except Exception as e:
                    logger.error(f"Error extracting {company} {quarter}: {e}")
                    company_data[quarter] = {
                        'company': company,
                        'quarter': quarter,
                        'year': year,
                        'error': str(e),
                        'extracted_data': {}
                    }
            
            all_results[company] = company_data
        
        return all_results
    
    def get_data_summary(self, result: Dict) -> str:
        """Generate summary of extraction result"""
        summary_lines = []
        summary_lines.append(f"Company: {result.get('company', 'N/A')}")
        summary_lines.append(f"Period: {result.get('quarter', 'N/A')} {result.get('year', 'N/A')}")
        summary_lines.append(f"Source: {result.get('source', 'Unknown')}")
        summary_lines.append(f"Confidence: {result.get('context_confidence', 0):.2f}")
        summary_lines.append("\nExtracted Indicators:")
        
        data = result.get('extracted_data', {})
        if not data:
            summary_lines.append("  No data extracted")
        else:
            for indicator, values in data.items():
                if isinstance(values, dict) and 'value' in values:
                    value = values['value']
                    confidence = values.get('confidence', 0)
                    summary_lines.append(f"  {indicator}: ₹{value:.2f} Cr (conf: {confidence:.2f})")
                else:
                    summary_lines.append(f"  {indicator}: {values}")
        
        return '\n'.join(summary_lines)
    
    def get_available_companies(self) -> List[str]:
        """Get list of available companies"""
        return self.moneycontrol_scraper.get_available_companies()
    
    def add_company(self, name: str, slug: str, code: str, 
                   sector: str = 'computers-software') -> bool:
        """
        Add a new company
        
        Args:
            name: Company display name
            slug: Moneycontrol URL slug
            code: Moneycontrol company code
            sector: Company sector
            
        Returns:
            True if added successfully
        """
        return self.moneycontrol_scraper.add_company(name, slug, code, sector)
    
    def remove_company(self, name: str) -> bool:
        """Remove a company"""
        return self.moneycontrol_scraper.remove_company(name)
