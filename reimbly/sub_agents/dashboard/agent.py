"""
Dashboard Generation Agent
Generates HTML dashboard for admin view
"""

from typing import Dict, List, Any
import json
from datetime import datetime
from google.adk.agents import Agent

def generate_dashboard_html(data: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate HTML dashboard for admin view
    
    Args:
        data: Dictionary containing dashboard data
            {
                "pending_requests": List[Dict],
                "approved_requests": List[Dict],
                "rejected_requests": List[Dict],
                "summary_stats": Dict
            }
    
    Returns:
        Dict containing status and HTML content
    """
    try:
        # Pre-process data for better performance
        pending_requests = data.get("pending_requests", [])
        approved_requests = data.get("approved_requests", [])
        rejected_requests = data.get("rejected_requests", [])
        summary_stats = data.get("summary_stats", {})
        
        # Generate request lists using list comprehension for better performance
        pending_html = _generate_request_list(pending_requests, "pending")
        approved_html = _generate_request_list(approved_requests, "approved")
        rejected_html = _generate_request_list(rejected_requests, "rejected")
        
        # Generate summary section
        summary_html = _generate_summary_section(summary_stats)
        
        # Combine all sections
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reimbly Admin Dashboard</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .summary {{
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .requests-section {{
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .request-list {{
                    list-style: none;
                    padding: 0;
                }}
                .request-item {{
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                }}
                .request-item:last-child {{
                    border-bottom: none;
                }}
                .status-pending {{
                    color: #f39c12;
                }}
                .status-approved {{
                    color: #27ae60;
                }}
                .status-rejected {{
                    color: #c0392b;
                }}
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                }}
                .summary-item {{
                    text-align: center;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }}
                .summary-value {{
                    font-size: 24px;
                    font-weight: bold;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Reimbly Admin Dashboard</h1>
                    <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                {summary_html}
                
                <div class="requests-section">
                    <h2>Pending Requests</h2>
                    {pending_html}
                </div>
                
                <div class="requests-section">
                    <h2>Approved Requests</h2>
                    {approved_html}
                </div>
                
                <div class="requests-section">
                    <h2>Rejected Requests</h2>
                    {rejected_html}
                </div>
            </div>
        </body>
        </html>
        """
        
        return {
            "status": "success",
            "html": html
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def _generate_request_list(requests: List[Dict], status: str) -> str:
    """Generate HTML for a list of requests"""
    if not requests:
        return "<p>No requests found</p>"
    
    # Use list comprehension for better performance
    request_items = [
        f"""
        <div class=\"request-item\">\n            <strong>Request ID:</strong> {req.get('request_id', 'N/A')}<br>\n            <strong>Category:</strong> {req.get('category', 'N/A')}<br>\n            <strong>Amount:</strong> ${req.get('amount', 0):,.2f}<br>\n            <strong>User:</strong> {req.get('user_info', {}).get('user_id', 'N/A')}<br>\n            <strong>Timestamp:</strong> {req.get('timestamp', 'N/A')}<br>\n            <strong>Status:</strong> <span class=\"status-{status}\">{status.title()}</span>\n        </div>\n        """
        for req in requests
    ]
    
    return f'<div class="request-list">{"".join(request_items)}</div>'

def _generate_summary_section(stats: Dict) -> str:
    """Generate HTML for summary statistics"""
    return f"""
    <div class=\"summary\">\n        <h2>Summary Statistics</h2>\n        <div class=\"summary-grid\">\n            <div class=\"summary-item\">\n                <h3>Total Requests</h3>\n                <div class=\"summary-value\">{stats.get('total_requests', 0)}</div>\n            </div>\n            <div class=\"summary-item\">\n                <h3>Total Amount</h3>\n                <div class=\"summary-value\">${stats.get('total_amount', 0):,.2f}</div>\n            </div>\n            <div class=\"summary-item\">\n                <h3>Approval Rate</h3>\n                <div class=\"summary-value\">{stats.get('approval_rate', 0):.1f}%</div>\n            </div>\n        </div>\n    </div>\n    """

# Define the dashboard agent
dashboard_agent = Agent(
    name="dashboard_generator",
    description="Agent for generating HTML for the admin dashboard",
    model="gemini-2.0-flash",
    instruction=(
        "You are a dashboard generation agent. Your responsibilities include:\n"
        "1. Generating HTML for the admin dashboard\n"
        "2. Displaying summary statistics\n"
        "3. Showing pending, approved, and rejected requests\n"
        "4. Providing interactive elements for request management\n\n"
        "Dashboard features:\n"
        "- Summary statistics cards\n"
        "- Request lists by status\n"
        "- Interactive request details\n"
        "- Responsive design using Bootstrap"
    )
) 