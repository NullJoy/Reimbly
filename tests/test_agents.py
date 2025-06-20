import unittest
import time
from reimbly import (
    process_reimbursement,
    collect_request_info,
    validate_policy,
    review_request,
    generate_report
)
from reimbly.root_agent import get_pending_approvals
from reimbly.sub_agents.dashboard.agent import DashboardAgent
from reimbly.sub_agents.review.agent import validate_user_permission
from unittest.mock import patch, MagicMock

class TestReimbursementAgents(unittest.TestCase):
    def setUp(self):
        # Clear global state for test isolation
        from reimbly.root_agent import pending_approvals, reporting_data
        pending_approvals.clear()
        reporting_data.clear()
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
                },
                "travel_dates": {
                    "start": "2024-03-01",
                    "end": "2024-03-03"
                }
            }
        }
        self.dashboard_agent = DashboardAgent()

    def test_request_submission(self):
        """Test request submission flow."""
        with patch('reimbly.sub_agents.request.agent.RequestAgent') as mock_request_agent:
            mock_request_agent.return_value.transfer.return_value = {
                "status": "success",
                "data": {"request_id": "test123"},
                "message": "Request submitted successfully",
                "request_id": "test123"
            }
            # Test request submission
            result = mock_request_agent.return_value.transfer()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["data"]["request_id"], "test123")

    def test_approval_flow(self):
        """Test approval flow."""
        with patch('reimbly.sub_agents.policy.agent.PolicyAgent') as mock_policy_agent:
            mock_policy_agent.return_value.transfer.return_value = {
                "status": "success",
                "approval_route": "manager",
                "message": "Request approved",
                "request_id": "test123"
            }
            # Test approval
            result = mock_policy_agent.return_value.transfer()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["approval_route"], "manager")

    def test_rejection_flow(self):
        """Test rejection flow."""
        with patch('reimbly.sub_agents.policy.agent.PolicyAgent') as mock_policy_agent:
            mock_policy_agent.return_value.transfer.return_value = {
                "status": "success",
                "approval_route": "rejected",
                "message": "Request rejected",
                "request_id": "test123"
            }
            # Test rejection
            result = mock_policy_agent.return_value.transfer()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["approval_route"], "rejected")

    def test_pending_approvals(self):
        """Test pending approvals list."""
        with patch('reimbly.sub_agents.policy.agent.PolicyAgent') as mock_policy_agent:
            mock_policy_agent.return_value.transfer.return_value = {
                "status": "success",
                "pending_approvals": [
                    {"request_id": "req1", "amount": 100},
                    {"request_id": "req2", "amount": 200}
                ],
                "request_id": "test123"
            }
            # Test pending approvals
            result = mock_policy_agent.return_value.transfer()
            self.assertEqual(result["status"], "success")
            self.assertEqual(len(result["pending_approvals"]), 2)

    def test_notification_sending(self):
        """Test notification sending."""
        with patch('reimbly.sub_agents.notification.agent.NotificationAgent') as mock_notification_agent:
            mock_notification_agent.return_value.transfer.return_value = {
                "status": "success",
                "message": "Notification sent",
                "request_id": "test123"
            }
            # Test notification
            result = mock_notification_agent.return_value.transfer()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["message"], "Notification sent")

    def test_review_process(self):
        """Test review process."""
        with patch('reimbly.sub_agents.review.agent.ReviewAgent') as mock_review_agent:
            mock_review_agent.return_value.transfer.return_value = {
                "status": "success",
                "request_status": "approved",
                "updated_data": {"amount": 150},
                "request_id": "test123"
            }
            # Test review
            result = mock_review_agent.return_value.transfer()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["request_status"], "approved")

    def test_reporting(self):
        """Test reporting functionality."""
        with patch('reimbly.sub_agents.reporting.agent.ReportingAgent') as mock_reporting_agent:
            mock_reporting_agent.return_value.transfer.return_value = {
                "status": "success",
                "data": {"total_amount": 1000},
                "request_id": "test123"
            }
            # Test reporting
            result = mock_reporting_agent.return_value.transfer()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["data"]["total_amount"], 1000)

    def test_collect_request_info_validation(self):
        """Test request info collection with validation."""
        with patch('reimbly.sub_agents.request.agent.RequestAgent') as mock_request_agent:
            mock_request_agent.return_value.transfer.return_value = {
                "status": "success",
                "data": {
                    "request_id": "test123",
                    "amount": 100,
                    "category": "travel"
                },
                "message": "Request info collected",
                "request_id": "test123"
            }
            # Test request info collection
            result = mock_request_agent.return_value.transfer()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["data"]["amount"], 100)

    def test_meal_expense_validation(self):
        """Test meal expense validation."""
        with patch('reimbly.sub_agents.policy.agent.PolicyAgent') as mock_policy_agent:
            mock_policy_agent.return_value.transfer.return_value = {
                "status": "success",
                "approval_route": "manager",
                "message": "Meal expense validated",
                "request_id": "test123"
            }
            # Test meal expense validation
            result = mock_policy_agent.return_value.transfer()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["approval_route"], "manager")

    def test_travel_expense_validation(self):
        """Test travel expense validation."""
        with patch('reimbly.sub_agents.policy.agent.PolicyAgent') as mock_policy_agent:
            mock_policy_agent.return_value.transfer.return_value = {
                "status": "success",
                "approval_route": "manager",
                "message": "Travel expense validated",
                "request_id": "test123"
            }
            # Test travel expense validation
            result = mock_policy_agent.return_value.transfer()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["approval_route"], "manager")

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

    def test_invalid_action(self):
        """Test handling of invalid action"""
        invalid_action = {
            "action": "invalid_action",
            "data": {}
        }
        result = process_reimbursement(invalid_action)
        self.assertEqual(result["status"], "error")
        self.assertIn("message", result)

    # New test cases for role-based access control
    def test_user_permissions(self):
        """Test user role permissions"""
        # Test employee permissions
        employee_result = validate_user_permission("user123", "submit")
        self.assertEqual(employee_result["status"], "success")
        self.assertEqual(employee_result["role"], "employee")

        employee_approve_result = validate_user_permission("user123", "approve")
        self.assertEqual(employee_approve_result["status"], "error")
        self.assertIn("cannot approve", employee_approve_result["message"])

        # Test admin permissions
        admin_result = validate_user_permission("admin123", "approve")
        self.assertEqual(admin_result["status"], "success")
        self.assertEqual(admin_result["role"], "admin")

        admin_view_result = validate_user_permission("admin123", "view_all")
        self.assertEqual(admin_view_result["status"], "success")

        # Test manager permissions
        manager_result = validate_user_permission("manager123", "approve")
        self.assertEqual(manager_result["status"], "success")
        self.assertEqual(manager_result["role"], "manager")

        manager_view_result = validate_user_permission("manager123", "view_all")
        self.assertEqual(manager_view_result["status"], "error")
        self.assertIn("cannot view all", manager_view_result["message"])

    # New test cases for category-specific validations
    def test_travel_expense_validation(self):
        """Test travel expense specific validations"""
        travel_request = self.valid_request.copy()
        travel_request["data"]["category"] = "travel"
        
        # Test missing itinerary
        invalid_travel = travel_request.copy()
        invalid_travel["data"]["supporting_material"] = ["receipt"]
        result = process_reimbursement(invalid_travel)
        self.assertEqual(result["status"], "error")
        self.assertIn("itinerary", result["message"].lower())

        # Test missing travel dates (but with itinerary and receipt)
        valid_travel = travel_request.copy()
        valid_travel["data"]["supporting_material"] = ["receipt", "itinerary"]
        valid_travel["data"].pop("travel_dates", None)
        result = process_reimbursement(valid_travel)
        self.assertEqual(result["status"], "error")
        self.assertIn("travel dates", result["message"].lower())

    def test_meal_expense_validation(self):
        """Test meal expense specific validations"""
        meal_request = self.valid_request.copy()
        meal_request["data"].update({
            "category": "meals",
            "meal_date": "2024-03-01",
            "attendees": 4
        })
        
        # Test missing meal date
        invalid_meal = meal_request.copy()
        invalid_meal["data"].pop("meal_date", None)
        result = process_reimbursement(invalid_meal)
        self.assertEqual(result["status"], "error")
        self.assertIn("meal date", result["message"].lower())

        # Test missing attendees (meal date present)
        valid_meal = meal_request.copy()
        valid_meal["data"]["meal_date"] = "2024-03-01"
        valid_meal["data"].pop("attendees", None)
        result = process_reimbursement(valid_meal)
        self.assertEqual(result["status"], "error")
        self.assertIn("attendees", result["message"].lower())

    def test_supply_expense_validation(self):
        """Test supply expense specific validations"""
        supply_request = self.valid_request.copy()
        supply_request["data"].update({
            "category": "supplies",
            "supporting_material": ["invoice", "receipt"],
            "purchase_date": "2024-03-01",
            "vendor": "Office Supplies Inc."
        })
        
        # Test missing invoice
        invalid_supply = supply_request.copy()
        invalid_supply["data"]["supporting_material"] = ["receipt"]
        result = process_reimbursement(invalid_supply)
        self.assertEqual(result["status"], "error")
        self.assertIn("invoice", result["message"].lower())

        # Test missing vendor (invoice present)
        valid_supply = supply_request.copy()
        valid_supply["data"]["supporting_material"] = ["invoice", "receipt"]
        valid_supply["data"].pop("vendor", None)
        result = process_reimbursement(valid_supply)
        self.assertEqual(result["status"], "error")
        self.assertIn("vendor", result["message"].lower())

    # New test cases for dashboard generation
    def test_dashboard_generation(self):
        """Test dashboard HTML generation"""
        test_data = {
            "pending_requests": [
                {
                    "request_id": "req1",
                    "category": "travel",
                    "amount": 1000,
                    "user_info": {"user_id": "user1"},
                    "timestamp": "2024-03-01T10:00:00"
                }
            ],
            "approved_requests": [
                {
                    "request_id": "req2",
                    "category": "meals",
                    "amount": 500,
                    "user_info": {"user_id": "user2"},
                    "timestamp": "2024-03-01T11:00:00"
                }
            ],
            "rejected_requests": [
                {
                    "request_id": "req3",
                    "category": "supplies",
                    "amount": 200,
                    "user_info": {"user_id": "user3"},
                    "timestamp": "2024-03-01T12:00:00"
                }
            ],
            "summary_stats": {
                "total_requests": 3,
                "total_amount": 1700,
                "approval_rate": 33.33
            }
        }
        
        result = self.dashboard_agent.generate_dashboard_html(data=test_data)
        self.assertEqual(result["status"], "success")
        self.assertIn("html", result)
        
        # Verify HTML content
        html = result["html"]
        self.assertIn("Reimbly Admin Dashboard", html)
        self.assertIn("Total Requests", html)
        self.assertIn("Total Amount", html)
        self.assertIn("Pending Requests", html)
        self.assertIn("Approval Rate", html)
        
        # Verify request cards
        self.assertIn("req1", html)  # Pending request
        self.assertIn("req2", html)  # Approved request
        self.assertIn("req3", html)  # Rejected request
        
        # Verify amounts
        self.assertIn("$1,000.00", html)
        self.assertIn("$500.00", html)
        self.assertIn("$200.00", html)

    def test_dashboard_performance(self):
        """Test dashboard generation performance with different data sizes."""
        # Test with small dataset
        small_data = {
            "pending_requests": [
                {
                    "request_id": f"req{i}",
                    "category": "travel",
                    "amount": 1000,
                    "user_info": {"user_id": f"user{i}"},
                    "timestamp": "2024-03-01T10:00:00"
                } for i in range(5)
            ],
            "approved_requests": [
                {
                    "request_id": f"req{i}",
                    "category": "meals",
                    "amount": 500,
                    "user_info": {"user_id": f"user{i}"},
                    "timestamp": "2024-03-01T11:00:00"
                } for i in range(5)
            ],
            "rejected_requests": [
                {
                    "request_id": f"req{i}",
                    "category": "supplies",
                    "amount": 200,
                    "user_info": {"user_id": f"user{i}"},
                    "timestamp": "2024-03-01T12:00:00"
                } for i in range(5)
            ],
            "summary_stats": {
                "total_requests": 15,
                "total_amount": 8500,
                "approval_rate": 33.33
            }
        }

        # Test with medium dataset
        medium_data = small_data.copy()
        medium_data["pending_requests"].extend([
            {
                "request_id": f"req{i}",
                "category": "travel",
                "amount": 1000,
                "user_info": {"user_id": f"user{i}"},
                "timestamp": "2024-03-01T10:00:00"
            } for i in range(5, 20)
        ])

        # Test with large dataset
        large_data = medium_data.copy()
        large_data["pending_requests"].extend([
            {
                "request_id": f"req{i}",
                "category": "travel",
                "amount": 1000,
                "user_info": {"user_id": f"user{i}"},
                "timestamp": "2024-03-01T10:00:00"
            } for i in range(20, 100)
        ])

        # Measure performance for each dataset
        datasets = {
            "small": small_data,
            "medium": medium_data,
            "large": large_data
        }

        results = {}
        for name, data in datasets.items():
            start_time = time.time()
            result = self.dashboard_agent.generate_dashboard_html(data=data)
            end_time = time.time()
            
            results[name] = {
                "time": end_time - start_time,
                "request_count": len(data["pending_requests"]) + 
                               len(data["approved_requests"]) + 
                               len(data["rejected_requests"]),
                "html_size": len(result["html"])
            }
            
            # Verify the result is valid
            self.assertEqual(result["status"], "success")
            self.assertIn("html", result)
            
            # Verify HTML content
            html = result["html"]
            self.assertIn("Reimbly Admin Dashboard", html)
            self.assertIn("Total Requests", html)
            
            # Verify all requests are included
            for request in data["pending_requests"]:
                self.assertIn(request["request_id"], html)
            for request in data["approved_requests"]:
                self.assertIn(request["request_id"], html)
            for request in data["rejected_requests"]:
                self.assertIn(request["request_id"], html)

        # Print performance results
        print("\nDashboard Generation Performance Results:")
        print("=" * 50)
        for name, metrics in results.items():
            print(f"\n{name.upper()} Dataset:")
            print(f"Number of requests: {metrics['request_count']}")
            print(f"Generation time: {metrics['time']:.3f} seconds")
            print(f"HTML size: {metrics['html_size']} bytes")
            print(f"Average time per request: {metrics['time']/metrics['request_count']:.3f} seconds")

        # Performance assertions
        self.assertLess(results["small"]["time"], 1.0, "Small dataset should generate in under 1 second")
        self.assertLess(results["medium"]["time"], 2.0, "Medium dataset should generate in under 2 seconds")
        self.assertLess(results["large"]["time"], 5.0, "Large dataset should generate in under 5 seconds")

    def test_dashboard_memory_usage(self):
        """Test dashboard generation memory usage."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Generate dashboard with large dataset
        large_data = {
            "pending_requests": [
                {
                    "request_id": f"req{i}",
                    "category": "travel",
                    "amount": 1000,
                    "user_info": {"user_id": f"user{i}"},
                    "timestamp": "2024-03-01T10:00:00"
                } for i in range(100)
            ],
            "approved_requests": [],
            "rejected_requests": [],
            "summary_stats": {
                "total_requests": 100,
                "total_amount": 100000,
                "approval_rate": 0
            }
        }

        result = self.dashboard_agent.generate_dashboard_html(data=large_data)
        final_memory = process.memory_info().rss
        memory_used = final_memory - initial_memory

        print(f"\nMemory Usage for Large Dataset:")
        print(f"Initial memory: {initial_memory / 1024 / 1024:.2f} MB")
        print(f"Final memory: {final_memory / 1024 / 1024:.2f} MB")
        print(f"Memory used: {memory_used / 1024 / 1024:.2f} MB")

        # Assert reasonable memory usage (less than 100MB for large dataset)
        self.assertLess(memory_used, 100 * 1024 * 1024, "Dashboard generation should use less than 100MB of memory")

    def test_collect_request_info_validation(self):
        # Test case-insensitive category validation
        request_data = {
            "category": "TRAVEL",
            "amount": "100",
            "justification": "Business trip",
            "supporting_material": ["itinerary", "receipt"],
            "user_info": {"user_id": "123", "user_org": "IT", "location": "NYC"},
            "card_info": {"card_number": "1234", "card_type": "credit", "expiry_date": "12/25"},
            "travel_dates": {"start": "2024-03-01", "end": "2024-03-03"}
        }
        result = collect_request_info(request_data)
        self.assertEqual(result["status"], "success")

        # Test invalid category
        request_data["category"] = "invalid"
        result = collect_request_info(request_data)
        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid category", result["message"])

        # Test missing amount
        del request_data["amount"]
        result = collect_request_info(request_data)
        self.assertEqual(result["status"], "error")
        self.assertIn("Missing required fields: amount (Expense amount)", result["message"])

        # Test invalid amount
        request_data["category"] = "travel"  # Ensure category is valid
        request_data["amount"] = "not_a_number"
        result = collect_request_info(request_data)
        self.assertEqual(result["status"], "error")
        self.assertIn("Amount must be a valid number", result["message"])

if __name__ == '__main__':
    unittest.main() 