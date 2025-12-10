# Moneycontrol Quarterly Financial Data Scraper
# Extracts quarterly financial indicators from Moneycontrol portal

import re
import requests
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from config.logging_config import get_logger

logger = get_logger('moneycontrol_scraper')

class MoneycontrolScraper:
    """Scrape quarterly financial data from Moneycontrol portal"""
    
    # Moneycontrol URL pattern for quarterly results
    BASE_URL_PATTERN = "https://www.moneycontrol.com/markets/financials/quarterly-results/{company_slug}-w/#w"
    
    # Financial indicators to extract
    INDICATORS = {
        'total_income': ['Total Income', 'Total Revenue', 'Revenue from Operations'],
        'ebitda': ['EBITDA', 'Operating EBITDA'],
        'ebit': ['EBIT', 'Operating EBIT'],
        'pbt': ['PBT', 'Profit Before Tax'],
        'pat': ['PAT', 'Profit After Tax', 'Net Profit'],
        'employee_cost': ['Employee Cost', 'Personnel Cost', 'Staff Cost'],
        'other_expenses': ['Other Expenses', 'Operating Expenses'],
        'depreciation': ['Depreciation', 'D&A', 'Depreciation & Amortization'],
        'interest': ['Interest', 'Finance Cost', 'Interest Expense'],
        'other_income': ['Other Income', 'Non-Operating Income'],
        'tax': ['Tax', 'Income Tax', 'Taxation'],
        'ebitda_margin': ['EBITDA Margin', 'Operating Margin'],
        'ebit_margin': ['EBIT Margin'],
        'profit_margin': ['Profit Margin', 'Net Margin'],
    }
    
    def __init__(self, timeout: int = 10):
        """
        Initialize scraper
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_company_url(self, company_name: str) -> str:
        """
        Generate Moneycontrol URL for company
        
        Args:
            company_name: Company name (e.g., 'Wipro', 'TCS')
            
        Returns:
            Full URL for company's quarterly results page
        """
        # Convert company name to slug format (lowercase, hyphens)
        slug = company_name.lower().replace(' ', '-')
        return self.BASE_URL_PATTERN.format(company_slug=slug)
    
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from URL
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None on failure
        """
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def parse_quarterly_table(self, html: str, company: str) -> Dict[str, Dict]:
        """
        Parse quarterly financial data from HTML
        
        Args:
            html: HTML content
            company: Company name
            
        Returns:
            Dictionary mapping quarter to financial data
        """
        soup = BeautifulSoup(html, 'html.parser')
        quarterly_data = {}
        
        try:
            # Find all tables on the page
            tables = soup.find_all('table')
            logger.info(f"Found {len(tables)} tables on page")
            
            if not tables:
                logger.warning("No tables found on page")
                return quarterly_data
            
            # Process each table
            for table_idx, table in enumerate(tables):
                table_data = self._extract_table_data(table)
                if table_data:
                    quarterly_data.update(table_data)
            
            logger.info(f"Extracted data for {len(quarterly_data)} quarters")
            return quarterly_data
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return quarterly_data
    
    def _extract_table_data(self, table) -> Dict[str, Dict]:
        """
        Extract financial data from a single table
        
        Args:
            table: BeautifulSoup table element
            
        Returns:
            Dictionary of extracted quarterly data
        """
        quarterly_data = {}
        
        try:
            rows = table.find_all('tr')
            if not rows or len(rows) < 2:
                return quarterly_data
            
            # Get header row to identify quarters
            header_row = rows[0]
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            if not headers:
                return quarterly_data
            
            # Identify quarter columns (look for Q1, Q2, Q3, Q4, FY patterns)
            quarter_cols = {}
            for idx, header in enumerate(headers):
                header_lower = header.lower()
                # Match patterns like "Q1 FY25", "Q2 2024", "FY25", etc.
                quarter_match = re.search(r'(q[1-4]|fy)\s*(?:fy)?(\d{2,4})?', header_lower)
                if quarter_match:
                    quarter = quarter_match.group(1).upper()
                    year_str = quarter_match.group(2)
                    
                    # Try to extract year
                    year = None
                    if year_str:
                        if len(year_str) == 2:
                            # Convert 25 to 2025, 24 to 2024
                            year = 2000 + int(year_str)
                        else:
                            year = int(year_str)
                    
                    quarter_cols[idx] = {'quarter': quarter, 'year': year, 'header': header}
            
            if not quarter_cols:
                logger.debug(f"No quarter columns found in table with headers: {headers}")
                return quarterly_data
            
            logger.debug(f"Found quarter columns: {quarter_cols}")
            
            # Extract data rows
            for row_idx, row in enumerate(rows[1:], 1):
                cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if not cells:
                    continue
                
                # Get indicator name from first column
                indicator_name = cells[0].lower() if cells else ''
                
                # Skip empty rows
                if not indicator_name or indicator_name.strip() == '':
                    continue
                
                # Match against known indicators
                matched_indicator = self._match_indicator(indicator_name)
                
                if matched_indicator:
                    # Extract values for each quarter
                    for col_idx, quarter_info in quarter_cols.items():
                        if col_idx < len(cells):
                            value = self._parse_value(cells[col_idx])
                            if value is not None:
                                quarter_key = quarter_info['quarter']
                                if quarter_key not in quarterly_data:
                                    quarterly_data[quarter_key] = {}
                                
                                quarterly_data[quarter_key][matched_indicator] = {
                                    'value': value,
                                    'confidence': 0.9,
                                    'raw_text': cells[col_idx]
                                }
            
            return quarterly_data
            
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            return quarterly_data
    
    def _match_indicator(self, text: str) -> Optional[str]:
        """
        Match text to known financial indicator
        
        Args:
            text: Text to match
            
        Returns:
            Indicator key or None
        """
        text_lower = text.lower().strip()
        
        for indicator_key, aliases in self.INDICATORS.items():
            for alias in aliases:
                if alias.lower() in text_lower or text_lower in alias.lower():
                    return indicator_key
        
        return None
    
    def _parse_value(self, text: str) -> Optional[float]:
        """
        Parse numerical value from text
        
        Args:
            text: Text containing number
            
        Returns:
            Parsed float value or None
        """
        if not text or text.strip() == '-' or text.strip() == 'N/A':
            return None
        
        try:
            # Remove common text patterns
            cleaned = text.replace('₹', '').replace('Rs', '').replace('INR', '').strip()
            
            # Extract number with optional decimal
            match = re.search(r'([\d,]+\.?\d*)', cleaned)
            if match:
                num_str = match.group(1).replace(',', '')
                value = float(num_str)
                
                # Handle unit suffixes (Cr, Lac, etc.)
                if 'cr' in cleaned.lower():
                    return value  # Already in crores
                elif 'lac' in cleaned.lower() or 'lakh' in cleaned.lower():
                    return value / 100  # Convert lakhs to crores
                elif '%' in cleaned:
                    return value  # Percentage value
                
                return value
        except (ValueError, AttributeError) as e:
            logger.debug(f"Could not parse value '{text}': {e}")
        
        return None
    
    def scrape_company(self, company_name: str) -> Dict[str, Dict]:
        """
        Scrape all quarterly data for a company
        
        Args:
            company_name: Company name
            
        Returns:
            Dictionary of quarterly financial data
        """
        url = self.get_company_url(company_name)
        html = self.fetch_page(url)
        
        if not html:
            logger.error(f"Failed to fetch data for {company_name}")
            return {}
        
        quarterly_data = self.parse_quarterly_table(html, company_name)
        
        if quarterly_data:
            logger.info(f"Successfully scraped {company_name}: {len(quarterly_data)} quarters")
        else:
            logger.warning(f"No quarterly data found for {company_name}")
        
        return quarterly_data
    
    def scrape_multiple_companies(self, companies: List[str]) -> Dict[str, Dict]:
        """
        Scrape data for multiple companies
        
        Args:
            companies: List of company names
            
        Returns:
            Dictionary mapping company to quarterly data
        """
        all_data = {}
        
        for company in companies:
            try:
                data = self.scrape_company(company)
                if data:
                    all_data[company] = data
            except Exception as e:
                logger.error(f"Error scraping {company}: {e}")
        
        return all_data
    
    def extract_specific_quarter(self, company_name: str, quarter: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Extract data for a specific company quarter
        
        Args:
            company_name: Company name
            quarter: Quarter (Q1, Q2, Q3, Q4)
            year: Year (optional)
            
        Returns:
            Dictionary of financial indicators or None
        """
        quarterly_data = self.scrape_company(company_name)
        
        # Find matching quarter
        quarter_upper = quarter.upper()
        if quarter_upper in quarterly_data:
            return quarterly_data[quarter_upper]
        
        logger.warning(f"Quarter {quarter} not found for {company_name}")
        return None
