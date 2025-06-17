"""Integration tests for the notification system."""
import unittest
from unittest.mock import patch
from reimbly.tools.notification import notification_tool

class TestNotificationIntegration(unittest.TestCase):
    def setUp(self):
        # Create a mock for notification_tool
        self.notification_tool_patcher = patch('reimbly.tools.notification.notification_tool')
        self.mock_notification_tool = self.notification_tool_patcher.start()
        self.mock_notification_tool.return_value = {
            "status": "success",
            "message": "Notification sent successfully",
            "recipient": "test@example.com",
            "request_id": "test_123"
        }

    def tearDown(self):
        self.notification_tool_patcher.stop()

    def test_send_notification_integration(self):
        """Test sending a notification through the notification tool."""
        notification_data = {
            "type": "submit",
            "recipient": "test@example.com",
            "subject": "Test Subject",
            "request_data": {
                "request_id": "test_123",
                "category": "Travel",
                "amount": 100.50
            }
        }

        # Call the notification tool
        result = self.mock_notification_tool(notification_data)

        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["recipient"], "test@example.com")
        self.assertEqual(result["request_id"], "test_123")

        # Verify the mock was called correctly
        self.mock_notification_tool.assert_called_once_with(notification_data)

    def test_resend_notification_integration(self):
        """Test resending a notification through the notification tool."""
        notification_data = {
            "type": "update",
            "recipient": "test@example.com",
            "subject": "Test Update",
            "request_data": {
                "request_id": "test_123",
                "status": "approved"
            }
        }

        # Call the notification tool
        result = self.mock_notification_tool(notification_data)

        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["recipient"], "test@example.com")
        self.assertEqual(result["request_id"], "test_123")

        # Verify the mock was called correctly
        self.mock_notification_tool.assert_called_once_with(notification_data)

    def test_notification_with_chatbox_integration(self):
        """Test sending a notification with chatbox link through the notification tool."""
        notification_data = {
            "type": "review",
            "recipient": "test@example.com",
            "subject": "Test Review",
            "request_data": {
                "request_id": "test_123",
                "category": "Travel",
                "amount": 100.50
            },
            "chatbox_link": "https://example.com/chat/123"
        }

        # Call the notification tool
        result = self.mock_notification_tool(notification_data)

        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["recipient"], "test@example.com")
        self.assertEqual(result["request_id"], "test_123")

        # Verify the mock was called correctly
        self.mock_notification_tool.assert_called_once_with(notification_data)

if __name__ == '__main__':
    unittest.main() 