from google.adk.agents import Agent
from typing import Dict, Any, List
import uuid
from datetime import datetime
from ...tools.validation import validate_approval_data
from ...tools.database import db

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
    # Get user role from Firestore
    user = db.get_user(user_id)
    if not user:
        return {
            "status": "error",
            "message": "User not found"
        }
    
    user_role = user.get("role", "employee")
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
        
        # Step 2: Validate against policies and determine approval route
        policy_result = validate_policy(request_result["data"])
        if policy_result["status"] == "error":
            return policy_result
        
        # Add approval route to request data
        request_data = request_result["data"]
        request_data["approval_route"] = policy_result.get("approval_route")
        request_data["status"] = "pending"
        
        # Store in Firestore
        try:
            request_id = db.create_reimbursement_request(request_data)
            return {
                "status": "success",
                "message": "Request submitted successfully",
                "request_id": request_id,
                "approval_route": policy_result.get("approval_route")
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to store request: {str(e)}"
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
    
    # Get request from Firestore
    request = db.get_reimbursement_request(request_id)
    if not request:
        return {
            "status": "error",
            "message": f"Request {request_id} not found"
        }
    
    # Prevent self-approval
    requestor_id = request.get("user_info", {}).get("user_id")
    if approver_id == requestor_id:
        return {
            "status": "error",
            "message": "You cannot approve or reject your own reimbursement request."
        }
    
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
            update_data = {
                "status": "approved",
                "reviews": request["reviews"]
            }
        else:
            update_data = {
                "approval_route": request["approval_route"],
                "reviews": request["reviews"]
            }
    else:  # reject
        request["status"] = "rejected"
        update_data = {
            "status": "rejected",
            "reviews": request["reviews"]
        }
    
    # Update in Firestore
    try:
        db.update_reimbursement_request(request_id, update_data)
        return {
            "status": "success",
            "message": "Request review processed successfully",
            "request_status": request["status"]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update request: {str(e)}"
        }

def get_pending_approvals(approver_id: str) -> Dict[str, Any]:
    """Get all pending approvals for an approver.
    
    Args:
        approver_id (str): The ID of the approver.
        
    Returns:
        Dict[str, Any]: List of pending approvals.
    """
    try:
        pending_approvals = db.get_pending_approvals(approver_id)
        return {
            "status": "success",
            "data": pending_approvals
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get pending approvals: {str(e)}"
        }

# Define the review agent
review_agent = Agent(
    name="review_processor",
    description="Agent for processing reimbursement reviews and approvals",
    model="gemini-2.0-flash",
    instruction=(
        "You are a reimbursement review processor. Your responsibilities include:\n"
        "1. Validating user permissions for actions\n"
        "2. Processing approval/rejection of requests\n"
        "3. Managing the approval workflow\n"
        "4. Tracking request status and history\n\n"
        "You can process the following actions:\n"
        "- submit: Submit a new reimbursement request\n"
        "- approve: Approve or reject a request\n"
        "- report: Generate reports\n\n"
        "Please ensure all required information is provided and valid."
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