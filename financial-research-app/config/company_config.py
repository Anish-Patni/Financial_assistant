# Company Configuration
# Moneycontrol company mappings and settings

from typing import Dict, List, Optional
import json
from pathlib import Path
from config.logging_config import get_logger

logger = get_logger('company_config')

# Moneycontrol company code mappings
# Format: company_name -> {slug, code, sector}
MONEYCONTROL_COMPANIES = {
    'TCS': {
        'slug': 'tataconsultancyservices',
        'code': 'TCS',
        'sector': 'computers-software',
        'full_name': 'Tata Consultancy Services Ltd.'
    },
    'Infosys': {
        'slug': 'infosys',
        'code': 'IT',
        'sector': 'computers-software',
        'full_name': 'Infosys Ltd.'
    },
    'Wipro': {
        'slug': 'wipro',
        'code': 'W',
        'sector': 'computers-software',
        'full_name': 'Wipro Ltd.'
    },
    'Tech Mahindra': {
        'slug': 'techmahindra',
        'code': 'TM4',
        'sector': 'computers-software',
        'full_name': 'Tech Mahindra Ltd.'
    },
    'HCL Tech': {
        'slug': 'hcltechnologies',
        'code': 'HCL02',
        'sector': 'computers-software',
        'full_name': 'HCL Technologies Ltd.'
    },
    'LTIMindtree': {
        'slug': 'ltimindtree',
        'code': 'LI12',
        'sector': 'computers-software',
        'full_name': 'LTIMindtree Ltd.'
    },
    'Persistent Systems': {
        'slug': 'persistentsystems',
        'code': 'PS05',
        'sector': 'computers-software',
        'full_name': 'Persistent Systems Ltd.'
    },
    'Coforge': {
        'slug': 'aborocoforge',
        'code': 'NC13',
        'sector': 'computers-software',
        'full_name': 'Coforge Ltd.'
    },
    'MPHASIS': {
        'slug': 'aboromphasis',
        'code': 'MP',
        'sector': 'computers-software',
        'full_name': 'Mphasis Ltd.'
    },
    'Cyient': {
        'slug': 'cyaboroient',
        'code': 'IL',
        'sector': 'computers-software',
        'full_name': 'Cyient Ltd.'
    },
    'LT Technology Services': {
        'slug': 'aboraboroltaborotechnologyservices',
        'code': 'LT11',
        'sector': 'computers-software',
        'full_name': 'L&T Technology Services Ltd.'
    },
    'Zensar': {
        'slug': 'zaboroensartechnologies',
        'code': 'ZT',
        'sector': 'computers-software',
        'full_name': 'Zensar Technologies Ltd.'
    },
    'Hexaware': {
        'slug': 'hexaboroawaretechnologies',
        'code': 'HT10',
        'sector': 'computers-software',
        'full_name': 'Hexaware Technologies Ltd.'
    },
    'Birlasoft': {
        'slug': 'birlasoft',
        'code': 'KS13',
        'sector': 'computers-software',
        'full_name': 'Birlasoft Ltd.'
    }
}

# Custom companies file path
CUSTOM_COMPANIES_FILE = Path(__file__).parent.parent / 'data' / 'custom_companies.json'


class CompanyConfig:
    """Manage company configurations and custom companies"""
    
    def __init__(self):
        self.companies = MONEYCONTROL_COMPANIES.copy()
        self._load_custom_companies()
    
    def _load_custom_companies(self):
        """Load custom companies from file"""
        try:
            if CUSTOM_COMPANIES_FILE.exists():
                with open(CUSTOM_COMPANIES_FILE, 'r') as f:
                    custom = json.load(f)
                    self.companies.update(custom)
                    logger.info(f"Loaded {len(custom)} custom companies")
        except Exception as e:
            logger.error(f"Error loading custom companies: {e}")
    
    def _save_custom_companies(self):
        """Save custom companies to file"""
        try:
            CUSTOM_COMPANIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Get only custom companies (not in default)
            custom = {k: v for k, v in self.companies.items() 
                     if k not in MONEYCONTROL_COMPANIES}
            
            with open(CUSTOM_COMPANIES_FILE, 'w') as f:
                json.dump(custom, f, indent=2)
            
            logger.info(f"Saved {len(custom)} custom companies")
        except Exception as e:
            logger.error(f"Error saving custom companies: {e}")
    
    def get_company(self, name: str) -> Optional[Dict]:
        """Get company configuration by name"""
        # Try exact match first
        if name in self.companies:
            return self.companies[name]
        
        # Try case-insensitive match
        name_lower = name.lower()
        for company_name, config in self.companies.items():
            if company_name.lower() == name_lower:
                return config
        
        return None
    
    def get_all_companies(self) -> List[str]:
        """Get list of all company names"""
        return list(self.companies.keys())
    
    def add_company(self, name: str, slug: str, code: str, 
                   sector: str = 'computers-software', 
                   full_name: str = None) -> bool:
        """
        Add a new company
        
        Args:
            name: Company display name
            slug: Moneycontrol URL slug
            code: Moneycontrol company code
            sector: Company sector
            full_name: Full company name
            
        Returns:
            True if added successfully
        """
        if name in self.companies:
            logger.warning(f"Company '{name}' already exists")
            return False
        
        self.companies[name] = {
            'slug': slug,
            'code': code,
            'sector': sector,
            'full_name': full_name or f"{name} Ltd."
        }
        
        self._save_custom_companies()
        logger.info(f"Added company: {name}")
        return True
    
    def remove_company(self, name: str) -> bool:
        """
        Remove a company
        
        Args:
            name: Company name to remove
            
        Returns:
            True if removed successfully
        """
        if name not in self.companies:
            logger.warning(f"Company '{name}' not found")
            return False
        
        if name in MONEYCONTROL_COMPANIES:
            logger.warning(f"Cannot remove default company '{name}'")
            return False
        
        del self.companies[name]
        self._save_custom_companies()
        logger.info(f"Removed company: {name}")
        return True
    
    def get_moneycontrol_url(self, name: str, url_type: str = 'quarterly') -> Optional[str]:
        """
        Get Moneycontrol URL for a company
        
        Args:
            name: Company name
            url_type: Type of URL (quarterly, profit-loss, balance-sheet)
            
        Returns:
            Full URL or None
        """
        config = self.get_company(name)
        if not config:
            return None
        
        slug = config['slug']
        code = config['code']
        
        url_patterns = {
            'quarterly': f"https://www.moneycontrol.com/financials/{slug}/results/quarterly-results/{code}",
            'profit-loss': f"https://www.moneycontrol.com/financials/{slug}/profit-lossVI/{code}",
            'balance-sheet': f"https://www.moneycontrol.com/financials/{slug}/balance-sheetVI/{code}",
            'ratios': f"https://www.moneycontrol.com/financials/{slug}/ratiosVI/{code}",
            'stock': f"https://www.moneycontrol.com/india/stockpricequote/{config['sector']}/{slug}/{code}"
        }
        
        return url_patterns.get(url_type)


# Global instance
company_config = CompanyConfig()
