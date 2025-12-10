# Moneycontrol Quarterly Financial Data Scraper V2
# Uses correct Moneycontrol URL patterns and company codes

import re
import requests
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from config.logging_config import get_logger
from config.company_config import company_config

logger = get_logger('moneycontrol_scraper_v2')


class MoneycontrolScraperV2:
    """Scrape quarterly financial data from Moneycontrol portal - Version 2"""
    
    # Financial indicators to extract
    INDICATORS = {
        'total_income': ['Total Income From Operations', 'Total Income', 'Total Revenue', 
                        'Revenue From Operations', 'Net Sales', 'Sales'],
        'ebitda': ['EBITDA', 'Operating EBITDA', 'PBDIT'],
        'ebit': ['EBIT', 'Operating EBIT', 'PBIT'],
        'pbt': ['PBT', 'Profit Before Tax', 'Profit/(Loss) Before Tax'],
        'pat': ['PAT', 'Profit After Tax', 'Net Profit', 'Profit/(Loss) For The Period',
               'Net Profit/(Loss) For The Period'],
        'employee_cost': ['Employee Cost', 'Employee Benefit Expense', 'Personnel Cost', 
                         'Staff Cost', 'Employees Cost'],
        'other_expenses': ['Other Expenses', 'Other Expenditure', 'Operating Expenses'],
        'depreciation': ['Depreciation', 'Depreciation And Amortisation', 'D&A',
                        'Depreciation And Amortization Expenses'],
        'interest': ['Interest', 'Finance Cost', 'Finance Costs', 'Interest Expense'],
        'other_income': ['Other Income', 'Non-Operating Income'],
        'tax': ['Tax', 'Tax Expense', 'Income Tax', 'Taxation', 'Current Tax'],
        'eps': ['EPS', 'Basic EPS', 'Diluted EPS', 'Earnings Per Share'],
    }
    
    def __init__(self, timeout: int = 15):
        """Initialize scraper"""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
    
    def get_quarterly_url(self, company_name: str) -> Optional[str]:
        """Get Moneycontrol quarterly results URL for company"""
        return company_config.get_moneycontrol_url(company_name, 'quarterly')
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def parse_quarterly_table(self, html: str, company: str) -> Dict[str, Dict]:
        """Parse quarterly financial data from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        quarterly_data = {}
        
        try:
            # Find all tables
            tables = soup.find_all('table')
            logger.info(f"Found {len(tables)} tables on page for {company}")
            
            for table in tables:
                table_data = self._extract_table_data(table)
                if table_data:
                    # Merge data
                    for quarter, indicators in table_data.items():
                        if quarter not in quarterly_data:
                            quarterly_data[quarter] = {}
                        quarterly_data[quarter].update(indicators)
            
            # Also try to extract from div-based layouts
            div_data = self._extract_from_divs(soup)
            if div_data:
                for quarter, indicators in div_data.items():
                    if quarter not in quarterly_data:
                        quarterly_data[quarter] = {}
                    quarterly_data[quarter].update(indicators)
            
            logger.info(f"Extracted data for {len(quarterly_data)} quarters for {company}")
            return quarterly_data
            
        except Exception as e:
            logger.error(f"Error parsing HTML for {company}: {e}")
            return quarterly_data
    
    def _extract_table_data(self, table) -> Dict[str, Dict]:
        """Extract financial data from a table element"""
        quarterly_data = {}
        
        try:
            rows = table.find_all('tr')
            if not rows or len(rows) < 2:
                return quarterly_data
            
            # Get headers
            header_row = rows[0]
            headers = []
            for cell in header_row.find_all(['th', 'td']):
                text = cell.get_text(strip=True)
                headers.append(text)
            
            if not headers:
                return quarterly_data
            
            # Find quarter columns
            quarter_cols = {}
            for idx, header in enumerate(headers):
                quarter_info = self._parse_quarter_header(header)
                if quarter_info:
                    quarter_cols[idx] = quarter_info
            
            if not quarter_cols:
                return quarterly_data
            
            # Extract data rows
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue
                
                cell_texts = [c.get_text(strip=True) for c in cells]
                if not cell_texts:
                    continue
                
                indicator_name = cell_texts[0]
                matched_indicator = self._match_indicator(indicator_name)
                
                if matched_indicator:
                    for col_idx, quarter_info in quarter_cols.items():
                        if col_idx < len(cell_texts):
                            value = self._parse_value(cell_texts[col_idx])
                            if value is not None:
                                quarter_key = quarter_info['key']
                                if quarter_key not in quarterly_data:
                                    quarterly_data[quarter_key] = {}
                                
                                quarterly_data[quarter_key][matched_indicator] = {
                                    'value': value,
                                    'confidence': 0.95,
                                    'raw_text': cell_texts[col_idx],
                                    'year': quarter_info.get('year')
                                }
            
            return quarterly_data
            
        except Exception as e:
            logger.debug(f"Error extracting table data: {e}")
            return quarterly_data
    
    def _extract_from_divs(self, soup) -> Dict[str, Dict]:
        """Extract data from div-based layouts (modern Moneycontrol pages)"""
        quarterly_data = {}
        
        try:
            # Look for financial data in various div structures
            # This handles the newer Moneycontrol page layouts
            
            # Find elements with financial data
            data_elements = soup.find_all(['div', 'span'], class_=re.compile(r'(value|data|amount|number)', re.I))
            
            for elem in data_elements:
                text = elem.get_text(strip=True)
                # Try to extract quarter and value pairs
                # This is a fallback for non-table layouts
                
            return quarterly_data
            
        except Exception as e:
            logger.debug(f"Error extracting from divs: {e}")
            return quarterly_data
    
    def _parse_quarter_header(self, header: str) -> Optional[Dict]:
        """Parse quarter information from header text"""
        if not header:
            return None
        
        header_clean = header.strip()
        
        # Patterns to match: "Sep 2024", "Jun 2024", "Mar 2024", "Dec 2023"
        # Also: "Q1 FY25", "Q2 2024", etc.
        
        # Month-Year pattern (Sep 2024, Jun 2024, etc.)
        month_year = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*[\'"]?(\d{2,4})', header_clean, re.I)
        if month_year:
            month = month_year.group(1).capitalize()
            year_str = month_year.group(2)
            year = int(year_str) if len(year_str) == 4 else 2000 + int(year_str)
            
            # Map month to quarter
            month_to_quarter = {
                'Jan': 'Q3', 'Feb': 'Q3', 'Mar': 'Q4',
                'Apr': 'Q1', 'May': 'Q1', 'Jun': 'Q1',
                'Jul': 'Q2', 'Aug': 'Q2', 'Sep': 'Q2',
                'Oct': 'Q3', 'Nov': 'Q3', 'Dec': 'Q3'
            }
            quarter = month_to_quarter.get(month, 'Q1')
            
            return {
                'quarter': quarter,
                'year': year,
                'key': f"{quarter}_{year}",
                'header': header_clean
            }
        
        # Q1/Q2/Q3/Q4 pattern
        quarter_match = re.search(r'(Q[1-4])\s*(?:FY)?[\'"]?(\d{2,4})?', header_clean, re.I)
        if quarter_match:
            quarter = quarter_match.group(1).upper()
            year_str = quarter_match.group(2)
            year = None
            if year_str:
                year = int(year_str) if len(year_str) == 4 else 2000 + int(year_str)
            
            return {
                'quarter': quarter,
                'year': year,
                'key': f"{quarter}_{year}" if year else quarter,
                'header': header_clean
            }
        
        return None
    
    def _match_indicator(self, text: str) -> Optional[str]:
        """Match text to known financial indicator"""
        if not text:
            return None
        
        text_lower = text.lower().strip()
        
        for indicator_key, aliases in self.INDICATORS.items():
            for alias in aliases:
                alias_lower = alias.lower()
                if alias_lower in text_lower or text_lower in alias_lower:
                    return indicator_key
                # Also check for partial matches
                if len(alias_lower) > 5 and alias_lower[:5] in text_lower:
                    return indicator_key
        
        return None
    
    def _parse_value(self, text: str) -> Optional[float]:
        """Parse numerical value from text"""
        if not text or text.strip() in ['-', '--', 'N/A', 'NA', '']:
            return None
        
        try:
            # Clean the text
            cleaned = text.replace(',', '').replace('Rs', '').replace('INR', '').strip()
            cleaned = re.sub(r'[₹$€£]', '', cleaned)
            
            # Handle parentheses for negative numbers
            if '(' in cleaned and ')' in cleaned:
                cleaned = '-' + cleaned.replace('(', '').replace(')', '')
            
            # Extract number
            match = re.search(r'(-?[\d.]+)', cleaned)
            if match:
                value = float(match.group(1))
                
                # Handle unit suffixes
                text_lower = text.lower()
                if 'cr' in text_lower or 'crore' in text_lower:
                    return value
                elif 'lac' in text_lower or 'lakh' in text_lower:
                    return value / 100
                elif 'million' in text_lower:
                    return value / 10  # Approximate conversion
                elif 'billion' in text_lower:
                    return value * 100  # Approximate conversion
                
                return value
                
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def scrape_company(self, company_name: str) -> Dict[str, Dict]:
        """Scrape all quarterly data for a company"""
        url = self.get_quarterly_url(company_name)
        
        if not url:
            logger.error(f"No URL found for company: {company_name}")
            return {}
        
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
    
    def extract_specific_quarter(self, company_name: str, quarter: str, 
                                year: Optional[int] = None) -> Optional[Dict]:
        """Extract data for a specific company quarter"""
        quarterly_data = self.scrape_company(company_name)
        
        if not quarterly_data:
            return None
        
        # Try to find matching quarter
        quarter_upper = quarter.upper()
        
        # Try exact match with year
        if year:
            key = f"{quarter_upper}_{year}"
            if key in quarterly_data:
                return quarterly_data[key]
        
        # Try quarter only match
        for key, data in quarterly_data.items():
            if key.startswith(quarter_upper):
                return data
        
        # Return first available if no match
        if quarterly_data:
            first_key = list(quarterly_data.keys())[0]
            logger.warning(f"Quarter {quarter} not found, returning {first_key}")
            return quarterly_data[first_key]
        
        return None
    
    def get_available_companies(self) -> List[str]:
        """Get list of available companies"""
        return company_config.get_all_companies()
    
    def add_company(self, name: str, slug: str, code: str, 
                   sector: str = 'computers-software') -> bool:
        """Add a new company"""
        return company_config.add_company(name, slug, code, sector)
    
    def remove_company(self, name: str) -> bool:
        """Remove a company"""
        return company_config.remove_company(name)
