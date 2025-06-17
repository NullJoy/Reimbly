"""Notification tools for the reimbursement system."""
from typing import Dict, Any, Optional
import os
import re
import logging
from google.adk.tools import FunctionTool
from typing import Dict, Any

# Configure logging for this module
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Email configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "reimbly@gmail.com")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# Try to import SendGrid, but don't fail if not available
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    from python_http_client.exceptions import HTTPError
    SENDGRID_AVAILABLE = True
except ImportError:
    logging.warning("SendGrid package not available. Email notifications will be logged but not sent.")
    SENDGRID_AVAILABLE = False

def validate_email(email: str) -> bool:
    """Validate email format.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if email is valid, False otherwise
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def format_notification_subject(notification_type: str, request_data: Dict[str, Any]) -> str:
    """Format the subject line for a notification.
    
    Args:
        notification_type (str): Type of notification
        request_data (Dict[str, Any]): The request data
        
    Returns:
        str: Formatted subject line
    """
    case_id = request_data.get("case_id", "Unknown")
    subject_templates = {
        "submit": f"Reimbursement Request Submitted - {case_id}",
        "update": f"Reimbursement Request Update - {case_id}",
        "review": f"New Reimbursement Request to Review - {case_id}",
        "complete": f"Reimbursement Request Completed - {case_id}"
    }
    return subject_templates.get(notification_type, f"Reimbursement Request - {case_id}")

def format_notification_body(notification_type: str, request_data: Dict[str, Any], progress_bar: Optional[str] = None) -> str:
    """Format the body of a notification.
    
    Args:
        notification_type (str): Type of notification
        request_data (Dict[str, Any]): The request data
        progress_bar (Optional[str]): Progress bar string if available
        
    Returns:
        str: Formatted notification body
    """
    case_id = request_data.get("case_id", "Unknown")
    category = request_data.get("case_id", "Unknown")
    amount = request_data.get("amount", 0)
    status = request_data.get("status", "Unknown")
    
    body = f"Case ID: {case_id}\n"
    body += f"Category: {category}\n"
    body += f"Amount: ${amount}\n"
    body += f"Status: {status}\n"
    
    if progress_bar:
        body += f"\nProgress:\n{progress_bar}\n"
    
    if notification_type == "review":
        body += f"\nPlease review this request at: https://reimbly.company.com/review/{case_id}"
    
    return body

def format_progress_bar(request_data: Dict[str, Any]) -> str:
    """Format the progress bar for a request.
    
    Args:
        request_data (Dict[str, Any]): The request data containing approval route and reviews.
        
    Returns:
        str: HTML formatted progress bar.
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
    
    # Format as HTML
    progress_html = " → ".join(steps)
    return f'<div style="margin: 20px 0; padding: 10px; background: #f5f5f5; border-radius: 5px;">{progress_html}</div>'

