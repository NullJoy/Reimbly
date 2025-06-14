from google.adk.agents import Agent
from typing import Dict, Any, List

def determine_approval_route(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Determine the required approval route based on request details.
    
    Args:
        request_data (Dict[str, Any]): The validated request data.
        
    Returns:
        Dict[str, Any]: The approval route information.
    """
    amount = float(request_data["amount"])
    category = request_data["category"]
    user_org = request_data["user_info"]["user_org"]
    
    # Define approval thresholds
    thresholds = {
        "low": 1000,      # Up to $1,000
        "medium": 5000,   # Up to $5,000
        "high": 10000     # Up to $10,000
    }
    
    # Define approval routes
    routes = {
        "low": ["direct_manager"],
        "medium": ["direct_manager", "department_head"],
        "high": ["direct_manager", "department_head", "finance"],
        "executive": ["direct_manager", "department_head", "finance", "executive"]
    }
    
    # Special cases
    if category == "travel" and amount > 2000:
        # All travel expenses over $2,000 need executive approval
        return {
            "route": routes["executive"],
            "reason": "High-value travel expense requiring executive approval"
        }
    
    if user_org.lower() == "executive":
        # All executive expenses need executive approval
        return {
            "route": routes["executive"],
            "reason": "Executive-level expense requiring full approval chain"
        }
    
    # Standard routing based on amount
    if amount <= thresholds["low"]:
        return {
            "route": routes["low"],
            "reason": "Standard expense within low threshold"
        }
    elif amount <= thresholds["medium"]:
        return {
            "route": routes["medium"],
            "reason": "Medium-value expense requiring department head approval"
        }
    elif amount <= thresholds["high"]:
        return {
            "route": routes["high"],
            "reason": "High-value expense requiring finance approval"
        }
    else:
        return {
            "route": routes["executive"],
            "reason": "High-value expense requiring executive approval"
        }

def validate_policy(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate request against company policies.
    
    Args:
        request_data (Dict[str, Any]): The request data to validate.
        
    Returns:
        Dict[str, Any]: The validation result.
    """
    # Validate amount limits
    amount = float(request_data["amount"])
    category = request_data["category"]
    
    # Category-specific limits
    category_limits = {
        "travel": 10000,    # $10,000 per trip
        "meals": 100,       # $100 per meal
        "supplies": 1000,   # $1,000 per order
        "other": 5000       # $5,000 per request
    }
    
    if amount > category_limits[category]:
        return {
            "status": "error",
            "message": f"Amount exceeds category limit of ${category_limits[category]} for {category}"
        }
    
    # Validate supporting material
    supporting_material = request_data["supporting_material"]
    if not supporting_material:
        return {
            "status": "error",
            "message": "Supporting material is required"
        }
    
    # Category-specific material requirements
    required_material = {
        "travel": ["receipt", "itinerary"],
        "meals": ["receipt"],
        "supplies": ["receipt", "invoice"],
        "other": ["receipt", "justification"]
    }
    
    missing_material = []
    for material in required_material[category]:
        if not any(material in doc.lower() for doc in supporting_material):
            missing_material.append(material)
    
    if missing_material:
        return {
            "status": "error",
            "message": f"Missing required supporting material for {category}: {', '.join(missing_material)}"
        }
    
    # If all validations pass, determine approval route
    approval_route = determine_approval_route(request_data)
    
    return {
        "status": "success",
        "message": "Request passes all policy checks",
        "approval_route": approval_route["route"],
        "approval_reason": approval_route["reason"]
    }

# Define the policy agent
policy_agent = Agent(
    name="policy_agent",
    description="Agent for validating reimbursement requests against company policies",
    model="gemini-2.0-flash",
    instruction=(
        "You are a policy validation agent. Your responsibilities include:\n"
        "1. Validating requests against company policies\n"
        "2. Checking amount limits for different categories\n"
        "3. Verifying required supporting material\n"
        "4. Determining the appropriate approval route\n\n"
        "Policy rules:\n"
        "- Travel: Up to $10,000 per trip, requires receipt and itinerary\n"
        "- Meals: Up to $100 per meal, requires receipt\n"
        "- Supplies: Up to $1,000 per order, requires receipt and invoice\n"
        "- Other: Up to $5,000 per request, requires receipt and justification\n\n"
        "Approval routes:\n"
        "- Low: Direct manager only\n"
        "- Medium: Direct manager and department head\n"
        "- High: Direct manager, department head, and finance\n"
        "- Executive: Full approval chain including executive"
    )
) 