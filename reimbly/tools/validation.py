"""Validation tools for the reimbursement system."""
from typing import Dict, Any, List, Tuple
from datetime import datetime

def validate_request_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate the basic structure of a reimbursement request.
    
    Args:
        data (Dict[str, Any]): The request data to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    required_fields = ["user_id", "category", "amount", "justification"]
    
    # Check for required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate amount
    try:
        amount = float(data["amount"])
        if amount <= 0:
            return False, "Amount must be greater than 0"
    except (ValueError, TypeError):
        return False, "Invalid amount format"
    
    # Validate category
    valid_categories = ["travel", "meals", "supplies", "other"]
    if data["category"].lower() not in valid_categories:
        return False, f"Invalid category. Must be one of: {', '.join(valid_categories)}"
    
    # Validate justification
    if len(data["justification"].strip()) < 10:
        return False, "Justification must be at least 10 characters long"
    
    return True, ""

def validate_approval_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate approval/rejection data.
    
    Args:
        data (Dict[str, Any]): The approval data to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    required_fields = ["request_id", "approver_id", "action", "comment"]
    
    # Check for required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate action
    if data["action"] not in ["approve", "reject"]:
        return False, "Invalid action. Must be 'approve' or 'reject'"
    
    # Validate comment
    if len(data["comment"].strip()) < 5:
        return False, "Comment must be at least 5 characters long"
    
    return True, ""

def validate_reporting_params(params: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate reporting parameters.
    
    Args:
        params (Dict[str, Any]): The reporting parameters to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Validate date range if provided
    if "start_date" in params:
        try:
            datetime.fromisoformat(params["start_date"])
        except ValueError:
            return False, "Invalid start_date format. Use ISO format (YYYY-MM-DD)"
    
    if "end_date" in params:
        try:
            datetime.fromisoformat(params["end_date"])
        except ValueError:
            return False, "Invalid end_date format. Use ISO format (YYYY-MM-DD)"
    
    # Validate category filter if provided
    if "category" in params:
        valid_categories = ["travel", "meals", "supplies", "other"]
        if params["category"].lower() not in valid_categories:
            return False, f"Invalid category. Must be one of: {', '.join(valid_categories)}"
    
    return True, ""

def validate_user_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate user data structure.
    
    Args:
        data (Dict[str, Any]): The user data to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    required_fields = ["user_id", "name", "email", "department"]
    
    # Check for required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate email format
    if "@" not in data["email"] or "." not in data["email"]:
        return False, "Invalid email format"
    
    return True, "" 