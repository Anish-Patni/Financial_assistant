# Cache Manager
# Intelligent caching system for API responses

import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any
from config.logging_config import get_logger

logger = get_logger('cache')

class CacheManager:
    """Manages caching of API responses with TTL support"""
    
    def __init__(self, cache_dir: Path, ttl_seconds: int = 86400):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            ttl_seconds: Time to live for cache entries (default 24 hours)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self.stats = {'hits': 0, 'misses': 0}
        
    def _generate_key(self, data: Any) -> str:
        """Generate cache key from data"""
        key_string = json.dumps(data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query_params: Dict[str, Any]) -> Optional[Dict]:
        """
        Retrieve cached response
        
        Args:
            query_params: Query parameters to lookup
            
        Returns:
            Cached response or None if not found/expired
        """
        cache_key = self._generate_key(query_params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            self.stats['misses'] += 1
            logger.debug(f"Cache miss: {cache_key}")
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if expired
            cached_time = cache_data.get('timestamp', 0)
            if time.time() - cached_time > self.ttl_seconds:
                logger.debug(f"Cache expired: {cache_key}")
                cache_file.unlink()  # Delete expired cache
                self.stats['misses'] += 1
                return None
            
            self.stats['hits'] += 1
            logger.debug(f"Cache hit: {cache_key}")
            return cache_data.get('response')
            
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            self.stats['misses'] += 1
            return None
    
    def set(self, query_params: Dict[str, Any], response: Dict):
        """
        Store response in cache
        
        Args:
            query_params: Query parameters used as key
            response: Response to cache
        """
        cache_key = self._generate_key(query_params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        cache_data = {
            'timestamp': time.time(),
            'query_params': query_params,
            'response': response
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"Cached response: {cache_key}")
        except Exception as e:
            logger.error(f"Error writing cache: {e}")
    
    def clear(self):
        """Clear all cache files"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared")
            self.stats = {'hits': 0, 'misses': 0}
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'total_requests': total,
            'hit_rate_percent': round(hit_rate, 2)
        }