def send_notification(notification_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send an email notification.
    
    Args:
        notification_data (Dict[str, Any]): The notification data containing:
            - type: Type of notification (submit, update, review, complete)
            - recipient: Email address of the recipient
            - request_data: The request data for context
            - subject: Email subject
            - content: Email content
            - chatbox_link: Optional link to chatbox
            
    Returns:
        Dict[str, Any]: The result of sending the notification.
    """
    logging.debug(f"send_notification called with data: {notification_data}")
    print(f"[DEBUG]: send_notification called with data: {notification_data}")
    
    # Validate recipient email
    recipient_email = notification_data.get('recipient')
    if not recipient_email:
        error_msg = "No recipient email provided"
        logging.error(error_msg)
        return {"status": "error", "error_message": error_msg}
        
    if not validate_email(recipient_email):
        error_msg = f"Invalid recipient email format: {recipient_email}"
        logging.error(error_msg)
        return {"status": "error", "error_message": error_msg}
    
    try:
        if not SENDGRID_AVAILABLE:
            error_msg = "SendGrid package not available"
            logging.error(error_msg)
            return {"status": "error", "error_message": error_msg}

        if not SENDGRID_API_KEY:
            error_msg = "SENDGRID_API_KEY environment variable not set"
            logging.error(error_msg)
            return {"status": "error", "error_message": error_msg}

        notification_type = notification_data.get("type")
        request_data = notification_data.get("request_data", {})
        
        # Generate appropriate content based on notification type
        if notification_type == "submit":
            content = f"""
            <h2>New Reimbursement Request Submitted</h2>
            <p>Your reimbursement request has been submitted successfully.</p>
            <p><strong>Reimbursement Case ID:</strong> {request_data.get("case_id")}</p>
            <p><strong>Amount:</strong> ${request_data.get("amount")}</p>
            <p><strong>Category:</strong> {request_data.get("category")}</p>
            <p><strong>Justification:</strong> {request_data.get("justification")}</p>
            """
        elif notification_type == "update":
            content = f"""
            <h2>Reimbursement Request Update</h2>
            <p>Your reimbursement request has been updated.</p>
            <p><strong>Reimbursement Case ID:</strong> {request_data.get("case_id")}</p>
            <p><strong>Status:</strong> {request_data.get("status")}</p>
            {format_progress_bar(request_data)}
            """
        elif notification_type == "review":
            chatbox_link = notification_data.get("chatbox_link", "#")
            content = f"""
            <h2>New Reimbursement Request to Review</h2>
            <p>You have been assigned to review a reimbursement request.</p>
            <p><strong>Reimbursement Case ID:</strong> {request_data.get("case_id")}</p>
            <p><strong>Amount:</strong> ${request_data.get("amount")}</p>
            <p><strong>Category:</strong> {request_data.get("category")}</p>
            <p><strong>Justification:</strong> {request_data.get("justification")}</p>
            {format_progress_bar(request_data)}
            <p><a href="{chatbox_link}" style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">Review Request</a></p>
            """
        elif notification_type == "complete":
            content = f"""
            <h2>Reimbursement Request Review Completed</h2>
            <p>Your review has been recorded.</p>
            <p><strong>Reimbursement Case ID:</strong> {request_data.get("case_id")}</p>
            <p><strong>Your Decision:</strong> {request_data.get("action")}</p>
            <p><strong>Comment:</strong> {request_data.get("comment")}</p>
            {format_progress_bar(request_data)}
            """
        else:
            content = notification_data.get("content", "")

        # Send email using SendGrid
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=recipient_email,
            subject=notification_data['subject'],
            html_content=content
        )
        
        logging.info(f"Sending notification to {recipient_email} for request {request_data.get('case_id')}")
        response = sg.send(message)
        
        logging.info(f"SendGrid API response status code: {response.status_code}")
        logging.debug(f"SendGrid API response body: {response.body}")
        logging.debug(f"SendGrid API response headers: {response.headers}")
        
        return {
            "status": "success",
            "message": "Notification sent successfully",
            "recipient": recipient_email,
            "case_id": request_data.get("case_id")
        }
    except HTTPError as e:
        error_msg = f"SendGrid API error: {str(e)}"
        logging.error(error_msg)
        logging.debug(f"SendGrid API error details: {e.to_dict}")
        return {"status": "error", "error_message": error_msg}
    except Exception as e:
        error_msg = f"Failed to send notification: {str(e)}"
        logging.error(error_msg)
        return {"status": "error", "error_message": error_msg}
    
send_notification_tool = FunctionTool(func=send_notification)

def resend_case_update_email(case_id: str, case_data: Dict[str, Any], user_email: str) -> Dict[str, Any]:
    """Resend an update email for a specific case ID.

    Args:
        case_id (str): The unique ID of the reimbursement case.
        case_data (Dict[str, Any]): The case data containing all necessary information.
        user_email (str): The email address of the recipient.

    Returns:
        Dict[str, Any]: The result of sending the notification.
    """
    logging.debug(f"resend_case_update_email called for case ID: {case_id}")
    
    try:
        if not case_data:
            return {
                "status": "error",
                "error_message": f"Case data not provided for case {case_id}"
            }

        if not user_email:
            return {
                "status": "error",
                "error_message": f"User email not provided for case {case_id}"
            }

        if not validate_email(user_email):
            return {
                "status": "error",
                "error_message": f"Invalid email format: {user_email}"
            }

        notification_data = {
            "type": "update",
            "recipient": user_email,
            "subject": f"Reimbursement Request Update: {case_id}",
            "request_data": case_data
        }

        logging.debug(f"Attempting to resend update for case: {case_id} to {user_email}")
        return send_notification(notification_data)
    except Exception as e:
        error_msg = f"Error in resend_case_update_email: {str(e)}"
        logging.error(error_msg)
        return {"status": "error", "error_message": error_msg}
    

resend_case_update_email_tool = FunctionTool(func=resend_case_update_email)
