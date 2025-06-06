from google.adk.agents import Agent
from typing import Dict, Any
import uuid
from datetime import datetime

# Import only the agent instances
from .sub_agents.request.agent import request_agent
from .sub_agents.policy.agent import policy_agent
from .sub_agents.review.agent import review_agent
from .sub_agents.reporting.agent import reporting_agent

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
        request_result = request_agent.transfer(request.get("data", {}))
        if request_result["status"] == "error":
            return request_result
        
        # Add request ID and timestamp
        request_id = str(uuid.uuid4())
        request_data = request.get("data", {})
        request_data["request_id"] = request_id
        request_data["timestamp"] = datetime.now().isoformat()
        
        # Step 2: Validate against policies and determine approval route
        policy_result = policy_agent.transfer(request_data)
        if policy_result["status"] == "error":
            return policy_result
        
        # Add approval route to request data
        request_data["approval_route"] = policy_result.get("approval_route")
        
        # Step 3: Add to pending approvals for review
        review_result = review_agent.transfer({"action": "add", "data": request_data})
        if review_result["status"] == "error":
            return review_result
        
        # Step 4: Add to reporting data
        reporting_result = reporting_agent.transfer({"action": "add", "data": request_data})
        if reporting_result["status"] == "error":
            return reporting_result
        
        return {
            "status": "success",
            "message": "Request submitted successfully",
            "request_id": request_id,  # Include the UUID in the response
            "approval_route": policy_result.get("approval_route"),
            "data": request_data  # Include the full request data in the response
        }
    
    elif action == "approve":
        return review_agent.transfer(request)
    
    elif action == "report":
        return reporting_agent.transfer(request)
    
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
    sub_agents=[
        request_agent,
        policy_agent,
        review_agent,
        reporting_agent,
    ],
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