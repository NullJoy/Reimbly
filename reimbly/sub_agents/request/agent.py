from google.adk.agents import Agent
from typing import Dict, Any, List

def collect_request_info(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Collect and validate request information from users.
    
    Args:
        request_data (Dict[str, Any]): The request data to validate.
        
    Returns:
        Dict[str, Any]: The validation result.
    """
    # Validate required fields
    required_fields = {
        "category": "Expense category (travel, meals, supplies, other)",
        "amount": "Expense amount",
        "justification": "Business justification",
        "supporting_material": "Supporting documents (receipts, invoices, etc.)",
        "user_info": {
            "user_id": "User ID",
            "user_org": "User's organization/department",
            "location": "User's location"
        },
        "card_info": {
            "card_number": "Last 4 digits of card",
            "card_type": "Card type (credit/debit)",
            "expiry_date": "Card expiry date"
        }
    }
    
    # Check for missing fields
    missing_fields = []
    for field, description in required_fields.items():
        if field not in request_data:
            missing_fields.append(f"{field} ({description})")
    
    if missing_fields:
        return {
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }
    
    # Convert category to lowercase for case-insensitive comparison
    request_data["category"] = request_data["category"].lower()

    # Use a set for valid categories for better performance
    valid_categories = {"travel", "meals", "supplies", "other"}

    # Validate category
    if "category" not in request_data:
        return {"status": "error", "message": "Category is required"}
    if request_data["category"] not in valid_categories:
        return {
            "status": "error",
            "message": f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        }

    # Validate amount
    if "amount" not in request_data:
        return {"status": "error", "message": "Amount is required"}
    try:
        amount = float(request_data["amount"])
        if amount <= 0:
            return {"status": "error", "message": "Amount must be greater than 0"}
    except ValueError:
        return {"status": "error", "message": "Amount must be a valid number"}
    
    # Validate category and handle category-specific cases
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
    
    elif category == "supplies":
        # Validate supply-specific requirements
        if not any("invoice" in doc.lower() for doc in request_data["supporting_material"]):
            return {
                "status": "error",
                "message": "Supply expenses require an invoice"
            }
        # Check for purchase date
        if "purchase_date" not in request_data:
            return {
                "status": "error",
                "message": "Supply expenses require purchase date"
            }
        # Check for vendor information
        if "vendor" not in request_data:
            return {
                "status": "error",
                "message": "Supply expenses require vendor information"
            }
    
    elif category == "other":
        # Validate other expense requirements
        if not any("receipt" in doc.lower() for doc in request_data["supporting_material"]):
            return {
                "status": "error",
                "message": "Other expenses require receipts"
            }
        # Check for detailed justification
        if len(request_data["justification"]) < 50:
            return {
                "status": "error",
                "message": "Other expenses require detailed justification (minimum 50 characters)"
            }
    
    # Validate user_info structure
    user_info = request_data["user_info"]
    if not all(key in user_info for key in ["user_id", "user_org", "location"]):
        return {
            "status": "error",
            "message": "Invalid user_info structure. Must include user_id, user_org, and location"
        }
    
    # Validate card_info structure
    card_info = request_data["card_info"]
    if not all(key in card_info for key in ["card_number", "card_type", "expiry_date"]):
        return {
            "status": "error",
            "message": "Invalid card_info structure. Must include card_number, card_type, and expiry_date"
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
    name="request_collector",
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