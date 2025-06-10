import pytest
import json
import time
from reimbly.tools.cache import Cache
from google.cloud import firestore
from datetime import datetime, timedelta
import os
from unittest.mock import patch

@pytest.fixture
def cache():
    """Create a cache instance for testing."""
    # Use a test collection to avoid affecting production data
    os.environ['FIRESTORE_CACHE_COLLECTION'] = 'test_cache'
    cache = Cache()
    yield cache
    # Clean up after tests
    cache.clear()

def test_set_and_get(cache):
    """Test basic set and get operations."""
    # Test setting and getting a simple value
    cache.set('test_key', 'test_value')
    assert cache.get('test_key') == 'test_value'
    
    # Test setting and getting a complex value
    complex_value = {'name': 'test', 'numbers': [1, 2, 3]}
    cache.set('complex_key', complex_value)
    assert cache.get('complex_key') == complex_value

def test_ttl(cache):
    """Test time-to-live functionality."""
    # Set a value with 1 second TTL
    cache.set('ttl_key', 'ttl_value', ttl=1)
    assert cache.get('ttl_key') == 'ttl_value'
    
    # Wait for TTL to expire
    time.sleep(1.1)
    assert cache.get('ttl_key') is None

def test_delete(cache):
    """Test delete operation."""
    cache.set('delete_key', 'delete_value')
    assert cache.exists('delete_key')
    
    cache.delete('delete_key')
    assert not cache.exists('delete_key')

def test_exists(cache):
    """Test exists operation."""
    assert not cache.exists('nonexistent_key')
    
    cache.set('existent_key', 'value')
    assert cache.exists('existent_key')

def test_set_many_and_get_many(cache):
    """Test batch operations."""
    # Test setting multiple values
    mapping = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3'
    }
    cache.set_many(mapping)
    
    # Test getting multiple values
    result = cache.get_many(['key1', 'key2', 'key3'])
    assert result == mapping
    
    # Test getting some nonexistent keys
    result = cache.get_many(['key1', 'nonexistent'])
    assert result == {'key1': 'value1', 'nonexistent': None}

def test_clear(cache):
    """Test clear operation."""
    # Set some values
    cache.set('key1', 'value1')
    cache.set('key2', 'value2')
    
    # Clear the cache
    cache.clear()
    
    # Verify all values are gone
    assert not cache.exists('key1')
    assert not cache.exists('key2')

def test_get_or_set(cache):
    """Test get_or_set operation."""
    # Test when value doesn't exist
    def default_func():
        return 'default_value'
    
    value = cache.get_or_set('get_or_set_key', default_func)
    assert value == 'default_value'
    
    # Test when value exists
    cache.set('get_or_set_key', 'existing_value')
    value = cache.get_or_set('get_or_set_key', default_func)
    assert value == 'existing_value'

def test_json_serialization(cache):
    """Test JSON serialization of complex objects."""
    # Test with datetime
    now = datetime.now()
    cache.set('datetime_key', now)
    retrieved = cache.get('datetime_key')
    assert isinstance(retrieved, str)  # Should be serialized to string
    
    # Test with custom object
    class TestObject:
        def __init__(self, value):
            self.value = value
    
    obj = TestObject('test')
    with pytest.raises(TypeError):
        cache.set('object_key', obj)  # Should fail as object is not JSON serializable

def test_error_handling(cache):
    """Test error handling."""
    # Test with invalid key type
    with pytest.raises(TypeError):
        cache.set(123, 'value')  # Key must be string
    
    # Test with invalid TTL
    with pytest.raises(TypeError):
        cache.set('key', 'value', ttl='invalid')  # TTL must be int

def test_cleanup_expired(cache):
    """Test cleanup of expired entries."""
    # Set some values with different TTLs
    cache.set('expired_key', 'expired_value', ttl=1)
    cache.set('valid_key', 'valid_value', ttl=3600)
    
    # Wait for the first key to expire
    time.sleep(1.1)
    
    # Run cleanup
    cache.cleanup_expired()
    
    # Verify expired key is gone but valid key remains
    assert not cache.exists('expired_key')
    assert cache.exists('valid_key')

def test_timestamp_handling(cache):
    """Test handling of Firestore timestamps."""
    # Set a value
    cache.set('timestamp_key', 'value')
    
    # Get the document directly from Firestore
    doc = cache._get_cache_doc('timestamp_key').get()
    data = doc.to_dict()
    
    # Verify timestamp fields exist
    assert 'updated_at' in data
    assert isinstance(data['updated_at'], datetime)
    
    # Verify the value is correct
    assert json.loads(data['value']) == 'value'

