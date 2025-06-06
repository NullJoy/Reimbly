import unittest
from reimbly import (
    process_reimbursement,
    collect_request_info,
    validate_policy,
    review_request,
    get_pending_approvals,
    generate_report
)

class TestReimbursementAgents(unittest.TestCase):
    def setUp(self):
        self.valid_request = {
            "action": "submit",
            "data": {
                "category": "travel",
                "amount": 2500,  # Increased to trigger medium approval route
                "justification": "Business trip to client meeting",
                "supporting_material": ["receipt", "itinerary"],
                "user_info": {
                    "user_id": "user123",
                    "user_org": "Engineering",
                    "location": "New York"
                },
                "card_info": {
                    "card_number": "****1234",
                    "card_type": "credit",
                    "expiry_date": "12/25"
                }
            }
        }

    def test_request_submission(self):
        result = process_reimbursement(self.valid_request)
        self.assertEqual(result["status"], "success")
        self.assertIn("request_id", result)
        self.assertIn("approval_route", result)
        self.assertIn("direct_manager", result["approval_route"])
        self.assertIn("department_head", result["approval_route"])

    def test_invalid_request(self):
        invalid_request = {
            "action": "submit",
            "data": {
                "category": "invalid_category",
                "amount": 800
            }
        }
        result = process_reimbursement(invalid_request)
        self.assertEqual(result["status"], "error")

    def test_approval_flow(self):
        # First submit a request
        submit_result = process_reimbursement(self.valid_request)
        request_id = submit_result["request_id"]

        # Then approve it as direct manager
        approval_request = {
            "action": "approve",
            "data": {
                "action": "approve",
                "approver_id": "direct_manager",
                "request_id": request_id,
                "comment": "Approved"
            }
        }
        approval_result = process_reimbursement(approval_request)
        self.assertEqual(approval_result["status"], "success")
        self.assertEqual(approval_result["request_status"], "pending")  # Still pending because department_head needs to approve

    def test_reporting(self):
        # First submit a request to have some data
        process_reimbursement(self.valid_request)

        report_request = {
            "action": "report",
            "data": {
                "report_type": "summary",
                "filters": {
                    "category": "travel"
                }
            }
        }
        report_result = process_reimbursement(report_request)
        self.assertEqual(report_result["status"], "success")
        self.assertIn("data", report_result)
        self.assertIn("total_amount", report_result["data"])

    def test_rejection_flow(self):
        """Test request rejection"""
        # First submit a request
        submit_result = process_reimbursement(self.valid_request)
        request_id = submit_result["request_id"]

        # Then reject it as direct manager
        rejection_request = {
            "action": "approve",
            "data": {
                "action": "reject",
                "approver_id": "direct_manager",
                "request_id": request_id,
                "comment": "Rejected due to insufficient documentation"
            }
        }
        rejection_result = process_reimbursement(rejection_request)
        self.assertEqual(rejection_result["status"], "success")
        self.assertEqual(rejection_result["request_status"], "rejected")

    def test_pending_approvals(self):
        """Test getting pending approvals for an approver"""
        # First submit a request
        submit_result = process_reimbursement(self.valid_request)
        request_id = submit_result["request_id"]

        # Get pending approvals for direct manager
        pending = get_pending_approvals("direct_manager")
        self.assertEqual(pending["status"], "success")
        self.assertIn("pending_approvals", pending)
        self.assertIn(request_id, pending["pending_approvals"])

    def test_invalid_action(self):
        """Test handling of invalid action"""
        invalid_action = {
            "action": "invalid_action",
            "data": {}
        }
        result = process_reimbursement(invalid_action)
        self.assertEqual(result["status"], "error")
        self.assertIn("error_message", result)

if __name__ == '__main__':
    unittest.main() 