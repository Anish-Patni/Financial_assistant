# NLP Data Extractor
# Advanced extraction of financial data from natural language responses

import re
from typing import Dict, List, Optional, Tuple
from config.logging_config import get_logger

logger = get_logger('data_extractor')

class FinancialDataExtractor:
    """Extract structured financial data from natural language text using NLP patterns"""
    
    def __init__(self):
        """Initialize extractor with financial data patterns"""
        self.patterns = self._build_patterns()
        
    def _build_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Build regex patterns for financial indicators"""
        
        # Common number pattern (handles: 1,234.56 or 1234.56)
        num = r'(\d+(?:,\d+)*(?:\.\d+)?)'
        
        # Currency prefixes (optional)
        curr = r'(?:Rs\.?\s*|₹\s*|INR\s*)?'
        
        # Unit suffixes
        unit_cr = r'(?:cr\.?|crores?|crore)'
        unit_lac = r'(?:lac|lacs|lakh|lakhs)'
        
        # Markdown table patterns with variations
        # | **Label** | value | or | Label | value |
        md_table = r'\|\s*\**'
        md_val = r'\**\s*\|\s*'
        
        patterns = {
            'total_income': [
                # Markdown table format
                re.compile(rf'{md_table}(?:total revenue|revenue from operations|total income|net sales){md_val}{num}', re.IGNORECASE),
                re.compile(rf'(?:total income|revenue|total revenue|sales).*?{curr}\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'{num}\s*{unit_cr}.*?(?:total income|revenue)', re.IGNORECASE),
                re.compile(rf'(?:income|revenue).*?stood at.*?{num}\s*{unit_cr}', re.IGNORECASE),
                # Plain number after label
                re.compile(rf'(?:total revenue|revenue|sales|income).*?{num}', re.IGNORECASE),
            ],
            
            'ebitda': [
                re.compile(rf'{md_table}(?:ebitda|operating ebitda){md_val}{num}', re.IGNORECASE),
                re.compile(rf'(?:ebitda|operating ebitda).*?{curr}\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'{num}\s*{unit_cr}.*?ebitda', re.IGNORECASE),
                re.compile(rf'ebitda.*?stood at.*?{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'ebitda.*?{num}', re.IGNORECASE),
            ],
            
            'ebit': [
                re.compile(rf'\*\*(?:ebit|operating ebit)[:]*\*\*\s*:?\s*{curr}?\s*{num}', re.IGNORECASE),
                re.compile(rf'{md_table}(?:ebit|operating ebit){md_val}{num}', re.IGNORECASE),
                re.compile(rf'(?:ebit|operating ebit).*?{curr}\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'{num}\s*{unit_cr}.*?ebit(?!\w)', re.IGNORECASE),
                re.compile(rf'ebit[:\s]+.*?{num}\s*(?:crore|cr)', re.IGNORECASE),
            ],
            
            'pbt': [
                # Match "**PBT (Profit Before Tax):** ₹220.30" format without unit
                re.compile(rf'\*\*pbt\s*\(profit before tax\)[:]*\*\*\s*:?\s*{curr}?\s*{num}', re.IGNORECASE),
                # Match "**PBT (Profit Before Tax):** ₹220.30 Cr" format - simple and direct
                re.compile(rf'pbt\s*\(profit before tax\)\**\s*:?\s*{curr}?\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'\*\*pbt.*?\*\*.*?{curr}?\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'{md_table}(?:pbt|profit before tax){md_val}{curr}?\s*{num}', re.IGNORECASE),
                re.compile(rf'(?:^|\n).*?pbt[:\s]+{curr}?\s*{num}\s*{unit_cr}', re.IGNORECASE | re.MULTILINE),
                re.compile(rf'{num}\s*{unit_cr}.*?pbt(?!\s*\()', re.IGNORECASE),
            ],
            
            'pat': [
                re.compile(rf'\*\*(?:pat|profit after tax)\s*\(profit after tax\)[:]*\*\*\s*:?\s*{curr}?\s*{num}', re.IGNORECASE),
                re.compile(rf'{md_table}(?:pat|net profit|profit after tax){md_val}{num}', re.IGNORECASE),
                re.compile(rf'(?:pat|profit after tax|net profit).*?{curr}\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'{num}\s*{unit_cr}.*?(?:pat|net profit)', re.IGNORECASE),
                re.compile(rf'net profit.*?{num}', re.IGNORECASE),
            ],
            
            'employee_cost': [
                re.compile(rf'\*\*employee cost\*\*\s*:?\s*{curr}?\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'{md_table}(?:employee cost|employee expenses|personnel cost|staff cost){md_val}{curr}?\s*{num}', re.IGNORECASE),
                re.compile(rf'(?:employee cost|employee expenses|personnel cost|staff cost)[:\s\|]+{curr}\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'(?:employee cost|employee expenses|personnel cost|staff cost)[:\s\|]+{curr}\s*{num}(?!\s*%)', re.IGNORECASE),
                re.compile(rf'{num}\s*{unit_cr}.*?(?:employee|personnel|staff) (?:cost|expense)', re.IGNORECASE),
            ],
            
            'other_expenses': [
                re.compile(rf'\*\*other expenses\*\*\s*:?\s*{curr}?\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'{md_table}(?:other expenses|operating expenses|other costs){md_val}{curr}?\s*{num}', re.IGNORECASE),
                re.compile(rf'(?:other expenses|operating expenses|other costs)[:\s\|]+{curr}\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'(?:other expenses|operating expenses|other costs)[:\s\|]+{curr}\s*{num}(?!\s*%)', re.IGNORECASE),
                re.compile(rf'{num}\s*{unit_cr}.*?other expenses', re.IGNORECASE),
            ],
            
            'depreciation': [
                re.compile(rf'\*\*depreciation\*\*\s*:?\s*{curr}?\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'{md_table}(?:depreciation|amortization|depreciation & amortization|d&a){md_val}{curr}?\s*{num}', re.IGNORECASE),
                re.compile(rf'(?:depreciation|amortization|d&a)[:\s\|]+{curr}\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'(?:depreciation|amortization|d&a)[:\s\|]+{curr}\s*{num}(?!\s*%)', re.IGNORECASE),
                re.compile(rf'{num}\s*{unit_cr}.*?depreciation', re.IGNORECASE),
            ],
            
            'interest': [
                re.compile(rf'\*\*(?:interest|interest expense|finance cost)[:]*\*\*\s*:?\s*{curr}?\s*{num}', re.IGNORECASE),
                re.compile(rf'{md_table}(?:interest|interest expense|finance cost){md_val}{curr}?\s*{num}', re.IGNORECASE),
                re.compile(rf'(?:interest|finance cost|interest expense)[:\s\|]+{curr}\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'(?:interest|finance cost|interest expense)[:\s\|]+{curr}\s*{num}(?!\s*%)', re.IGNORECASE),
                re.compile(rf'{num}\s*{unit_cr}.*?(?:interest|finance cost)', re.IGNORECASE),
            ],
            
            'other_income': [
                re.compile(rf'\*\*(?:other income|non-operating income)[:]*\*\*\s*:?\s*{curr}?\s*{num}', re.IGNORECASE),
                re.compile(rf'{md_table}(?:other income|non-operating income){md_val}{curr}?\s*{num}', re.IGNORECASE),
                re.compile(rf'(?:other income|non-operating income)[:\s\|]+{curr}\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'(?:other income|non-operating income)[:\s\|]+{curr}\s*{num}(?!\s*%)', re.IGNORECASE),
                re.compile(rf'{num}\s*{unit_cr}.*?other income', re.IGNORECASE),
            ],
            
            'tax': [
                # Exclude "before tax" phrases to avoid matching PBT
                re.compile(rf'(?:^|\W)(?:tax|taxation|income tax)(?!\s*\))[:\s\|]*{curr}\s*{num}\s*{unit_cr}', re.IGNORECASE),
                re.compile(rf'{num}\s*{unit_cr}.*?(?:tax|taxation)(?!\s*\))', re.IGNORECASE),
            ],
            
            # Margin patterns (percentages)
            'ebitda_margin': [
                re.compile(rf'(?:ebitda|operating) margin.*?{num}\s*%', re.IGNORECASE),
                re.compile(rf'{num}\s*%.*?(?:ebitda|operating) margin', re.IGNORECASE),
            ],
            
            'ebit_margin': [
                re.compile(rf'ebit margin.*?{num}\s*%', re.IGNORECASE),
                re.compile(rf'{num}\s*%.*?ebit margin', re.IGNORECASE),
            ],
            
            'profit_margin': [
                re.compile(rf'(?:profit|net) margin.*?{num}\s*%', re.IGNORECASE),
                re.compile(rf'{num}\s*%.*?(?:profit|net) margin', re.IGNORECASE),
            ],
            
            # EPS pattern
            'eps': [
                re.compile(rf'{md_table}(?:eps|earnings per share){md_val}(?:Rs\.?\s*)?{num}', re.IGNORECASE),
                re.compile(rf'(?:eps|earnings per share).*?(?:Rs\.?\s*)?{num}', re.IGNORECASE),
                re.compile(rf'(?:Rs\.?\s*)?{num}.*?(?:eps|earnings per share)', re.IGNORECASE),
            ],
        }
        
        return patterns
    
    def _clean_number(self, num_str: str) -> float:
        """Clean and convert number string to float"""
        # Remove currency symbols and extra spaces
        cleaned = num_str.replace('₹', '').replace('Rs', '').replace('INR', '').strip()
        # Remove commas
        cleaned = cleaned.replace(',', '')
        # Handle multiple dots (keep only the last one as decimal point)
        parts = cleaned.split('.')
        if len(parts) > 2:
            # Rejoin all but last part, then add last part with decimal
            cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
        try:
            value = float(cleaned)
            return value
        except ValueError:
            logger.warning(f"Could not convert '{num_str}' to float")
            return 0.0
    
    def extract_indicator(self, text: str, indicator: str) -> Optional[Tuple[float, float]]:
        """
        Extract a specific financial indicator from text
        
        Args:
            text: Text to extract from
            indicator: Indicator name (e.g., 'total_income', 'ebitda')
            
        Returns:
            Tuple of (value, confidence) or None if not found
        """
        if indicator not in self.patterns:
            logger.warning(f"Unknown indicator: {indicator}")
            return None
        
        patterns = self.patterns[indicator]
        
        for i, pattern in enumerate(patterns):
            match = pattern.search(text)
            if match:
                value = self._clean_number(match.group(1))
                
                # Confidence scoring based on pattern position and match quality
                # Earlier patterns are usually more specific = higher confidence
                confidence = 0.95 - (i * 0.1)  # First pattern: 0.95, second: 0.85, etc.
                
                # Boost confidence if we find context keywords nearby
                context_window = text[max(0, match.start()-100):min(len(text), match.end()+100)]
                if any(word in context_window.lower() for word in ['quarterly', 'q1', 'q2', 'q3', 'q4', 'fy']):
                    confidence = min(1.0, confidence + 0.05)
                
                logger.info(f"Extracted {indicator}: {value} (confidence: {confidence:.2f})")
                return (value, confidence)
        
        logger.debug(f"No match found for {indicator}")
        return None
    
    def extract_all_indicators(self, text: str) -> Dict[str, Dict]:
        """
        Extract all financial indicators from text
        
        Args:
            text: Text to extract from
            
        Returns:
            Dictionary of indicator_name: {value, confidence}
        """
        results = {}
        
        for indicator in self.patterns.keys():
            extraction = self.extract_indicator(text, indicator)
            if extraction:
                value, confidence = extraction
                results[indicator] = {
                    'value': value,
                    'confidence': confidence
                }
        
        # Validation: Check for unreasonable values
        # PBT should not equal total_income (common extraction error)
        if 'pbt' in results and 'total_income' in results:
            if abs(results['pbt']['value'] - results['total_income']['value']) < 1.0:
                logger.warning(f"PBT ({results['pbt']['value']}) equals Total Income - likely extraction error, removing PBT")
                del results['pbt']
        
        # PAT should be less than total_income and not be a small percentage value
        if 'pat' in results and 'total_income' in results:
            pat_val = results['pat']['value']
            income_val = results['total_income']['value']
            # If PAT is less than 100 and total income is in thousands, likely extracted a percentage
            if pat_val < 100 and income_val > 10000:
                logger.warning(f"PAT ({pat_val}) seems to be a percentage, not absolute value - removing")
                del results['pat']
        
        # Check if text explicitly says a field is "Not available" or "Not disclosed"
        for indicator in list(results.keys()):
            # Search for patterns like "PBT: Not available" or "Interest: Not disclosed"
            indicator_label = indicator.replace('_', ' ').title()
            not_available_pattern = rf'{indicator_label}[:\s]+(?:Not|N/A|NA|not available|not disclosed|not reported|not explicitly)'
            if re.search(not_available_pattern, text, re.IGNORECASE):
                logger.warning(f"{indicator_label} marked as not available in text - removing extracted value")
                del results[indicator]
        
        logger.info(f"Extracted {len(results)} indicators from text (after validation)")
        return results
    
    def extract_with_context(self, text: str, company: str, quarter: str, year: int) -> Dict:
        """
        Extract financial data with context validation
        
        Args:
            text: Response text
            company: Company name
            quarter: Quarter (Q1, Q2, Q3, Q4)
            year: Year
            
        Returns:
            Dictionary with extracted data and metadata
        """
        # Verify the text mentions the correct company/period
        text_lower = text.lower()
        company_mentioned = company.lower() in text_lower
        quarter_mentioned = quarter.lower() in text_lower or f"fy {year}" in text_lower
        
        context_confidence = 1.0
        if not company_mentioned:
            context_confidence -= 0.3
            logger.warning(f"Company '{company}' not clearly mentioned in response")
        if not quarter_mentioned:
            context_confidence -= 0.2
            logger.warning(f"Quarter/Year '{quarter} {year}' not clearly mentioned")
        
        # Extract all indicators
        extracted = self.extract_all_indicators(text)
        
        # Adjust confidence based on context
        for indicator in extracted:
            extracted[indicator]['confidence'] *= context_confidence
            extracted[indicator]['confidence'] = round(min(1.0, extracted[indicator]['confidence']), 2)
        
        return {
            'company': company,
            'quarter': quarter,
            'year': year,
            'extracted_data': extracted,
            'context_confidence': context_confidence,
            'raw_text': text
        }
    
    def get_extraction_summary(self, extracted_data: Dict) -> str:
        """Generate human-readable summary of extraction"""
        summary_lines = []
        summary_lines.append(f"Company: {extracted_data['company']}")
        summary_lines.append(f"Period: {extracted_data['quarter']} {extracted_data['year']}")
        summary_lines.append(f"Context Confidence: {extracted_data['context_confidence']:.2f}")
        summary_lines.append("\nExtracted Indicators:")
        
        data = extracted_data['extracted_data']
        if not data:
            summary_lines.append("  No data extracted")
        else:
            for indicator, values in data.items():
                summary_lines.append(f"  {indicator}: ₹{values['value']:.2f} Cr (conf: {values['confidence']:.2f})")
        
        return '\n'.join(summary_lines)