def test_batch_operations(cache):
    """Test batch operations with large datasets."""
    # Create a large dataset
    large_mapping = {f'key_{i}': f'value_{i}' for i in range(1000)}
    
    # Test setting many values
    assert cache.set_many(large_mapping)
    
    # Test getting many values
    keys = list(large_mapping.keys())
    result = cache.get_many(keys)
    
    # Verify all values are correct
    for key in keys:
        assert result[key] == large_mapping[key]

def test_concurrent_operations(cache):
    """Test concurrent operations on the cache."""
    import threading
    
    def worker():
        for i in range(100):
            key = f'concurrent_key_{i}'
            cache.set(key, f'value_{i}')
            assert cache.get(key) == f'value_{i}'
    
    # Create multiple threads
    threads = [threading.Thread(target=worker) for _ in range(5)]
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify all values were set correctly
    for i in range(100):
        key = f'concurrent_key_{i}'
        assert cache.exists(key)
        assert cache.get(key) == f'value_{i}'

def test_ttl_edge_cases(cache):
    """Test TTL edge cases."""
    # Test with very short TTL
    cache.set('short_ttl', 'value', ttl=0)
    assert cache.get('short_ttl') is None
    
    # Test with very long TTL
    cache.set('long_ttl', 'value', ttl=31536000)  # 1 year
    assert cache.get('long_ttl') == 'value'
    
    # Test with negative TTL
    with pytest.raises(ValueError):
        cache.set('negative_ttl', 'value', ttl=-1)

def test_batch_ttl(cache):
    """Test batch operations with TTL."""
    # Set multiple values with TTL
    mapping = {
        'batch_ttl_1': 'value1',
        'batch_ttl_2': 'value2'
    }
    cache.set_many(mapping, ttl=1)
    
    # Verify values are set
    assert cache.get('batch_ttl_1') == 'value1'
    assert cache.get('batch_ttl_2') == 'value2'
    
    # Wait for TTL to expire
    time.sleep(1.1)
    
    # Verify values are expired
    assert cache.get('batch_ttl_1') is None
    assert cache.get('batch_ttl_2') is None

def test_get_or_set_with_ttl(cache):
    """Test get_or_set with TTL."""
    def default_func():
        return 'default_value'
    
    # Test get_or_set with TTL
    value = cache.get_or_set('get_or_set_ttl', default_func, ttl=1)
    assert value == 'default_value'
    
    # Verify value is set with TTL
    doc = cache._get_cache_doc('get_or_set_ttl').get()
    data = doc.to_dict()
    assert 'expires_at' in data
    
    # Wait for TTL to expire
    time.sleep(1.1)
    
    # Verify value is expired and new value is set
    value = cache.get_or_set('get_or_set_ttl', default_func, ttl=1)
    assert value == 'default_value'

def test_cleanup_expired_batch(cache):
    """Test cleanup of expired entries in batches."""
    # Set multiple values with different TTLs
    expired_mapping = {f'expired_{i}': f'value_{i}' for i in range(100)}
    valid_mapping = {f'valid_{i}': f'value_{i}' for i in range(100)}
    
    # Set expired values
    cache.set_many(expired_mapping, ttl=1)
    # Set valid values
    cache.set_many(valid_mapping, ttl=3600)
    
    # Wait for expired values to expire
    time.sleep(1.1)
    
    # Run cleanup
    cache.cleanup_expired()
    
    # Verify expired values are gone but valid values remain
    for i in range(100):
        assert not cache.exists(f'expired_{i}')
        assert cache.exists(f'valid_{i}')

def test_error_recovery(cache):
    """Test error recovery in cache operations."""
    # Test recovery from failed set
    with patch.object(cache.db, 'batch', side_effect=Exception('Test error')):
        assert not cache.set_many({'key': 'value'})
    
    # Test recovery from failed get
    with patch.object(cache.db, 'get_all', side_effect=Exception('Test error')):
        assert cache.get_many(['key']) == {}
    
    # Test recovery from failed clear
    with patch.object(cache.cache_collection, 'limit', side_effect=Exception('Test error')):
        assert not cache.clear()

def test_document_structure(cache):
    """Test Firestore document structure."""
    # Set a value
    cache.set('structure_test', 'value', ttl=3600)
    
    # Get the document
    doc = cache._get_cache_doc('structure_test').get()
    data = doc.to_dict()
    
    # Verify document structure
    assert 'value' in data
    assert 'updated_at' in data
    assert 'expires_at' in data
    assert isinstance(data['updated_at'], datetime)
    assert isinstance(data['expires_at'], datetime)
    assert data['expires_at'] > data['updated_at']

