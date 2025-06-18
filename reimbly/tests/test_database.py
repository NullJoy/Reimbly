import pytest
from unittest.mock import Mock, patch
from datetime import datetime, UTC
from typing import Dict, Any, List

from reimbly.tools.database import FirestoreDB
from reimbly.shared_libraries.models import Case, UserProfile, DecisionLog, Attachment

# Patch FirestoreDB.__init__ to avoid real Firestore connection
def fake_init(self):
    from datetime import datetime, UTC
    from unittest.mock import Mock

    self.db = Mock()
    self.client = self.db

    # ---- Mock Case Document ----
    mock_case_doc = Mock()
    mock_case_doc.id = "test_case_1"
    mock_case_doc.exists = True
    mock_case_doc.to_dict.return_value = {
        'case_id': 'test_case_1',
        'user_id': 'user_1',
        'submitted_at': datetime.now(UTC),
        'status': 'submitted',
        'amount': 100.0,
        'currency': 'USD',
        'category': 'travel',
        'justification': 'Test justification',
        'reimburse_card_number': '1234-5678-9012-3456',
        'reviewer_route': ['manager_1'],
        'decision_log': [{
            'actor_id': 'user_1',
            'action': 'submit',
            'timestamp': datetime.now(UTC),
            'comments': 'Test comment'
        }],
        'attachments': [{
            'type': 'receipt',
            'name': 'test_receipt.pdf',
            'url': 'https://example.com/receipt.pdf'
        }],
        'last_updated': datetime.now(UTC)
    }
    mock_case_doc.get.return_value = mock_case_doc

    # ---- Mock User Document ----
    mock_user_doc = Mock()
    mock_user_doc.id = "user_1"
    mock_user_doc.exists = True
    mock_user_doc.to_dict.return_value = {
        'user_id': 'user_1',
        'name': 'Test User',
        'email': 'test@example.com',
        'direct_manager_id': 'manager_1',
        'department': 'Engineering',
        'location': 'New York',
        'default_card_number': '1234-5678-9012-3456',
        'cases': ['test_case_1']
    }
    mock_user_doc.get.return_value = mock_user_doc

    # ---- Mock Reimbursement Collection ----
    reimbursement_collection = Mock()
    reimbursement_collection.document.return_value = mock_case_doc
    reimbursement_collection.where.return_value = reimbursement_collection
    reimbursement_collection.stream.return_value = [mock_case_doc]

    # ---- Mock User Collection ----
    user_collection = Mock()
    user_collection.document.return_value = mock_user_doc
    user_collection.where.return_value = user_collection
    user_collection.stream.return_value = [mock_user_doc]

    # ---- Routing by collection name ----
    def collection_side_effect(name):
        if name == 'reimbursement_requests':
            return reimbursement_collection
        elif name == 'users':
            return user_collection
        return Mock()

    self.db.collection.side_effect = collection_side_effect

    # ---- Mock Transaction ----
    mock_transaction = Mock()
    mock_transaction._max_attempts = 5
    mock_transaction._read_only = False
    mock_transaction.update.return_value = None
    self.db.transaction.return_value = mock_transaction

    # ---- Mock Batch ----
    mock_batch = Mock()
    mock_batch.set.return_value = None
    mock_batch.commit.return_value = ['test_case_1']
    self.db.batch.return_value = mock_batch

@pytest.fixture(autouse=True)
def patch_firestore_init():
    with patch.object(FirestoreDB, "__init__", fake_init):
        yield

@pytest.fixture
def db():
    """Create a FirestoreDB instance with mocked client and clear after"""
    db_instance = FirestoreDB()
    yield db_instance

    # Teardown: clear mock state (safe for mock-based testing)
    db_instance.db.reset_mock()
    
    # Clear all mock collections
    for collection_name in ['reimbursement_requests', 'users']:
        collection = db_instance.db.collection(collection_name)
        collection.reset_mock()
        collection.document.reset_mock()
        collection.where.reset_mock()
        collection.stream.reset_mock()

@pytest.fixture
def sample_case():
    """Create a sample Case object for testing"""
    return Case(
        case_id='test_case_1',
        user_id='user_1',
        submitted_at=datetime.now(UTC),
        status='submitted',
        amount=100.0,
        currency='USD',
        category='travel',
        justification='Test justification',
        reimburse_card_number='1234-5678-9012-3456',
        reviewer_route=['manager_1'],
        decision_log=[
            DecisionLog(
                actor_id='user_1',
                action='submit',
                timestamp=datetime.now(UTC),
                comments='Test comment'
            )
        ],
        attachments=[
            Attachment(
                type='receipt',
                name='test_receipt.pdf',
                url='https://example.com/receipt.pdf'
            )
        ],
        last_updated=datetime.now(UTC)
    )

