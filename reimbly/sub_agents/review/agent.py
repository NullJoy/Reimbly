from google.adk.agents import Agent
from typing import Dict, Any, List
import uuid
from datetime import datetime
from ...tools.validation import validate_approval_data

# In-memory storage for pending approvals
pending_approvals: Dict[str, Dict[str, Any]] = {}

# User roles and permissions
USER_ROLES = {
    "employee": {
        "can_submit": True,
        "can_approve": False,
        "can_view_all": False
    },
    "admin": {
        "can_submit": True,
        "can_approve": True,
        "can_view_all": True
    },
    "manager": {
        "can_submit": True,
        "can_approve": True,
        "can_view_all": False
    }
}

def validate_user_permission(user_id: str, action: str) -> Dict[str, Any]:
    """Validate if a user has permission to perform an action.
    
    Args:
        user_id (str): The ID of the user
        action (str): The action to validate
        
    Returns:
        Dict[str, Any]: The validation result
    """
    # TODO: Replace with actual user role lookup from database
    # For now, we'll use a simple mapping
    user_roles = {
        "user123": "employee",
        "admin123": "admin",
        "manager123": "manager"
    }
    
    user_role = user_roles.get(user_id, "employee")
    role_permissions = USER_ROLES[user_role]
    
    if action == "submit" and not role_permissions["can_submit"]:
        return {
            "status": "error",
            "message": f"User with role {user_role} cannot submit reimbursements"
        }
    elif action == "approve" and not role_permissions["can_approve"]:
        return {
            "status": "error",
            "message": f"User with role {user_role} cannot approve reimbursements"
        }
    elif action == "view_all" and not role_permissions["can_view_all"]:
        return {
            "status": "error",
            "message": f"User with role {user_role} cannot view all reimbursements"
        }
    
    return {
        "status": "success",
        "message": "Permission validated successfully",
        "role": user_role
    }

def process_reimbursement(request: Dict[str, Any]) -> Dict[str, Any]:
    """Process a reimbursement request through the entire workflow.
    
    Args:
        request (Dict[str, Any]): The request containing action and data.
        
    Returns:
        Dict[str, Any]: The result of the processing.
    """
    action = request.get("action", "").lower()
    
    if action == "submit":
        # Validate user permission
        user_id = request.get("data", {}).get("user_info", {}).get("user_id")
        if not user_id:
            return {
                "status": "error",
                "message": "User ID is required"
            }
        
        permission_result = validate_user_permission(user_id, "submit")
        if permission_result["status"] == "error":
            return permission_result
        
        # Step 1: Collect and validate request information
        request_result = collect_request_info(request.get("data", {}))
        if request_result["status"] == "error":
            return request_result
        
        # Add request ID and timestamp
        request_id = str(uuid.uuid4())
        request_data = request.get("data", {})
        request_data["request_id"] = request_id
        
        # Step 2: Validate against policies and determine approval route
        policy_result = validate_policy(request_data)
        if policy_result["status"] == "error":
            return policy_result
        
        # Add approval route to request data
        request_data["approval_route"] = policy_result.get("approval_route")
        
        # Step 3: Add to pending approvals for review
        pending_approvals[request_id] = request_data
        
        # Step 4: Add to reporting data
        from reporting.agent import reimbursement_data
        reimbursement_data[request_id] = request_data
        
        return {
            "status": "success",
            "message": "Request submitted successfully",
            "request_id": request_id,
            "approval_route": policy_result.get("approval_route")
        }
    
    elif action == "approve":
        # Validate user permission
        approver_id = request.get("data", {}).get("approver_id")
        if not approver_id:
            return {
                "status": "error",
                "message": "Approver ID is required"
            }
        
        permission_result = validate_user_permission(approver_id, "approve")
        if permission_result["status"] == "error":
            return permission_result
        
        return review_request(request.get("data", {}))
    
    elif action == "report":
        # Validate user permission
        user_id = request.get("data", {}).get("user_id")
        if not user_id:
            return {
                "status": "error",
                "message": "User ID is required"
            }
        
        permission_result = validate_user_permission(user_id, "view_all")
        if permission_result["status"] == "error":
            return permission_result
        
        return generate_report(request.get("data", {}))
    
    else:
        return {
            "status": "error",
            "message": f"Unknown action: {action}"
        }

