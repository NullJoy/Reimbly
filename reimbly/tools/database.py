from google.cloud import firestore
from typing import Dict, Any, Optional, List
import os
from datetime import UTC, datetime
import logging
from ..shared_libraries.models import Case, UserProfile, case_to_dict, user_profile_to_dict, dict_to_case, dict_to_user_profile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirestoreDB:
    def __init__(self):
        """Initialize Firestore client"""
        try:
            # Get the environment (default to dev)
            env = os.getenv('REIMBLY_ENV', 'dev')
            
            # Construct the path to the key file
            key_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                  'config', env, 'reimbly-dev-key.json')
            
            # Initialize Firestore client with credentials
            self.client = firestore.Client.from_service_account_json(key_file)
            self.db = self.client
            logger.info(f"Successfully connected to Firestore using {key_file}")
        except Exception as e:
            logger.error(f"Failed to connect to Firestore: {str(e)}")
            raise

    # Reimbursement Request Operations
    def create_reimbursement_request(self, case: Case) -> str:
        """Create a new reimbursement request"""
        try:
            logger.info(f"Starting to create reimbursement request for case_id: {case.case_id}")
            logger.debug(f"Case data to be saved: {case_to_dict(case)}")
            
            collection = self.db.collection('reimbursement_requests')
            request_data = case_to_dict(case)
            request_data['created_at'] = datetime.now(UTC)
            request_data['updated_at'] = datetime.now(UTC)
            
            # Use the case_id from the Case object
            doc_ref = collection.document(case.case_id)
            logger.debug(f"Document reference created with path: {doc_ref.path}")
            
            # Save to Firestore
            doc_ref.set(request_data)
            logger.info(f"Successfully saved case {case.case_id} to Firestore")
            
            # Verify the save
            saved_doc = doc_ref.get()
            if saved_doc.exists:
                logger.info(f"Verified case {case.case_id} exists in database")
                logger.debug(f"Saved document data: {saved_doc.to_dict()}")
            else:
                logger.error(f"Failed to verify case {case.case_id} in database - document not found")
                raise Exception(f"Document verification failed for case {case.case_id}")
            
            return case.case_id
        except Exception as e:
            logger.error(f"Error creating reimbursement request: {str(e)}")
            logger.exception("Full traceback:")
            raise

    def get_reimbursement_request(self, request_id: str) -> Optional[Case]:
        """Get a reimbursement request by ID"""
        try:
            doc_ref = self.db.collection('reimbursement_requests').document(request_id)
            doc = doc_ref.get()
            if doc.exists:
                return dict_to_case(doc.to_dict())
            return None
        except Exception as e:
            logger.error(f"Error retrieving reimbursement request: {str(e)}")
            raise

    def update_reimbursement_request(self, request_id: str, case: Case) -> bool:
        """Update a reimbursement request"""
        try:
            doc_ref = self.db.collection('reimbursement_requests').document(request_id)
            update_data = case_to_dict(case)
            update_data['updated_at'] = datetime.now(UTC)
            
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

    def get_pending_approvals(self, approver_id: str) -> List[Case]:
        """Get all pending approvals for an approver"""
        try:
            collection = self.db.collection('reimbursement_requests')
            query = collection.where('reviewer_route', 'array_contains', approver_id).where('status', '==', 'pending_review')
            docs = query.stream()
            return [dict_to_case(doc.to_dict()) for doc in docs]
        except Exception as e:
            logger.error(f"Error retrieving pending approvals: {str(e)}")
            raise

    # User Operations
    def create_user(self, profile: UserProfile) -> str:
        """Create a new user"""
        try:
            collection = self.db.collection('users')
            user_data = user_profile_to_dict(profile)
            user_data['created_at'] = datetime.now(UTC)
            user_data['updated_at'] = datetime.now(UTC)
            
            # Create a new document with auto-generated ID
            doc_ref = collection.document()
            user_data['user_id'] = doc_ref.id
            doc_ref.set(user_data)
            
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get a user by ID"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                return dict_to_user_profile(doc.to_dict())
            return None
        except Exception as e:
            logger.error(f"Error retrieving user: {str(e)}")
            raise

    def update_user(self, user_id: str, profile: UserProfile) -> bool:
        """Update a user"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            update_data = user_profile_to_dict(profile)
            update_data['updated_at'] = datetime.now(UTC)
            
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
    def batch_create_cases(self, cases: List[Case]) -> List[str]:
        """Create multiple case documents in a batch"""
        try:
            logger.info(f"Starting batch creation of {len(cases)} cases")
            logger.debug(f"Cases to be saved: {[case.case_id for case in cases]}")
            
            batch = self.db.batch()
            case_ids = []
            
            for case in cases:
                logger.debug(f"Preparing case {case.case_id} for batch save")
                doc_ref = self.db.collection('reimbursement_requests').document(case.case_id)
                case_data = case_to_dict(case)
                case_data['created_at'] = datetime.now(UTC)
                case_data['updated_at'] = datetime.now(UTC)
                batch.set(doc_ref, case_data)
                case_ids.append(case.case_id)
                logger.debug(f"Added case {case.case_id} to batch")
            
            # Commit the batch
            logger.info("Committing batch to Firestore")
            batch.commit()
            logger.info(f"Successfully committed batch with {len(case_ids)} cases")
            
            # Verify the saves
            for case_id in case_ids:
                doc_ref = self.db.collection('reimbursement_requests').document(case_id)
                saved_doc = doc_ref.get()
                if saved_doc.exists:
                    logger.info(f"Verified case {case_id} exists in database")
                    logger.debug(f"Saved document data for {case_id}: {saved_doc.to_dict()}")
                else:
                    logger.error(f"Failed to verify case {case_id} in database - document not found")
                    raise Exception(f"Document verification failed for case {case_id}")
            
            return case_ids
        except Exception as e:
            logger.error(f"Error in batch creation: {str(e)}")
            logger.exception("Full traceback:")
            raise

    def query_cases_by_field(self, field: str, value: Any) -> List[Case]:
        """Query case documents by field value"""
        try:
            collection = self.db.collection('reimbursement_requests')
            query = collection.where(field, '==', value)
            docs = query.stream()
            return [dict_to_case(doc.to_dict()) for doc in docs]
        except Exception as e:
            logger.error(f"Error querying by field: {str(e)}")
            raise

# Create a singleton instance
db = FirestoreDB() 