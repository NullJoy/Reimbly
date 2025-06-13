import unittest
import time
import psutil
import os
from reimbly.sub_agents.dashboard.agent import DashboardAgent

class TestDashboardAgent(unittest.TestCase):
    def setUp(self):
        self.dashboard_agent = DashboardAgent()

    def test_dashboard_generation(self):
        """Test dashboard HTML generation."""
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
        html = result["html"]
        self.assertIn("Reimbly Admin Dashboard", html)
        self.assertIn("Total Requests", html)
        self.assertIn("Total Amount", html)
        self.assertIn("Pending Requests", html)
        self.assertIn("Approval Rate", html)
        self.assertIn("req1", html)
        self.assertIn("req2", html)
        self.assertIn("req3", html)
        self.assertIn("$1,000.00", html)
        self.assertIn("$500.00", html)
        self.assertIn("$200.00", html)

    def test_dashboard_performance(self):
        """Test dashboard generation performance with different data sizes."""
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
                "request_count": len(data["pending_requests"]) + len(data["approved_requests"]) + len(data["rejected_requests"]),
                "html_size": len(result["html"])
            }
            self.assertEqual(result["status"], "success")
            self.assertIn("html", result)
            html = result["html"]
            self.assertIn("Reimbly Admin Dashboard", html)
            self.assertIn("Total Requests", html)
            for request in data["pending_requests"]:
                self.assertIn(request["request_id"], html)
            for request in data["approved_requests"]:
                self.assertIn(request["request_id"], html)
            for request in data["rejected_requests"]:
                self.assertIn(request["request_id"], html)
        print("\nDashboard Generation Performance Results:")
        print("=" * 50)
        for name, metrics in results.items():
            print(f"\n{name.upper()} Dataset:")
            print(f"Number of requests: {metrics['request_count']}")
            print(f"Generation time: {metrics['time']:.3f} seconds")
            print(f"HTML size: {metrics['html_size']} bytes")
            print(f"Average time per request: {metrics['time']/metrics['request_count']:.3f} seconds")
        self.assertLess(results["small"]["time"], 1.0, "Small dataset should generate in under 1 second")
        self.assertLess(results["medium"]["time"], 2.0, "Medium dataset should generate in under 2 seconds")
        self.assertLess(results["large"]["time"], 5.0, "Large dataset should generate in under 5 seconds")

    def test_dashboard_memory_usage(self):
        """Test dashboard generation memory usage."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
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
        self.assertLess(memory_used, 100 * 1024 * 1024, "Dashboard generation should use less than 100MB of memory")

    def test_trigger_html_generation(self):
        """Test triggering HTML generation with a command."""
        # Test valid command
        result = self.dashboard_agent.trigger_html_generation("generate dashboard")
        self.assertEqual(result["status"], "success")
        self.assertIn("html", result)

        # Test invalid command
        result = self.dashboard_agent.trigger_html_generation("invalid command")
        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid command", result["message"])

if __name__ == '__main__':
    unittest.main() 