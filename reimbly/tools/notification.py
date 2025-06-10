"""Notification tools for the reimbursement system."""
from typing import Dict, Any, Optional
from ..sub_agents.notification.agent import notification_agent

def format_notification_subject(notification_type: str, request_data: Dict[str, Any]) -> str:
    """Format the subject line for a notification.
    
    Args:
        notification_type (str): Type of notification
        request_data (Dict[str, Any]): The request data
        
    Returns:
        str: Formatted subject line
    """
    request_id = request_data.get("request_id", "Unknown")
    subject_templates = {
        "submit": f"Reimbursement Request Submitted - {request_id}",
        "update": f"Reimbursement Request Update - {request_id}",
        "review": f"New Reimbursement Request to Review - {request_id}",
        "complete": f"Reimbursement Request Completed - {request_id}"
    }
    return subject_templates.get(notification_type, f"Reimbursement Request - {request_id}")

def format_notification_body(notification_type: str, request_data: Dict[str, Any], progress_bar: Optional[str] = None) -> str:
    """Format the body of a notification.
    
    Args:
        notification_type (str): Type of notification
        request_data (Dict[str, Any]): The request data
        progress_bar (Optional[str]): Progress bar string if available
        
    Returns:
        str: Formatted notification body
    """
    request_id = request_data.get("request_id", "Unknown")
    category = request_data.get("category", "Unknown")
    amount = request_data.get("amount", 0)
    status = request_data.get("status", "Unknown")
    
    body = f"Request ID: {request_id}\n"
    body += f"Category: {category}\n"
    body += f"Amount: ${amount}\n"
    body += f"Status: {status}\n"
    
    if progress_bar:
        body += f"\nProgress:\n{progress_bar}\n"
    
    if notification_type == "review":
        body += f"\nPlease review this request at: https://reimbly.company.com/review/{request_id}"
    
    return body

def send_notification(
    notification_type: str,
    recipient: str,
    request_data: Dict[str, Any],
    progress_bar: Optional[str] = None,
    chatbox_link: Optional[str] = None
) -> None:
    """Send a notification to the specified recipient.
    
    Args:
        notification_type (str): Type of notification (submit, update, review, complete)
        recipient (str): Email address of the recipient
        request_data (Dict[str, Any]): The request data
        progress_bar (Optional[str]): Progress bar string if available
        chatbox_link (Optional[str]): Link to the chatbox for review notifications
    """
    notification_data = {
        "type": notification_type,
        "recipient": recipient,
        "subject": format_notification_subject(notification_type, request_data),
        "body": format_notification_body(notification_type, request_data, progress_bar),
        "request_data": request_data
    }
    
    if chatbox_link:
        notification_data["chatbox_link"] = chatbox_link
    
    notification_agent.transfer(notification_data) 