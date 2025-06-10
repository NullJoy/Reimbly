import pytest
from unittest.mock import Mock, patch
from tools.realtime import RealtimeListener
from google.cloud import firestore
import threading

@pytest.fixture
def realtime():
    """Create a realtime listener instance for testing."""
    return RealtimeListener()

@pytest.fixture
def mock_callback():
    """Create a mock callback function."""
    return Mock()

def test_add_listener(realtime, mock_callback):
    """Test adding a listener."""
    # Add a listener
    listener_id = realtime.add_listener('test_collection', mock_callback)
    
    # Verify listener was added
    assert listener_id in [lid for lid, _ in realtime.listeners['test_collection']]
    assert len(realtime.listeners['test_collection']) == 1

def test_remove_listener(realtime, mock_callback):
    """Test removing a listener."""
    # Add a listener
    listener_id = realtime.add_listener('test_collection', mock_callback)
    
    # Remove the listener
    assert realtime.remove_listener(listener_id)
    
    # Verify listener was removed
    assert 'test_collection' not in realtime.listeners

def test_multiple_listeners(realtime):
    """Test multiple listeners for the same collection."""
    callback1 = Mock()
    callback2 = Mock()
    
    # Add two listeners
    id1 = realtime.add_listener('test_collection', callback1)
    id2 = realtime.add_listener('test_collection', callback2)
    
    # Verify both listeners were added
    assert len(realtime.listeners['test_collection']) == 2
    
    # Remove one listener
    realtime.remove_listener(id1)
    
    # Verify one listener remains
    assert len(realtime.listeners['test_collection']) == 1
    assert id2 in [lid for lid, _ in realtime.listeners['test_collection']]

def test_listener_filters(realtime, mock_callback):
    """Test adding a listener with filters."""
    filters = {'field': 'value'}
    
    with patch('google.cloud.firestore.CollectionReference.where') as mock_where:
        # Add a listener with filters
        realtime.add_listener('test_collection', mock_callback, filters)
        
        # Verify filters were applied
        mock_where.assert_called_once_with('field', '==', 'value')

def test_on_snapshot(realtime, mock_callback):
    """Test snapshot handling."""
    # Add a listener
    realtime.add_listener('test_collection', mock_callback)
    
    # Create mock snapshot data
    mock_doc = Mock()
    mock_doc.reference.parent.id = 'test_collection'
    mock_doc.to_dict.return_value = {'id': 'test_id', 'data': 'test_data'}
    
    mock_changes = Mock()
    mock_changes.added = [mock_doc]
    mock_changes.modified = []
    mock_changes.removed = []
    
    # Call _on_snapshot
    realtime._on_snapshot([mock_doc], mock_changes, None)
    
    # Verify callback was called with correct data
    mock_callback.assert_called_once_with({
        'added': [{'id': 'test_id', 'data': 'test_data'}],
        'modified': [],
        'removed': []
    })

def test_error_handling(realtime, mock_callback):
    """Test error handling in snapshot processing."""
    # Add a listener
    realtime.add_listener('test_collection', mock_callback)
    
    # Create mock snapshot with error
    mock_doc = Mock()
    mock_doc.reference.parent.id = 'test_collection'
    mock_doc.to_dict.side_effect = Exception('Test error')
    
    mock_changes = Mock()
    mock_changes.added = [mock_doc]
    mock_changes.modified = []
    mock_changes.removed = []
    
    # Call _on_snapshot - should not raise exception
    realtime._on_snapshot([mock_doc], mock_changes, None)
    
    # Verify callback was not called
    mock_callback.assert_not_called()

def test_concurrent_access(realtime):
    """Test concurrent access to listeners."""
    def add_listeners():
        for i in range(10):
            realtime.add_listener('test_collection', Mock())
    
    # Create multiple threads adding listeners
    threads = [threading.Thread(target=add_listeners) for _ in range(5)]
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify all listeners were added correctly
    assert len(realtime.listeners['test_collection']) == 50

def test_remove_nonexistent_listener(realtime):
    """Test removing a nonexistent listener."""
    assert not realtime.remove_listener('nonexistent_id')

def test_multiple_collections(realtime, mock_callback):
    """Test listeners for multiple collections."""
    # Add listeners for different collections
    id1 = realtime.add_listener('collection1', mock_callback)
    id2 = realtime.add_listener('collection2', mock_callback)
    
    # Verify listeners were added to correct collections
    assert id1 in [lid for lid, _ in realtime.listeners['collection1']]
    assert id2 in [lid for lid, _ in realtime.listeners['collection2']]
    
    # Remove one listener
    realtime.remove_listener(id1)
    
    # Verify only one collection remains
    assert 'collection1' not in realtime.listeners
    assert 'collection2' in realtime.listeners 