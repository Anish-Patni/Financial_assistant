# Research Storage System
# Store and retrieve research results with versioning

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from config.logging_config import get_logger

logger = get_logger('research_storage')

class ResearchStorage:
    """Manage storage and retrieval of research results"""
    
    def __init__(self, storage_dir: Path):
        """
        Initialize storage system
        
        Args:
            storage_dir: Directory to store research results
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_file_path(self, company: str, quarter: str, year: int) -> Path:
        """Generate file path for research result"""
        filename = f"{company.replace(' ', '_')}_{quarter}_{year}.json"
        return self.storage_dir / filename
    
    def save_research(self, research_data: Dict) -> bool:
        """
        Save research results to file
        
        Args:
            research_data: Research data dictionary
            
        Returns:
            True if successful
        """
        try:
            company = research_data['company']
            quarter = research_data['quarter']
            year = research_data['year']
            
            file_path = self._get_file_path(company, quarter, year)
            
            # Add metadata
            research_data['save_timestamp'] = datetime.now().isoformat()
            research_data['version'] = research_data.get('version', 1)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(research_data, f, indent=2)
            
            logger.info(f"Saved research: {company} {quarter} {year}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving research: {e}")
            return False
    
    def load_research(self, company: str, quarter: str, year: int) -> Optional[Dict]:
        """
        Load research results from file
        
        Args:
            company: Company name
            quarter: Quarter
            year: Year
            
        Returns:
            Research data or None if not found
        """
        try:
            file_path = self._get_file_path(company, quarter, year)
            
            if not file_path.exists():
                logger.debug(f"No saved research found for {company} {quarter} {year}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded research: {company} {quarter} {year}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading research: {e}")
            return None
    
    def get_all_research(self, company: Optional[str] = None) -> List[Dict]:
        """
        Get all stored research results
        
        Args:
            company: Filter by company name (None for all)
            
        Returns:
            List of research data dictionaries
        """
        results = []
        
        try:
            for file_path in self.storage_dir.glob("*.json"):
                if company and not file_path.stem.startswith(company.replace(' ', '_')):
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append(data)
            
            logger.info(f"Loaded {len(results)} research results")
            return results
            
        except Exception as e:
            logger.error(f"Error loading all research: {e}")
            return results
    
    def delete_research(self, company: str, quarter: str, year: int) -> bool:
        """Delete specific research result"""
        try:
            file_path = self._get_file_path(company, quarter, year)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted research: {company} {quarter} {year}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting research: {e}")
            return False
    
    def get_research_summary(self) -> Dict:
        """Get summary of all stored research"""
        all_research = self.get_all_research()
        
        companies = set()
        quarters_years = set()
        total_extractions = 0
        avg_confidence = 0.0
        
        for research in all_research:
            companies.add(research['company'])
            quarters_years.add(f"{research['quarter']} {research['year']}")
            
            if 'extracted_data' in research:
                total_extractions += len(research['extracted_data'])
                
                # Calculate average confidence
                for indicator_data in research['extracted_data'].values():
                    avg_confidence += indicator_data.get('confidence', 0)
        
        if total_extractions > 0:
            avg_confidence /= total_extractions
        
        return {
            'total_research_count': len(all_research),
            'unique_companies': len(companies),
            'unique_periods': len(quarters_years),
            'total_extractions': total_extractions,
            'average_confidence': round(avg_confidence, 2),
            'companies': sorted(list(companies)),
            'periods': sorted(list(quarters_years))
        }
