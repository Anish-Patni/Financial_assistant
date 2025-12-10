# Perplexity API Client
# Complete API wrapper with rate limiting, retry logic, and caching

import time
import requests
from typing import Dict, Optional, List
from collections import deque
from config.logging_config import get_logger
from core.cache_manager import CacheManager

logger = get_logger('perplexity')

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = deque()
        
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove requests older than 1 minute
        while self.requests and now - self.requests[0] > 60:
            self.requests.popleft()
        
        # If at limit, wait
        if len(self.requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.requests[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self.wait_if_needed()  # Recursive call after waiting
        
        self.requests.append(now)


class PerplexityClient:
    """Perplexity API client with enterprise features"""
    
    def __init__(self, api_key: str, rate_limit_rpm: int = 20, 
                 cache_manager: Optional[CacheManager] = None,
                 use_finance_domain: bool = False,
                 model: str = 'llama-3.1-sonar-large-128k-online'):
        """
        Initialize Perplexity client
        
        Args:
            api_key: Perplexity API key
            rate_limit_rpm: Requests per minute limit
            cache_manager: Optional cache manager instance
            use_finance_domain: Enable finance-focused domain (if available)
            model: Model to use for queries
        """
        self.api_key = api_key
        self.api_url = 'https://api.perplexity.ai/chat/completions'
        self.rate_limiter = RateLimiter(rate_limit_rpm)
        self.cache_manager = cache_manager
        self.use_finance_domain = use_finance_domain
        self.model = model
        
    def _build_financial_query(self, company: str, quarter: str, year: int, 
                               indicators: Optional[List[str]] = None) -> str:
        """
        Build optimized query for financial data extraction
        
        Args:
            company: Company name
            quarter: Quarter (Q1, Q2, Q3, Q4)
            year: Financial year
            indicators: Specific indicators to fetch
            
        Returns:
            Formatted query string
        """
        if indicators is None:
            indicators = [
                'Total Revenue/Total Income from Operations',
                'EBITDA', 'EBIT', 'PBT', 'PAT',
                'Employee Cost', 'Other Expenses',
                'Depreciation', 'Interest', 'Other Income'
            ]
        
        # Clarify fiscal year - Q3 2025 means FY 2024-25 Q3 (Oct-Dec 2024, announced Jan 2025)
        fy_context = f"FY{year-1}-{str(year)[2:]}" if year >= 2025 else f"FY{year}"
        quarter_end_month = {"Q1": "June", "Q2": "September", "Q3": "December", "Q4": "March"}
        
        query = f"""
        Search for the quarterly financial data for {company} for {quarter} {fy_context} (quarter ending {quarter_end_month.get(quarter, '')} {year-1 if quarter != 'Q4' else year}) from recent sources.
        
        Please provide the following metrics (in INR Crores):
        {chr(10).join('- ' + ind for ind in indicators)}
        
        Source: Use the most recent data from MoneyControl, Screener.in, BSE/NSE filings, or official company announcements.
        Format: Please provide exact numerical values with units.
        """
        
        return query.strip()
    
    def query(self, prompt: str, model: str = None,
              max_retries: int = 3) -> Optional[Dict]:
        """
        Query Perplexity API with retry logic
        
        Args:
            prompt: Query prompt
            model: Model to use (uses instance default if None)
            max_retries: Maximum retry attempts
            
        Returns:
            API response or None on failure
        """
        if model is None:
            model = self.model
            
        # Check cache first
        if self.cache_manager:
            cache_key = {'prompt': prompt, 'model': model}
            cached = self.cache_manager.get(cache_key)
            if cached:
                logger.info("Returning cached response")
                return cached
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Build system message with finance domain if enabled
        system_message = 'You are a financial data expert. Provide precise numerical data with sources from reliable financial databases and official filings.'
        
        if self.use_finance_domain:
            system_message += ' Focus on financial metrics, quarterly results, and company financials from sources like MoneyControl, Screener.in, BSE, NSE, and official company reports.'
        
        payload = {
            'model': model,
            'messages': [
                {
                    'role': 'system',
                    'content': system_message
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            # Force real-time search with recent data
            'search_recency_filter': 'month'
        }
        
        # Add search domain hint if finance domain is enabled
        if self.use_finance_domain:
            payload['search_domain_filter'] = ['finance']  # May not be supported by all plans
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Querying Perplexity API (attempt {attempt + 1}/{max_retries})")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Cache successful response
                    if self.cache_manager:
                        self.cache_manager.set(cache_key, result)
                    
                    logger.info("API query successful")
                    return result
                    
                elif response.status_code == 429:  # Rate limit hit
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limit hit, waiting {wait_time}s")
                    time.sleep(wait_time)
                    
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    
            except Exception as e:
                logger.error(f"Request failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def get_company_financials(self, company: str, quarter: str, year: int) -> Optional[Dict]:
        """
        Get comprehensive financial data for a company
        
        Args:
            company: Company name
            quarter: Quarter (Q1, Q2, Q3, Q4)
            year: Financial year
            
        Returns:
            Financial data dictionary or None
        """
        query = self._build_financial_query(company, quarter, year)
        response = self.query(query)
        
        if response and 'choices' in response:
            content = response['choices'][0]['message']['content']
            return {
                'company': company,
                'quarter': quarter,
                'year': year,
                'raw_response': content,
                'timestamp': time.time()
            }
        
        return None
    
    def parse_financial_response(self, response: Dict) -> Dict[str, float]:
        """
        Parse financial data from API response
        
        Args:
            response: API response dictionary
            
        Returns:
            Dictionary of indicator: value pairs
        """
        import re
        
        raw_text = response.get('raw_response', '')
        parsed_data = {}
        
        # Simple pattern matching for numbers
        # Format: "Revenue: 1,234.56" or "EBITDA: Rs. 500.00 Cr"
        patterns = [
            r'(?:Revenue|Total Income).*?(\d+(?:,\d+)*(?:\.\d+)?)',
            r'EBITDA.*?(\d+(?:,\d+)*(?:\.\d+)?)',
            r'EBIT.*?(\d+(?:,\d+)*(?:\.\d+)?)',
            r'PBT.*?(\d+(?:,\d+)*(?:\.\d+)?)',
            r'PAT.*?(\d+(?:,\d+)*(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(',', '')
                try:
                    parsed_data[pattern.split('.*')[0].strip('?:()')] = float(value_str)
                except ValueError:
                    pass
        
        logger.info(f"Parsed {len(parsed_data)} financial indicators")
        return parsed_data
