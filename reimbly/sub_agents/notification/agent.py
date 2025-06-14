from google.adk.agents import Agent
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import Dict, Any, List
import os

notification_agent = Agent(
    name="notification_agent",
    description="Agent for sending email notifications",
    model="gemini-2.0-flash",
    instruction=(
        "You are a notification agent. Your responsibilities include:\n"
        "1. Sending email notifications for reimbursement events\n"
        "2. Formatting email content appropriately\n"
        "3. Handling different types of notifications\n"
        "4. Managing email templates\n\n"
        "Notification types:\n"
        "1. Request Submission: When user submits a request\n"
        "2. Request Update: When a request status changes\n"
        "3. Review Assignment: When a reviewer is assigned\n"
        "4. Review Completion: When a review is completed"
    )
)

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
    try:
        notification_type = notification_data.get("type")
        request_data = notification_data.get("request_data", {})
        
        # Generate appropriate content based on notification type
        if notification_type == "submit":
            content = f"""
            <h2>New Reimbursement Request Submitted</h2>
            <p>Your reimbursement request has been submitted successfully.</p>
            <p><strong>Request ID:</strong> {request_data.get("request_id")}</p>
            <p><strong>Amount:</strong> ${request_data.get("amount")}</p>
            <p><strong>Category:</strong> {request_data.get("category")}</p>
            <p><strong>Justification:</strong> {request_data.get("justification")}</p>
            """
        elif notification_type == "update":
            content = f"""
            <h2>Reimbursement Request Update</h2>
            <p>Your reimbursement request has been updated.</p>
            <p><strong>Request ID:</strong> {request_data.get("request_id")}</p>
            <p><strong>Status:</strong> {request_data.get("status")}</p>
            {format_progress_bar(request_data)}
            """
        elif notification_type == "review":
            chatbox_link = notification_data.get("chatbox_link", "#")
            content = f"""
            <h2>New Reimbursement Request to Review</h2>
            <p>You have been assigned to review a reimbursement request.</p>
            <p><strong>Request ID:</strong> {request_data.get("request_id")}</p>
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
            <p><strong>Request ID:</strong> {request_data.get("request_id")}</p>
            <p><strong>Your Decision:</strong> {request_data.get("action")}</p>
            <p><strong>Comment:</strong> {request_data.get("comment")}</p>
            {format_progress_bar(request_data)}
            """
        else:
            content = notification_data.get("content", "")

        # Send email using SendGrid
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        message = Mail(
            from_email='reimbursements@company.com',
            to_emails=notification_data['recipient'],
            subject=notification_data['subject'],
            html_content=content
        )
        response = sg.send(message)
        return {
            "status": "success",
            "message": "Notification sent successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to send notification: {str(e)}"
        }
