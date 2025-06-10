import unittest
import time
from reimbly import (
    process_reimbursement,
    collect_request_info,
)
from reimbly.root_agent import get_pending_approvals
from reimbly.sub_agents.dashboard.agent import DashboardAgent
from reimbly.sub_agents.review.agent import validate_user_permission
from unittest.mock import patch

class TestReimbursementAgents(unittest.TestCase):
    def setUp(self):
        # Clear global state for test isolation
        get_pending_approvals('direct_manager').clear()

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

        # Create mock agent class
        class MockAgent:
            def __init__(self, return_value):
                self.return_value = return_value
            def transfer(self, *args, **kwargs):
                return self.return_value

        # Create mock agents with their return values
        self.mock_request_agent = MockAgent({
            "status": "success", 
            "data": self.valid_request["data"], 
            "message": "Validated",
            "request_id": "test_request_123"
        })

        self.mock_policy_agent = MockAgent({
            "status": "success", 
            "approval_route": ["direct_manager", "department_head"], 
            "message": "Policy passed",
            "request_id": "test_request_123"
        })

        self.mock_notification_agent = MockAgent({
            "status": "success", 
            "message": "Notification sent",
            "request_id": "test_request_123"
        })
        
        self.mock_review_agent = MockAgent({
            "status": "success", 
            "request_status": "pending", 
            "updated_data": {},
            "request_id": "test_request_123"
        })

        self.mock_reporting_agent = MockAgent({
            "status": "success", 
            "data": {"total_amount": 100},
            "request_id": "test_request_123"
        })

        self.mock_dashboard_agent = MockAgent({
            "status": "success", 
            "html": "mock html",
            "request_id": "test_request_123"
        })

        # Patch the agents where they are used in reimbly.root_agent
        self.patcher_request_agent = patch('reimbly.root_agent.request_agent', self.mock_request_agent)
        self.patcher_request_agent.start()

        self.patcher_policy_agent = patch('reimbly.root_agent.policy_agent', self.mock_policy_agent)
        self.patcher_policy_agent.start()

        self.patcher_notification_agent = patch('reimbly.root_agent.notification_agent', self.mock_notification_agent)
        self.patcher_notification_agent.start()
        
        self.patcher_review_agent = patch('reimbly.root_agent.review_agent', self.mock_review_agent)
        self.patcher_review_agent.start()

        self.patcher_reporting_agent = patch('reimbly.root_agent.reporting_agent', self.mock_reporting_agent)
        self.patcher_reporting_agent.start()

        self.patcher_dashboard_agent = patch('reimbly.root_agent.dashboard_agent', self.mock_dashboard_agent)
        self.patcher_dashboard_agent.start()

    def tearDown(self):
        self.patcher_request_agent.stop()
        self.patcher_policy_agent.stop()
        self.patcher_notification_agent.stop()
        self.patcher_review_agent.stop()
        self.patcher_reporting_agent.stop()
        self.patcher_dashboard_agent.stop()

    def test_request_submission(self):
        result = process_reimbursement(self.valid_request)
        print('DEBUG test_request_submission result:', result)
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
        print('DEBUG test_approval_flow submit_result:', submit_result)
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
        print('DEBUG test_rejection_flow submit_result:', submit_result)
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
        print('DEBUG test_pending_approvals submit_result:', submit_result)
        request_id = submit_result["request_id"]

        # Get pending approvals for direct manager
        pending = get_pending_approvals('direct_manager')
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
        
        dashboard_agent = DashboardAgent()
        # Patch _get_all_requests to return test_data
        with patch.object(dashboard_agent, '_get_all_requests', return_value=test_data):
            html = dashboard_agent.generate_dashboard_html(theme="light", layout="grid")
            self.assertIn("Summary Statistics", html)
            self.assertIn("Total Requests", html)
            self.assertIn("Pending Requests", html)
            self.assertIn("Approved Requests", html)
            self.assertIn("Rejected Requests", html)
            self.assertIn("req1", html)  # Pending request
            self.assertIn("req2", html)  # Approved request
            self.assertIn("req3", html)  # Rejected request
            self.assertIn("1000", html)
            self.assertIn("500", html)
            self.assertIn("200", html)

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
            dashboard_agent = DashboardAgent()
            # Patch _get_all_requests to return the current dataset
            with patch.object(dashboard_agent, '_get_all_requests', return_value=data):
                html = dashboard_agent.generate_dashboard_html(theme="light", layout="grid")
            end_time = time.time()
            
            results[name] = {
                "time": end_time - start_time,
                "request_count": len(data["pending_requests"]) + 
                               len(data["approved_requests"]) + 
                               len(data["rejected_requests"]),
                "html_size": len(html)
            }
            
            # Verify the result is valid
            self.assertIn("Summary Statistics", html)
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

        dashboard_agent = DashboardAgent()
        # Patch _get_all_requests to return large_data
        with patch.object(dashboard_agent, '_get_all_requests', return_value=large_data):
            result = dashboard_agent.generate_dashboard_html(theme="light", layout="grid")
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