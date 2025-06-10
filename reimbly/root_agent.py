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
  - Database Tools: Firestore operations for persistent storage.
"""
from google.adk.agents import Agent
from typing import Dict, Any
import uuid
from datetime import datetime
import time
import logging

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
from .tools.database import db

def process_reimbursement(request: Dict[str, Any]) -> Dict[str, Any]:
    """Process reimbursement requests and approvals."""
    try:
        action = request.get("action")
        data = request.get("data", {})

        if action == "submit":
            # Generate request ID first
            request_id = f"REQ-{int(time.time())}{uuid.uuid4().hex[:6]}"
            data["request_id"] = request_id

            # Delegate request validation to request agent
            validation_result = request_agent.transfer({
                "action": "validate",
                "data": data
            })
            if validation_result["status"] == "error":
                return {
                    "status": "error",
                    "message": validation_result["message"],
                    "request_id": request_id
                }

            # Delegate policy validation to policy agent
            policy_result = policy_agent.transfer({
                "action": "validate",
                "data": data
            })
            if policy_result["status"] == "error":
                return {
                    "status": "error",
                    "message": policy_result["message"],
                    "request_id": request_id
                }

            # Prepare data
            data["timestamp"] = datetime.now().isoformat()
            data["approval_route"] = policy_result["approval_route"].copy()
            data["status"] = "pending"
            data["reviews"] = []

            # Store data in Firestore
            try:
                db.create_reimbursement_request(data)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.exception("Error storing reimbursement request in Firestore:")
                return {
                    "status": "error",
                    "message": f"Failed to store request: {str(e)}",
                    "request_id": request_id
                }

            # Delegate notification to notification agent
            notification_agent.transfer({
                "action": "notify_submission",
                "data": data
            })

            return {
                "status": "success",
                "message": f"Request submitted successfully. Your request ID is: {request_id}",
                "request_id": request_id,
                "approval_route": policy_result["approval_route"]
            }

        elif action == "approve":
            # Get the request from Firestore
            request_id = data.get("request_id")
            existing_request = db.get_reimbursement_request(request_id)
            if not existing_request:
                return {"status": "error", "message": "Request not found"}

            # Delegate approval processing to review agent
            review_result = review_agent.transfer({
                "action": "process_approval",
                "data": data,
                "existing_request": existing_request
            })

            if review_result["status"] == "success":
                # Update stored data in Firestore
                db.update_reimbursement_request(request_id, review_result["updated_data"])

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
                "data": data
            })

        else:
            return {"status": "error", "message": f"Invalid action: {action}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_pending_approvals(approver_id: str) -> Dict[str, Any]:
    """Get all pending approvals for an approver."""
    try:
        # Get pending approvals from Firestore
        pending_approvals = db.get_pending_approvals(approver_id)
        
        # Delegate to review agent for additional processing if needed
        return review_agent.transfer({
            "action": "get_pending",
            "approver_id": approver_id,
            "pending_approvals": pending_approvals
        })
    except Exception as e:
        return {"status": "error", "message": str(e)}

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