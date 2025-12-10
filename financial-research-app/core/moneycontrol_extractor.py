# Moneycontrol-based Financial Data Extractor
# Direct extraction from Moneycontrol portal with fallback to Perplexity

from typing import Dict, Optional, List
from parsers.moneycontrol_scraper import MoneycontrolScraper
from core.perplexity_client import PerplexityClient
from core.data_extractor import FinancialDataExtractor
from config.logging_config import get_logger

logger = get_logger('moneycontrol_extractor')

class MoneycontrolFinancialExtractor:
    """Extract financial data from Moneycontrol with Perplexity fallback"""
    
    def __init__(self, perplexity_client: Optional[PerplexityClient] = None):
        """
        Initialize extractor
        
        Args:
            perplexity_client: Optional Perplexity client for fallback
        """
        self.scraper = MoneycontrolScraper()
        self.perplexity_client = perplexity_client
        self.nlp_extractor = FinancialDataExtractor()
    
    def extract_from_moneycontrol(self, company: str, quarter: str, year: int) -> Optional[Dict]:
        """
        Extract financial data directly from Moneycontrol
        
        Args:
            company: Company name
            quarter: Quarter (Q1, Q2, Q3, Q4)
            year: Financial year
            
        Returns:
            Dictionary of extracted financial data or None
        """
        try:
            logger.info(f"Extracting from Moneycontrol: {company} {quarter} {year}")
            
            # Scrape Moneycontrol
            quarterly_data = self.scraper.extract_specific_quarter(company, quarter, year)
            
            if quarterly_data:
                logger.info(f"Successfully extracted {len(quarterly_data)} indicators from Moneycontrol")
                return {
                    'company': company,
                    'quarter': quarter,
                    'year': year,
                    'source': 'Moneycontrol',
                    'extracted_data': quarterly_data,
                    'context_confidence': 0.95
                }
            else:
                logger.warning(f"No data found on Moneycontrol for {company} {quarter}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting from Moneycontrol: {e}")
            return None
    
    def extract_with_fallback(self, company: str, quarter: str, year: int) -> Dict:
        """
        Extract financial data with Moneycontrol primary and Perplexity fallback
        
        Args:
            company: Company name
            quarter: Quarter (Q1, Q2, Q3, Q4)
            year: Financial year
            
        Returns:
            Dictionary of extracted financial data
        """
        # Try Moneycontrol first
        mc_result = self.extract_from_moneycontrol(company, quarter, year)
        
        if mc_result:
            return mc_result
        
        # Fallback to Perplexity if available
        if self.perplexity_client:
            logger.info(f"Falling back to Perplexity for {company} {quarter} {year}")
            
            try:
                result = self.perplexity_client.get_company_financials(company, quarter, year)
                
                if result:
                    raw_text = result.get('raw_response', '')
                    extracted = self.nlp_extractor.extract_with_context(raw_text, company, quarter, year)
                    
                    return {
                        'company': company,
                        'quarter': quarter,
                        'year': year,
                        'source': 'Perplexity AI',
                        'extracted_data': extracted['extracted_data'],
                        'context_confidence': extracted['context_confidence']
                    }
            except Exception as e:
                logger.error(f"Perplexity fallback failed: {e}")
        
        # Return empty result if both sources fail
        return {
            'company': company,
            'quarter': quarter,
            'year': year,
            'source': 'None',
            'extracted_data': {},
            'context_confidence': 0.0,
            'error': 'No data available from Moneycontrol or Perplexity'
        }
    
    def extract_all_quarters(self, company: str, quarters: List[str], year: int) -> Dict[str, Dict]:
        """
        Extract data for all quarters of a company
        
        Args:
            company: Company name
            quarters: List of quarters (Q1, Q2, Q3, Q4)
            year: Financial year
            
        Returns:
            Dictionary mapping quarter to extracted data
        """
        results = {}
        
        for quarter in quarters:
            try:
                result = self.extract_with_fallback(company, quarter, year)
                results[quarter] = result
            except Exception as e:
                logger.error(f"Error extracting {company} {quarter}: {e}")
                results[quarter] = {
                    'company': company,
                    'quarter': quarter,
                    'year': year,
                    'error': str(e),
                    'extracted_data': {}
                }
        
        return results
    
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
            try:
                logger.info(f"Processing {company}...")
                company_data = self.extract_all_quarters(company, quarters, year)
                all_results[company] = company_data
            except Exception as e:
                logger.error(f"Error processing {company}: {e}")
                all_results[company] = {'error': str(e)}
        
        return all_results
    
    def get_extraction_summary(self, extracted_data: Dict) -> str:
        """Generate human-readable summary of extraction"""
        summary_lines = []
        summary_lines.append(f"Company: {extracted_data.get('company', 'N/A')}")
        summary_lines.append(f"Period: {extracted_data.get('quarter', 'N/A')} {extracted_data.get('year', 'N/A')}")
        summary_lines.append(f"Source: {extracted_data.get('source', 'Unknown')}")
        summary_lines.append(f"Confidence: {extracted_data.get('context_confidence', 0):.2f}")
        summary_lines.append("\nExtracted Indicators:")
        
        data = extracted_data.get('extracted_data', {})
        if not data:
            summary_lines.append("  No data extracted")
        else:
            for indicator, values in data.items():
                if isinstance(values, dict) and 'value' in values:
                    summary_lines.append(f"  {indicator}: ₹{values['value']:.2f} Cr (conf: {values.get('confidence', 0):.2f})")
                else:
                    summary_lines.append(f"  {indicator}: {values}")
        
        return '\n'.join(summary_lines)