@pytest.fixture
def sample_user():
    """Create a sample UserProfile object for testing"""
    return UserProfile(
        user_id='user_1',
        name='Test User',
        email='test@example.com',
        direct_manager_id='manager_1',
        department='Engineering',
        location='New York',
        default_card_number='1234-5678-9012-3456',
        cases=['test_case_1']
    )

def test_create_reimbursement_request(db, sample_case):
    """Test creating a new reimbursement request"""
    request_id = db.create_reimbursement_request(sample_case)
    assert request_id is not None
    assert isinstance(request_id, str)

def test_get_reimbursement_request(db, sample_case):
    """Test retrieving a reimbursement request"""
    case = db.get_reimbursement_request("test_case_1")
    assert case is not None
    assert case.case_id == sample_case.case_id
    assert case.user_id == sample_case.user_id

def test_update_reimbursement_request(db, sample_case):
    """Test updating a reimbursement request"""
    sample_case.status = "pending_approval"
    success = db.update_reimbursement_request("test_case_1", sample_case)
    assert success is True

def test_get_pending_approvals(db, sample_case):
    """Test getting pending approvals for an approver"""
    approvals = db.get_pending_approvals("manager_1")
    assert len(approvals) > 0
    assert approvals[0].case_id == sample_case.case_id

def test_create_user(db, sample_user):
    """Test creating a new user"""
    user_id = db.create_user(sample_user)
    assert user_id is not None
    assert isinstance(user_id, str)

def test_get_user(db, sample_user):
    """Test retrieving a user"""
    user = db.get_user("user_1")
    assert user is not None
    assert user.user_id == sample_user.user_id
    assert user.name == sample_user.name

def test_update_user(db, sample_user):
    """Test updating a user"""
    sample_user.department = "Product"
    success = db.update_user("user_1", sample_user)
    assert success is True

def test_batch_create_cases(db, sample_case):
    """Test batch creating multiple cases"""
    cases = [sample_case]
    case_ids = db.batch_create_cases(cases)
    assert len(case_ids) == len(cases)
    assert all(isinstance(case_id, str) for case_id in case_ids)

def test_query_cases_by_field(db, sample_case):
    """Test querying cases by field"""
    cases = db.query_cases_by_field("status", "submitted")
    assert len(cases) > 0
    assert cases[0].case_id == sample_case.case_id

def test_error_handling_create_request(db, sample_case):
    """Test error handling when creating a request fails"""
    with patch.object(db.db.collection('reimbursement_requests').document(), 'set', side_effect=Exception("Test error")):
        with pytest.raises(Exception):
            db.create_reimbursement_request(sample_case)

def test_error_handling_get_request(db):
    """Test error handling when getting a request fails"""
    with patch.object(db.db.collection('reimbursement_requests').document(), 'get', side_effect=Exception("Test error")):
        with pytest.raises(Exception):
            db.get_reimbursement_request("test_case_1")

def test_error_handling_update_request(db, sample_case):
    """Test error handling when updating a request fails"""
    with patch.object(db.db.collection('reimbursement_requests').document(), 'get', side_effect=Exception("Test error")):
        with pytest.raises(Exception):
            db.update_reimbursement_request("test_case_1", sample_case)

def test_nonexistent_request(db):
    """Test handling of nonexistent request"""
    with patch.object(db.db.collection('reimbursement_requests').document(), 'get', return_value=Mock(exists=False)):
        result = db.get_reimbursement_request("nonexistent_case")
        assert result is None

def test_nonexistent_user(db):
    """Test handling of nonexistent user"""
    with patch.object(db.db.collection('users').document(), 'get', return_value=Mock(exists=False)):
        result = db.get_user("nonexistent_user")
        assert result is None

def test_transaction_failure(db, sample_case):
    """Test handling of transaction failure"""
    with patch.object(db.db, 'transaction', side_effect=Exception("Transaction failed")):
        with pytest.raises(Exception):
            db.update_reimbursement_request("test_case_1", sample_case)

def test_batch_operation_failure(db, sample_case):
    """Test handling of batch operation failure"""
    with patch.object(db.db, 'batch', side_effect=Exception("Batch operation failed")):
        with pytest.raises(Exception):
            db.batch_create_cases([sample_case])

def test_query_failure(db):
    """Test handling of query failure"""
    with patch.object(db.db.collection('reimbursement_requests'), 'where', side_effect=Exception("Query failed")):
        with pytest.raises(Exception):
            db.query_cases_by_field("status", "submitted") 