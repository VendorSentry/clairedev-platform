
import time
import hashlib
import json
from typing import Dict, Any, Optional

class LightweightCache:
    def __init__(self, max_size: int = 100, default_ttl: int = 3600):
        self._cache: Dict[str, Dict] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry['expires']:
                return entry['value']
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        if len(self._cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['created'])
            del self._cache[oldest_key]
        
        self._cache[key] = {
            'value': value,
            'created': time.time(),
            'expires': time.time() + (ttl or self.default_ttl)
        }
    
    def cache_key(self, *args) -> str:
        combined = json.dumps(args, sort_keys=True)
        return hashlib.md5(combined.encode()).hexdigest()

# Global cache instance
cache = LightweightCache()
