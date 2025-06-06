from google.adk.agents import Agent
from typing import Dict, Any
import uuid
from datetime import datetime

# Import from sub-agents
from .sub_agents.request.agent import collect_request_info
from .sub_agents.policy.agent import validate_policy
from .sub_agents.review.agent import review_request, pending_approvals
from .sub_agents.reporting.agent import generate_report, reimbursement_data

def process_reimbursement(request: Dict[str, Any]) -> Dict[str, Any]:
    """Process a reimbursement request through the entire workflow.
    
    Args:
        request (Dict[str, Any]): The request containing action and data.
        
    Returns:
        Dict[str, Any]: The result of the processing.
    """
    action = request.get("action", "").lower()
    
    if action == "submit":
        # Step 1: Collect and validate request information
        request_result = collect_request_info(request.get("data", {}))
        if request_result["status"] == "error":
            return request_result
        
        # Add request ID and timestamp
        request_id = str(uuid.uuid4())
        request_data = request.get("data", {})
        request_data["request_id"] = request_id
        request_data["timestamp"] = datetime.now().isoformat()
        
        # Step 2: Validate against policies and determine approval route
        policy_result = validate_policy(request_data)
        if policy_result["status"] == "error":
            return policy_result
        
        # Add approval route to request data
        request_data["approval_route"] = policy_result.get("approval_route")
        
        # Step 3: Add to pending approvals for review
        pending_approvals[request_id] = request_data
        
        # Step 4: Add to reporting data
        reimbursement_data[request_id] = request_data
        
        return {
            "status": "success",
            "message": "Request submitted successfully",
            "request_id": request_id,
            "approval_route": policy_result.get("approval_route")
        }
    
    elif action == "approve":
        return review_request(request.get("data", {}))
    
    elif action == "report":
        return generate_report(request.get("data", {}))
    
    else:
        return {
            "status": "error",
            "error_message": f"Unknown action: {action}"
        }

# Define the root agent
root_agent = Agent(
    name="reimbursement_root",
    description="Root agent for coordinating reimbursement workflow",
    model="gemini-2.0-flash",
    instruction=(
        "You are the root agent for the reimbursement system. You coordinate between:\n"
        "1. Request Agent: Collects and validates reimbursement requests\n"
        "2. Policy Agent: Validates requests against company policies\n"
        "3. Review Agent: Handles the approval workflow\n"
        "4. Reporting Agent: Generates reports and analytics\n\n"
        "You can process the following actions:\n"
        "- submit: Submit a new reimbursement request\n"
        "- approve: Approve or reject a request\n"
        "- report: Generate reports and analytics\n\n"
        "Please ensure all required information is provided and valid."
    )
) 