def test_user_specific_cache(cache):
    """Test user-specific cache operations."""
    # Set cache entries for different users
    cache.set('key1', 'value1', user_id='user1')
    cache.set('key2', 'value2', user_id='user2')
    cache.set('key3', 'value3', user_id='user1')
    cache.set('key4', 'value4')  # No user_id

    # Test getting values with correct user_id
    assert cache.get('key1', user_id='user1') == 'value1'
    assert cache.get('key2', user_id='user2') == 'value2'
    assert cache.get('key3', user_id='user1') == 'value3'
    assert cache.get('key4') == 'value4'  # Should work without user_id

    # Test getting values with wrong user_id
    assert cache.get('key1', user_id='user2') is None
    assert cache.get('key2', user_id='user1') is None

    # Test getting values with user_id when none was set
    assert cache.get('key4', user_id='user1') is None

    # Test clearing user cache
    assert cache.clear_user_cache('user1')
    assert cache.get('key1', user_id='user1') is None
    assert cache.get('key3', user_id='user1') is None
    assert cache.get('key2', user_id='user2') == 'value2'  # Other user's cache should remain
    assert cache.get('key4') == 'value4'  # No user_id cache should remain

def test_user_cache_with_ttl(cache):
    """Test user-specific cache with TTL."""
    # Set values with TTL for different users
    cache.set('key1', 'value1', user_id='user1', ttl=1)
    cache.set('key2', 'value2', user_id='user2', ttl=3600)
    cache.set('key3', 'value3', user_id='user1', ttl=1)

    # Verify initial values
    assert cache.get('key1', user_id='user1') == 'value1'
    assert cache.get('key2', user_id='user2') == 'value2'
    assert cache.get('key3', user_id='user1') == 'value3'

    # Wait for TTL to expire
    time.sleep(1.1)

    # Verify expired values
    assert cache.get('key1', user_id='user1') is None
    assert cache.get('key3', user_id='user1') is None
    assert cache.get('key2', user_id='user2') == 'value2'  # Should still be valid

def test_user_cache_batch_operations(cache):
    """Test batch operations with user-specific cache."""
    # Set multiple values for different users
    user1_mapping = {f'user1_key_{i}': f'value_{i}' for i in range(5)}
    user2_mapping = {f'user2_key_{i}': f'value_{i}' for i in range(5)}

    # Set values for user1
    for key, value in user1_mapping.items():
        cache.set(key, value, user_id='user1')

    # Set values for user2
    for key, value in user2_mapping.items():
        cache.set(key, value, user_id='user2')

    # Test getting values for user1
    for key in user1_mapping:
        assert cache.get(key, user_id='user1') == user1_mapping[key]
        assert cache.get(key, user_id='user2') is None

    # Test getting values for user2
    for key in user2_mapping:
        assert cache.get(key, user_id='user2') == user2_mapping[key]
        assert cache.get(key, user_id='user1') is None

    # Clear user1's cache
    cache.clear_user_cache('user1')

    # Verify user1's values are gone but user2's remain
    for key in user1_mapping:
        assert cache.get(key, user_id='user1') is None
    for key in user2_mapping:
        assert cache.get(key, user_id='user2') == user2_mapping[key]

def test_user_cache_error_handling(cache):
    """Test error handling for user-specific cache operations."""
    # Test with invalid user_id type
    with pytest.raises(TypeError):
        cache.set('key', 'value', user_id=123)  # user_id should be string

    # Test with invalid key type
    with pytest.raises(TypeError):
        cache.set(123, 'value', user_id='user1')

    # Test with invalid TTL
    with pytest.raises(TypeError):
        cache.set('key', 'value', user_id='user1', ttl='invalid')

    # Test clearing cache for non-existent user
    assert cache.clear_user_cache('non_existent_user')  # Should return True but do nothing

def test_user_cache_stats(cache):
    """Test cache statistics for user-specific operations."""
    # Reset stats
    cache.reset_stats()
    
    # Perform cache operations
    cache.set('key1', 'value1', user_id='user1')
    cache.set('key2', 'value2', user_id='user2')
    cache.get('key1', user_id='user1')  # Hit
    cache.get('key2', user_id='user1')  # Miss (wrong user)
    cache.get('key3', user_id='user1')  # Miss (non-existent)
    cache.delete('key1')
    
    # Check stats
    stats = cache.get_stats()
    assert stats['sets'] == 2
    assert stats['hits'] == 1
    assert stats['misses'] == 2
    assert stats['deletes'] == 1 