def review_request(review_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a review action (approve/reject) for a request.
    
    Args:
        review_data (Dict[str, Any]): The review data containing:
            - request_id: The ID of the request to review
            - action: "approve" or "reject"
            - approver_id: The ID of the approver
            - comment: Optional comment for the review
            
    Returns:
        Dict[str, Any]: The result of the review action.
    """
    # Use the validation tool to check approval data structure
    is_valid, error_message = validate_approval_data(review_data)
    if not is_valid:
        return {
            "status": "error",
            "message": error_message
        }
    
    request_id = review_data["request_id"]
    action = review_data["action"]
    approver_id = review_data["approver_id"]
    comment = review_data["comment"]
    
    # Check if request exists
    if request_id not in pending_approvals:
        return {
            "status": "error",
            "message": f"Request {request_id} not found"
        }
    
    request = pending_approvals[request_id]
    
    # Check if approver is authorized
    if approver_id not in request["approval_route"]:
        return {
            "status": "error",
            "message": f"Approver {approver_id} is not authorized for this request"
        }
    
    # Record the review action
    review = {
        "approver_id": approver_id,
        "action": action,
        "comment": comment,
        "timestamp": datetime.now().isoformat()
    }
    
    if "reviews" not in request:
        request["reviews"] = []
    request["reviews"].append(review)
    
    # Update approval status
    if action == "approve":
        request["approval_route"].remove(approver_id)
        if not request["approval_route"]:
            request["status"] = "approved"
            return {
                "status": "success",
                "message": "Request fully approved",
                "request_status": "approved"
            }
        return {
            "status": "success",
            "message": "Request approved, waiting for additional approvals",
            "request_status": "pending",
            "remaining_approvers": request["approval_route"]
        }
    else:  # reject
        request["status"] = "rejected"
        return {
            "status": "success",
            "message": "Request rejected",
            "request_status": "rejected"
        }

def get_pending_approvals(approver_id: str) -> Dict[str, Any]:
    """Get all pending approvals for an approver.
    
    Args:
        approver_id (str): The ID of the approver.
        
    Returns:
        Dict[str, Any]: List of pending approvals.
    """
    pending = {
        request_id: request
        for request_id, request in pending_approvals.items()
        if approver_id in request["approval_route"]
    }
    
    return {
        "status": "success",
        "pending_approvals": pending
    }

# Define the review agent
review_agent = Agent(
    name="review_processor",
    description="Agent for processing reimbursement request reviews and approvals",
    model="gemini-2.0-flash",
    instruction=(
        "You are a review processing agent. Your responsibilities include:\n"
        "1. Processing approval and rejection actions\n"
        "2. Validating approver authorization\n"
        "3. Tracking approval progress\n"
        "4. Managing the approval workflow\n\n"
        "Review process:\n"
        "1. Validate review action and approver authorization\n"
        "2. Record the review with timestamp and comments\n"
        "3. Update request status based on action\n"
        "4. Track remaining approvers in the route\n\n"
        "Request states:\n"
        "- Pending: Waiting for approvals\n"
        "- Approved: All approvals received\n"
        "- Rejected: Any approver rejected the request"
    )
)

# Example usage:
if __name__ == "__main__":
    # Example 1: Submit a new request
    new_request = {
        "action": "submit",
        "data": {
            "category": "travel",
            "amount": 800,
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
    
    # Process the request
    result = process_reimbursement(new_request)
    
    # Example 2: Approve the request
    approval = {
        "action": "approve",
        "data": {
            "action": "approve",
            "approver_id": "manager123",
            "request_id": result["request_id"],
            "comment": "Approved after reviewing receipts"
        }
    }
    
    approval_result = process_reimbursement(approval)
    
    # Example 3: Generate a report
    report = {
        "action": "report",
        "data": {
            "report_type": "summary",
            "filters": {
                "category": "travel"
            }
        }
    }
    
    report_result = process_reimbursement(report) 