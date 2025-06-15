"""Common data schema and types for reimbursement agents."""

# Convenient declaration for controlled generation.
import types
from typing import Optional

from google.genai import types
from pydantic import BaseModel, Field


json_response_config = types.GenerateContentConfig(
    response_mime_type="application/json"
)

class Decision(BaseModel):
    """An entry in the decision log"""
    actor_id: str = Field(description="The id of the decision maker, e.g. policy_agent, 423517")
    action: str = Field(description="The decision action made, e.g. policy_compliance_validated, approve, reject")
    timestamp: str = Field(description="Time in YYYY-MM-DD HH:MM:SS format in UTC timezone, e.g. 2025/01/23 16:00:00Z")
    comments: Optional[str] = Field(description="Provide comments if reject")


class Document(BaseModel):
    """An entry in the attachments list"""
    type: str = Field(description="file type, either png/jpg/pdf")
    name: str = Field(description="file name")
    url: str = Field(description="file url, e.g. https://files.company.com/reimb/case_893124/hotel_invoice.pdf")

class ReimburseCase(BaseModel):
    """A reimburse case"""
    case_id: str = Field(description="Unique id of a reimburse case that is formatted like `case_12345`")
    user_id: str = Field(description="The employee id of the creator of this reimbursement case")
    submitted_at: str = Field(description="Submitted time in YYYY-MM-DD HH:MM:SS format in UTC timezone, e.g. 2025/01/23 16:00:00Z")
    status: str = Field(description="The case status, e.g. submitted, pending_review, approved, rejected")
    amount: float = Field(description="Reimbursement amount")
    currency: str = Field(description="Currency of the reimbursement, default to USD")
    category: str = Field(description="The reimbursement category, e.g., travel, meals, lodging, supplies")
    justification: str = Field(description="Business justification for the reimbursement case")
    reimburse_card_number: str = Field(description="The card number to accept the payment")
    reviewer_route: list[str] = Field(
        default=[], description="A list of the reviewers' employee id, in order"
    )
    decision_log: list[Decision] = Field(
        default=[], description="Decision log"
    )
    attachments: list[Document] = Field(
        default=[], description="Attachments like receipts/invoices"
    )
    last_updated: str = Field(description="Last updated time in YYYY-MM-DD HH:MM:SS format in UTC timezone, e.g. 2025/01/23 16:00:00Z")


class UserProfile(BaseModel):
    """An example user profile."""
    user_id: str = Field(description="Employee id of user")
    name: str = Field(description="Name of user")
    email: str = Field(description="Email address of user")
    direct_manager: str = Field(description="Employee id of the user's line manager")
    cases: list[ReimburseCase] = Field(
        default=[], description="A list of reimbursement requests this user submitted"
    )
    department: str = Field(
        description="User's department, e.g. Engineering"
    )
    location: str = Field(description="Home location of user")
    default_card_number: str = Field(
        description="User's default bank card number"
    )

