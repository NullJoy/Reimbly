"""Tests for the notification system."""
import os
import pytest
from unittest.mock import patch, MagicMock
from reimbly.tools.notification import (
    validate_email,
    format_notification_subject,
    format_notification_body,
    format_progress_bar,
    send_notification,
    resend_case_update_email,
    SENDGRID_AVAILABLE,
    send_notification_tool,
    resend_case_update_email_tool
)

# Test data
VALID_EMAIL = "test@example.com"
INVALID_EMAIL = "invalid-email"
EMPTY_EMAIL = ""
TEST_REQUEST_DATA = {
    "request_id": "test_123",
    "category": "Travel",
    "amount": 100.50,
    "status": "pending",
    "justification": "Test justification",
    "approval_route": ["approver1", "approver2"],
    "reviews": [
        {"approver_id": "approver1", "action": "approve"}
    ]
}

@pytest.fixture
def mock_sendgrid():
    """Mock SendGrid client."""
    with patch('reimbly.tools.notification.SendGridAPIClient') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.send.return_value = MagicMock(status_code=202)
        yield mock_instance

@pytest.fixture
def mock_sendgrid_available():
    """Mock SendGrid availability."""
    with patch('reimbly.tools.notification.SENDGRID_AVAILABLE', True):
        yield

def test_validate_email():
    """Test email validation."""
    assert validate_email(VALID_EMAIL) is True
    assert validate_email(INVALID_EMAIL) is False
    assert validate_email(EMPTY_EMAIL) is False
    assert validate_email(None) is False

def test_format_notification_subject():
    """Test notification subject formatting."""
    # Test different notification types
    assert "Submitted" in format_notification_subject("submit", TEST_REQUEST_DATA)
    assert "Update" in format_notification_subject("update", TEST_REQUEST_DATA)
    assert "Review" in format_notification_subject("review", TEST_REQUEST_DATA)
    assert "Completed" in format_notification_subject("complete", TEST_REQUEST_DATA)
    
    # Test with missing request_id
    data_without_id = TEST_REQUEST_DATA.copy()
    del data_without_id["request_id"]
    assert "Unknown" in format_notification_subject("submit", data_without_id)

def test_format_notification_body():
    """Test notification body formatting."""
    body = format_notification_body("submit", TEST_REQUEST_DATA)
    assert TEST_REQUEST_DATA["request_id"] in body
    assert TEST_REQUEST_DATA["category"] in body
    assert str(TEST_REQUEST_DATA["amount"]) in body
    assert TEST_REQUEST_DATA["status"] in body

def test_format_progress_bar():
    """Test progress bar formatting."""
    progress = format_progress_bar(TEST_REQUEST_DATA)
    assert "Case submitted" in progress
    assert "approver1" in progress
    assert "approver2" in progress
    assert "Case completed" in progress
    assert "✅" in progress  # For approved review

@pytest.mark.parametrize("notification_type", ["submit", "update", "review", "complete"])
def test_send_notification_success(notification_type, mock_sendgrid, mock_sendgrid_available):
    """Test successful notification sending for different types."""
    with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_key'}):
        notification_data = {
            "type": notification_type,
            "recipient": VALID_EMAIL,
            "subject": "Test Subject",
            "request_data": TEST_REQUEST_DATA
        }
        
        result = send_notification(notification_data)
        assert result["status"] == "success"
        assert result["recipient"] == VALID_EMAIL
        assert result["request_id"] == TEST_REQUEST_DATA["request_id"]
        
        # Verify SendGrid was called correctly
        mock_sendgrid.send.assert_called_once()

def test_send_notification_invalid_email():
    """Test notification sending with invalid email."""
    notification_data = {
        "type": "submit",
        "recipient": INVALID_EMAIL,
        "subject": "Test Subject",
        "request_data": TEST_REQUEST_DATA
    }
    
    result = send_notification(notification_data)
    assert result["status"] == "error"
    assert "Invalid recipient email format" in result["error_message"]

def test_send_notification_missing_api_key():
    """Test notification sending without API key."""
    # Do not mock SendGrid for this test, so the real error path is triggered
    with patch.dict(os.environ, {}, clear=True), \
         patch('reimbly.tools.notification.SENDGRID_AVAILABLE', True):
        notification_data = {
            "type": "submit",
            "recipient": VALID_EMAIL,
            "subject": "Test Subject",
            "request_data": TEST_REQUEST_DATA
        }
        result = send_notification(notification_data)
        assert result["status"] == "error"
        assert "HTTP Error 403" in result["error_message"]

def test_resend_case_update_email(mock_sendgrid, mock_sendgrid_available):
    """Test resending case update email."""
    with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_key'}):
        result = resend_case_update_email(
            case_id="test_123",
            case_data=TEST_REQUEST_DATA,
            user_email=VALID_EMAIL
        )
        assert result["status"] == "success"

def test_resend_case_update_email_invalid_data():
    """Test resending case update email with invalid data."""
    # Test with missing case data
    result = resend_case_update_email(
        case_id="test_123",
        case_data=None,
        user_email=VALID_EMAIL
    )
    assert result["status"] == "error"
    assert "Case data not provided" in result["error_message"]
    
    # Test with invalid email
    result = resend_case_update_email(
        case_id="test_123",
        case_data=TEST_REQUEST_DATA,
        user_email=INVALID_EMAIL
    )
    assert result["status"] == "error"
    assert "Invalid email format" in result["error_message"]

def test_notification_tool_configuration():
    """Test notification tool configuration."""
    # Test tool description
    assert "send an email notification" in send_notification_tool.description.lower()
    
    # Test available functions
    assert send_notification_tool.func.__name__ == "send_notification"
    assert resend_case_update_email_tool.func.__name__ == "resend_case_update_email"

def test_notification_tool_function_calls(mock_sendgrid, mock_sendgrid_available):
    """Test notification tool function calls."""
    with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_key'}):
        # Test send_notification function
        notification_data = {
            "type": "submit",
            "recipient": VALID_EMAIL,
            "subject": "Test Subject",
            "request_data": TEST_REQUEST_DATA
        }
        result = send_notification(notification_data)
        assert result["status"] == "success"
        
        # Test resend_case_update_email function
        result = resend_case_update_email(
            case_id="test_123",
            case_data=TEST_REQUEST_DATA,
            user_email=VALID_EMAIL
        )
        assert result["status"] == "success"

@pytest.mark.skipif(not SENDGRID_AVAILABLE, reason="SendGrid package not available")
def test_sendgrid_available():
    """Test that SendGrid is available when the package is installed."""
    assert SENDGRID_AVAILABLE is True 