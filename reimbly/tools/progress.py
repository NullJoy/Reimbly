"""Progress tracking tools for the reimbursement system."""
from typing import Dict, Any, List

def format_progress_bar(request_data: Dict[str, Any]) -> str:
    """Format the progress bar for a request.
    
    Args:
        request_data (Dict[str, Any]): The request data containing approval route and reviews.
        
    Returns:
        str: Formatted progress bar string.
    """
    approval_route = request_data.get("approval_route", [])
    reviews = request_data.get("reviews", [])
    
    # Create progress steps
    steps = ["Case submitted"]
    for approver in approval_route:
        # Check if this approver has reviewed
        approver_review = next((r for r in reviews if r["approver_id"] == approver), None)
        if approver_review:
            status = "✅" if approver_review["action"] == "approve" else "❌"
            steps.append(f"{approver}: {status}")
        else:
            steps.append(f"{approver}: Pending")
    steps.append("Case completed")
    
    return " → ".join(steps)

def get_approval_progress(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed approval progress information.
    
    Args:
        request_data (Dict[str, Any]): The request data
        
    Returns:
        Dict[str, Any]: Progress information including:
            - total_steps: Total number of approval steps
            - completed_steps: Number of completed steps
            - current_step: Current step in the process
            - remaining_steps: List of remaining approvers
            - progress_percentage: Percentage of completion
    """
    approval_route = request_data.get("approval_route", [])
    reviews = request_data.get("reviews", [])
    
    total_steps = len(approval_route)
    completed_steps = len([r for r in reviews if r["action"] == "approve"])
    
    # Find current step
    current_step = None
    for approver in approval_route:
        if not any(r["approver_id"] == approver for r in reviews):
            current_step = approver
            break
    
    # Calculate remaining steps
    remaining_steps = [a for a in approval_route if not any(r["approver_id"] == a for r in reviews)]
    
    # Calculate progress percentage
    progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
    
    return {
        "total_steps": total_steps,
        "completed_steps": completed_steps,
        "current_step": current_step,
        "remaining_steps": remaining_steps,
        "progress_percentage": progress_percentage
    }

def get_approval_status(request_data: Dict[str, Any]) -> str:
    """Get the current approval status of a request.
    
    Args:
        request_data (Dict[str, Any]): The request data
        
    Returns:
        str: Current status (pending, approved, rejected)
    """
    if request_data.get("status") == "rejected":
        return "rejected"
    
    approval_route = request_data.get("approval_route", [])
    reviews = request_data.get("reviews", [])
    
    # Check if all approvers have approved
    if all(any(r["approver_id"] == a and r["action"] == "approve" for r in reviews) for a in approval_route):
        return "approved"
    
    # Check if any approver has rejected
    if any(r["action"] == "reject" for r in reviews):
        return "rejected"
    
    return "pending" 