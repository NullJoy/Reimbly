from google.adk.agents import Agent
from typing import Dict, Any, List
from ...tools.validation import validate_request_data

def collect_request_info(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Collect and validate request information from users.
    
    Args:
        request_data (Dict[str, Any]): The request data to validate.
        
    Returns:
        Dict[str, Any]: The validation result.
    """
    # Use the validation tool to check basic request structure
    is_valid, error_message = validate_request_data(request_data)
    if not is_valid:
        return {
            "status": "error",
            "message": error_message
        }
    
    # Validate category-specific requirements
    category = request_data["category"]
    if category == "travel":
        # Validate travel-specific requirements
        if not any("itinerary" in doc.lower() for doc in request_data["supporting_material"]):
            return {
                "status": "error",
                "message": "Travel expenses require an itinerary"
            }
        if not any("receipt" in doc.lower() for doc in request_data["supporting_material"]):
            return {
                "status": "error",
                "message": "Travel expenses require receipts"
            }
        # Check for travel dates
        if "travel_dates" not in request_data:
            return {
                "status": "error",
                "message": "Travel expenses require travel dates"
            }
    
    elif category == "meals":
        # Validate meal-specific requirements
        if not any("receipt" in doc.lower() for doc in request_data["supporting_material"]):
            return {
                "status": "error",
                "message": "Meal expenses require receipts"
            }
        # Check for meal date
        if "meal_date" not in request_data:
            return {
                "status": "error",
                "message": "Meal expenses require meal date"
            }
        # Check for number of attendees
        if "attendees" not in request_data:
            return {
                "status": "error",
                "message": "Meal expenses require number of attendees"
            }
    
    # Validate supporting material
    if not isinstance(request_data["supporting_material"], list) or not request_data["supporting_material"]:
        return {
            "status": "error",
            "message": "Supporting material must be a non-empty list"
        }
    
    return {
        "status": "success",
        "message": "Request information validated successfully",
        "data": request_data
    }

def get_request_template() -> Dict[str, Any]:
    """Get a template for a reimbursement request.
    
    Returns:
        Dict[str, Any]: A template showing the required fields and their descriptions.
    """
    return {
        "category": "Expense category (travel, meals, supplies, other)",
        "amount": "Expense amount in USD",
        "justification": "Business justification for the expense",
        "supporting_material": ["List of supporting documents (receipts, invoices, etc.)"],
        "user_info": {
            "user_id": "Your employee ID",
            "user_org": "Your organization/department",
            "location": "Your office location"
        },
        "card_info": {
            "card_number": "Last 4 digits of your card",
            "card_type": "Card type (credit/debit)",
            "expiry_date": "Card expiry date (MM/YY)"
        }
    }

# Define the request agent
request_agent = Agent(
    name="request_agent",
    description="Agent for collecting and validating reimbursement requests",
    model="gemini-2.0-flash",
    instruction=(
        "You are a reimbursement request helper. Help users submit their reimbursement requests by:\n"
        "1. Explaining what information is needed\n"
        "2. Validating the provided information\n"
        "3. Ensuring all required fields are complete\n"
        "4. Providing clear error messages if something is missing or invalid\n\n"
        "Required information includes:\n"
        "- Expense category (travel, meals, supplies, other)\n"
        "- Amount\n"
        "- Business justification\n"
        "- Supporting documents\n"
        "- User information (ID, organization, location)\n"
        "- Card information for reimbursement"
    )
) 