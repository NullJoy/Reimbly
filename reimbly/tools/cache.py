from google.cloud import firestore
import json
import logging
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta, timezone
import os
from json import JSONEncoder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DateTimeEncoder(JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class Cache:
    def __init__(self, collection_name: str = 'cache'):
        """Initialize cache with Firestore collection."""
        self.db = firestore.Client()
        self.cache_collection = self.db.collection(collection_name)
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }

    def _get_cache_doc(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a cache document by key."""
        try:
            doc = self.cache_collection.document(key).get()
            if not doc.exists:
                return None
            return doc.to_dict()
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None

    def _serialize_value(self, value: Any) -> str:
        """Serialize a value to JSON string."""
        try:
            return json.dumps(value, cls=DateTimeEncoder)
        except TypeError as e:
            raise TypeError(f"Value is not JSON serializable: {str(e)}")

    def _deserialize_value(self, value_str: str) -> Any:
        """Deserialize a JSON string to a value."""
        try:
            return json.loads(value_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error deserializing value: {str(e)}")
            return None

    def set(self, key: str, value: Any, user_id: Optional[str] = None, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache with optional TTL and user_id."""
        try:
            if not isinstance(key, str):
                raise TypeError("Cache key must be a string")

            now = datetime.now(timezone.utc)
            cache_data = {
                'value': self._serialize_value(value),
                'created_at': now,
                'updated_at': now,
                'user_id': user_id
            }

            if ttl is not None:
                if not isinstance(ttl, int):
                    raise TypeError("TTL must be an integer")
                cache_data['expires_at'] = now + timedelta(seconds=ttl)

            self.cache_collection.document(key).set(cache_data)
            self.stats['sets'] += 1
            return True

        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False

    def get(self, key: str, user_id: Optional[str] = None) -> Any:
        """Get a value from the cache, optionally checking user_id."""
        try:
            if not isinstance(key, str):
                raise TypeError("Cache key must be a string")

            cache_data = self._get_cache_doc(key)
            if not cache_data:
                self.stats['misses'] += 1
                return None

            # Check user_id if provided
            if user_id is not None and cache_data.get('user_id') != user_id:
                self.stats['misses'] += 1
                return None

            # Check expiration
            expires_at = cache_data.get('expires_at')
            if expires_at and expires_at < datetime.now(timezone.utc):
                self.delete(key)
                self.stats['misses'] += 1
                return None

            self.stats['hits'] += 1
            return self._deserialize_value(cache_data['value'])

        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        if not isinstance(key, str):
            raise TypeError("Cache key must be a string")

        try:
            self.cache_collection.document(key).delete()
            self.stats['deletes'] += 1
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        if not isinstance(key, str):
            raise TypeError("Cache key must be a string")

        try:
            cache_data = self._get_cache_doc(key)
            if not cache_data:
                return False

            expires_at = cache_data.get('expires_at')
            if isinstance(expires_at, datetime) and expires_at < datetime.now(timezone.utc):
                self.delete(key)
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {str(e)}")
            return False

    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in the cache."""
        if not all(isinstance(k, str) for k in mapping.keys()):
            raise TypeError("All cache keys must be strings")

        try:
            batch = self.db.batch()
            now = datetime.now(timezone.utc)

            for key, value in mapping.items():
                cache_data = {
                    'value': self._serialize_value(value),
                    'updated_at': now
                }

                if ttl is not None:
                    if ttl <= 0:
                        cache_data['expires_at'] = now
                    else:
                        cache_data['expires_at'] = now + timedelta(seconds=ttl)

                batch.set(self.cache_collection.document(key), cache_data)

            batch.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting multiple cache keys: {str(e)}")
            return False

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from the cache."""
        if not all(isinstance(k, str) for k in keys):
            raise TypeError("All cache keys must be strings")

        try:
            result = {}
            now = datetime.now(timezone.utc)

            for key in keys:
                cache_data = self._get_cache_doc(key)
                if not cache_data:
                    continue

                expires_at = cache_data.get('expires_at')
                if isinstance(expires_at, datetime) and expires_at < now:
                    self.delete(key)
                    continue

                result[key] = self._deserialize_value(cache_data['value'])

            return result
        except Exception as e:
            logger.error(f"Error getting multiple cache keys: {str(e)}")
            return {}

    def clear(self) -> bool:
        """Clear all values from the cache.
        
        Returns:
            bool: True if successful
        """
        try:
            # Get all documents
            docs = self.cache_collection.limit(500).stream()
            
            # Delete in batches
            batch = self.db.batch()
            count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
                
                # Commit batch when it reaches 500 operations
                if count == 500:
                    batch.commit()
                    batch = self.db.batch()
                    count = 0
            
            # Commit any remaining operations
            if count > 0:
                batch.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False

    def get_or_set(self, key: str, default_value: Any, ttl: Optional[int] = None) -> Any:
        """Get a value from the cache or set it if it doesn't exist."""
        if not isinstance(key, str):
            raise TypeError("Cache key must be a string")

        value = self.get(key)
        if value is None:
            self.set(key, default_value, ttl)
            return default_value
        return value

    def cleanup_expired(self) -> int:
        """Clean up expired entries from the cache."""
        try:
            expired = self.cache_collection.where('expires_at', '<', datetime.now(timezone.utc)).limit(500).stream()
            batch = self.db.batch()
            count = 0

            for doc in expired:
                batch.delete(doc.reference)
                count += 1

            if count > 0:
                batch.commit()

            return count
        except Exception as e:
            logger.error(f"Error cleaning up expired cache entries: {str(e)}")
            return 0

    def clear_user_cache(self, user_id: str) -> bool:
        """Clear all cache entries for a specific user."""
        try:
            # Get all documents for this user
            user_docs = self.cache_collection.where('user_id', '==', user_id).stream()
            
            # Delete in batches
            batch = self.db.batch()
            count = 0
            
            for doc in user_docs:
                batch.delete(doc.reference)
                count += 1
                if count >= 500:  # Firestore batch limit
                    batch.commit()
                    batch = self.db.batch()
                    count = 0
            
            if count > 0:
                batch.commit()
            
            logger.info(f"Cleared {count} cache entries for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing user cache for {user_id}: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }

# Create a singleton instance
cache = Cache() 