"""
Reimbly - Reimbursement System Architecture Summary

High-Level Overview:
- Root Agent (root_agent.py): Orchestrates the entire reimbursement workflow.
- Sub-Agents:
  - Request Agent: Collects and validates reimbursement requests.
  - Policy Agent: Checks requests against company policies and determines approval routes.
  - Review Agent: Handles multi-step approval workflows and role-based access.
  - Reporting Agent: Aggregates data for analytics and reporting.
  - Dashboard Agent: Generates HTML dashboards for admins.
  - Notification Agent: Handles all notification logic.
- Tools:
  - Notification Tools: Email formatting and sending utilities.
  - Progress Tools: Status tracking and progress bar generation.
  - Validation Tools: Common validation utilities.
"""
from google.adk.agents import Agent
from typing import Dict, Any
import uuid
from datetime import datetime
import time

# Import sub-agents
from .sub_agents.request.agent import request_agent
from .sub_agents.policy.agent import policy_agent
from .sub_agents.review.agent import review_agent
from .sub_agents.reporting.agent import reporting_agent
from .sub_agents.dashboard.agent import dashboard_agent
from .sub_agents.notification.agent import notification_agent

# Import tools
from .tools.notification import send_notification
from .tools.progress import format_progress_bar

# Global in-memory storage for pending approvals and reporting data
pending_approvals: Dict[str, Dict[str, Any]] = {}
reporting_data: Dict[str, Dict[str, Any]] = {}

def process_reimbursement(request: Dict[str, Any]) -> Dict[str, Any]:
    """Process reimbursement requests and approvals."""
    try:
        action = request.get("action")
        data = request.get("data", {})

        if action == "submit":
            # Delegate request validation to request agent
            validation_result = request_agent.transfer({
                "action": "validate",
                "data": data
            })
            if validation_result["status"] == "error":
                return validation_result

            # Delegate policy validation to policy agent
            policy_result = policy_agent.transfer({
                "action": "validate",
                "data": data
            })
            if policy_result["status"] == "error":
                return policy_result

            # Generate request ID and prepare data
            request_id = f"REQ-{int(time.time())}{uuid.uuid4().hex[:6]}"
            data["request_id"] = request_id
            data["timestamp"] = datetime.now().isoformat()
            data["approval_route"] = policy_result["approval_route"].copy()
            data["status"] = "pending"
            data["reviews"] = []

            # Store data
            pending_approvals[request_id] = data.copy()
            reporting_data[request_id] = data.copy()

            # Delegate notification to notification agent
            notification_agent.transfer({
                "action": "notify_submission",
                "data": data
            })

            return {
                "status": "success",
                "request_id": request_id,
                "approval_route": policy_result["approval_route"]
            }

        elif action == "approve":
            # Delegate approval processing to review agent
            review_result = review_agent.transfer({
                "action": "process_approval",
                "data": data,
                "pending_approvals": pending_approvals
            })

            if review_result["status"] == "success":
                # Update stored data
                request_id = data.get("request_id")
                if request_id in pending_approvals:
                    pending_approvals[request_id].update(review_result["updated_data"])
                    reporting_data[request_id].update(review_result["updated_data"])

                # Delegate notification to notification agent
                notification_agent.transfer({
                    "action": "notify_approval_update",
                    "data": review_result["updated_data"]
                })

            return review_result

        elif action == "report":
            # Delegate reporting to reporting agent
            return reporting_agent.transfer({
                "action": "generate_report",
                "data": data,
                "reporting_data": reporting_data
            })

        else:
            return {"status": "error", "message": f"Invalid action: {action}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_pending_approvals(approver_id: str) -> Dict[str, Any]:
    """Get all pending approvals for an approver."""
    # Delegate to review agent
    return review_agent.transfer({
        "action": "get_pending",
        "approver_id": approver_id,
        "pending_approvals": pending_approvals
    })

# Define the root agent
root_agent = Agent(
    name="reimbursement_root",
    description="Root agent for coordinating reimbursement workflow",
    model="gemini-2.0-flash",
    sub_agents=[
        request_agent,
        policy_agent,
        notification_agent,
        review_agent,
        reporting_agent,
        dashboard_agent
    ],
    instruction=(
        "You are the root agent for the reimbursement system. You coordinate between:\n"
        "1. Request Agent: Collects and validates reimbursement requests\n"
        "2. Policy Agent: Validates requests against company policies\n"
        "3. Notification Agent: Sends email notifications\n"
        "4. Review Agent: Handles the approval workflow\n"
        "5. Reporting Agent: Generates reports and analytics\n"
        "6. Dashboard Agent: Generates admin dashboard\n\n"
        "You can process the following actions:\n"
        "- submit: Submit a new reimbursement request\n"
        "- approve: Approve or reject a request\n"
        "- report: Generate reports and analytics\n"
        "- dashboard: Generate admin dashboard\n\n"
        "Please ensure all required information is provided and valid."
    )
) 