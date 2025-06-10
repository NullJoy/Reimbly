from google.cloud import firestore
from typing import Dict, Any, Callable, List
import threading
import logging
from datetime import datetime
from .database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealtimeListener:
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}
        self._active_listeners: Dict[str, firestore.Watch] = {}
        self._lock = threading.Lock()

    def add_listener(self, collection: str, callback: Callable[[Dict[str, Any]], None], 
                    filters: Dict[str, Any] = None) -> str:
        """Add a real-time listener for a collection.
        
        Args:
            collection (str): The collection to listen to
            callback (Callable): Function to call when data changes
            filters (Dict[str, Any], optional): Filters to apply to the query
            
        Returns:
            str: Listener ID
        """
        listener_id = f"{collection}_{datetime.now().timestamp()}"
        
        with self._lock:
            if collection not in self.listeners:
                self.listeners[collection] = []
            self.listeners[collection].append((listener_id, callback))
            
            # Start listening if this is the first listener for this collection
            if collection not in self._active_listeners:
                self._start_listener(collection, filters)
        
        return listener_id

    def remove_listener(self, listener_id: str) -> bool:
        """Remove a real-time listener.
        
        Args:
            listener_id (str): The ID of the listener to remove
            
        Returns:
            bool: True if listener was removed, False otherwise
        """
        with self._lock:
            for collection, listeners in self.listeners.items():
                for i, (lid, _) in enumerate(listeners):
                    if lid == listener_id:
                        listeners.pop(i)
                        
                        # Stop listening if this was the last listener
                        if not listeners:
                            self._stop_listener(collection)
                            del self.listeners[collection]
                        
                        return True
        return False

    def _start_listener(self, collection: str, filters: Dict[str, Any] = None):
        """Start listening to a collection."""
        try:
            query = db.db.collection(collection)
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    query = query.where(field, "==", value)
            
            # Start the listener
            listener = query.on_snapshot(self._on_snapshot)
            self._active_listeners[collection] = listener
            logger.info(f"Started listening to collection: {collection}")
        except Exception as e:
            logger.error(f"Error starting listener for {collection}: {str(e)}")
            raise

    def _stop_listener(self, collection: str):
        """Stop listening to a collection."""
        if collection in self._active_listeners:
            self._active_listeners[collection].unsubscribe()
            del self._active_listeners[collection]
            logger.info(f"Stopped listening to collection: {collection}")

    def _on_snapshot(self, doc_snapshot, changes, read_time):
        """Handle Firestore snapshot updates."""
        try:
            # Get the collection name from the first document
            if doc_snapshot:
                collection = doc_snapshot[0].reference.parent.id
                
                # Notify all listeners for this collection
                if collection in self.listeners:
                    for _, callback in self.listeners[collection]:
                        try:
                            # Convert changes to a more usable format
                            updates = {
                                'added': [doc.to_dict() for doc in changes.added],
                                'modified': [doc.to_dict() for doc in changes.modified],
                                'removed': [doc.to_dict() for doc in changes.removed]
                            }
                            callback(updates)
                        except Exception as e:
                            logger.error(f"Error in listener callback: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing snapshot: {str(e)}")

# Create a singleton instance
realtime = RealtimeListener() 