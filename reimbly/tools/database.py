from google.cloud import firestore
from typing import Dict, Any, Optional
import os
from datetime import datetime
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirestoreDB:
    def __init__(self):
        """Initialize Firestore client"""
        try:
            # Get the environment (default to dev)
            env = os.getenv('REIMBLY_ENV', 'dev')
            
            # For testing, use in-memory client
            if os.getenv('TESTING', 'false').lower() == 'true':
                self.client = firestore.Client(project='test-project')
                self.db = self.client
                logger.info("Using in-memory Firestore client for testing")
                return
            
            # Construct the path to the key file
            key_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                  'config', env, 'reimbly-dev-key.json')
            
            if not os.path.exists(key_file):
                logger.warning(f"Key file not found at {key_file}, using default credentials")
                self.client = firestore.Client()
            else:
                # Initialize Firestore client with credentials
                self.client = firestore.Client.from_service_account_json(key_file)
            
            self.db = self.client
            logger.info(f"Successfully connected to Firestore")
        except Exception as e:
            logger.error(f"Failed to connect to Firestore: {str(e)}")
            raise

    # Reimbursement Request Operations
    def create_reimbursement_request(self, request_data: Dict[str, Any]) -> str:
        """Create a new reimbursement request"""
        try:
            collection = self.db.collection('reimbursement_requests')
            request_data['created_at'] = datetime.utcnow()
            request_data['updated_at'] = datetime.utcnow()
            
            # Use the provided request_id instead of generating a new one
            request_id = request_data.get('request_id')
            if not request_id:
                raise ValueError("Request ID is required")
                
            # Create document with the provided request_id
            doc_ref = collection.document(request_id)
            doc_ref.set(request_data)
            
            return request_id
        except Exception as e:
            logger.error(f"Error creating reimbursement request: {str(e)}")
            raise

    def get_reimbursement_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a reimbursement request by ID"""
        try:
            doc_ref = self.db.collection('reimbursement_requests').document(request_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Error retrieving reimbursement request: {str(e)}")
            raise

    def update_reimbursement_request(self, request_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a reimbursement request"""
        try:
            doc_ref = self.db.collection('reimbursement_requests').document(request_id)
            update_data['updated_at'] = datetime.utcnow()
            
            # Use transaction to ensure atomic updates
            transaction = self.db.transaction()
            
            @firestore.transactional
            def update_in_transaction(transaction, doc_ref, update_data):
                snapshot = doc_ref.get(transaction=transaction)
                if not snapshot.exists:
                    return False
                transaction.update(doc_ref, update_data)
                return True
            
            return update_in_transaction(transaction, doc_ref, update_data)
        except Exception as e:
            logger.error(f"Error updating reimbursement request: {str(e)}")
            raise

    def get_pending_approvals(self, approver_id: str) -> list:
        """Get all pending approvals for an approver"""
        try:
            collection = self.db.collection('reimbursement_requests')
            query = collection.where('approval_route', '==', approver_id).where('status', '==', 'pending')
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error retrieving pending approvals: {str(e)}")
            raise

    # User Operations
    def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user"""
        try:
            collection = self.db.collection('users')
            user_data['created_at'] = datetime.utcnow()
            user_data['updated_at'] = datetime.utcnow()
            
            # Create a new document with auto-generated ID
            doc_ref = collection.document()
            user_data['user_id'] = doc_ref.id
            doc_ref.set(user_data)
            
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Error retrieving user: {str(e)}")
            raise

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a user"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            update_data['updated_at'] = datetime.utcnow()
            
            # Use transaction to ensure atomic updates
            transaction = self.db.transaction()
            
            @firestore.transactional
            def update_in_transaction(transaction, doc_ref, update_data):
                snapshot = doc_ref.get(transaction=transaction)
                if not snapshot.exists:
                    return False
                transaction.update(doc_ref, update_data)
                return True
            
            return update_in_transaction(transaction, doc_ref, update_data)
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise

    # Additional Firestore-specific operations
    def batch_create(self, collection_name: str, items: list[Dict[str, Any]]) -> list[str]:
        """Create multiple documents in a batch"""
        try:
            batch = self.db.batch()
            doc_refs = []
            
            for item in items:
                doc_ref = self.db.collection(collection_name).document()
                item['created_at'] = datetime.utcnow()
                item['updated_at'] = datetime.utcnow()
                item['id'] = doc_ref.id
                batch.set(doc_ref, item)
                doc_refs.append(doc_ref.id)
            
            batch.commit()
            return doc_refs
        except Exception as e:
            logger.error(f"Error in batch creation: {str(e)}")
            raise

    def query_by_field(self, collection_name: str, field: str, value: Any) -> list[Dict[str, Any]]:
        """Query documents by field value"""
        try:
            collection = self.db.collection(collection_name)
            query = collection.where(field, '==', value)
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error querying by field: {str(e)}")
            raise

# Create a singleton instance
db = FirestoreDB() 