from enum import Enum

class ReimbursementStatus(Enum):
    """Enum representing the possible statuses of a reimbursement request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    COMPLETED = "completed"

class ReimbursementType(Enum):
    """Enum representing the different types of reimbursements."""
    TRAVEL = "travel"
    MEALS = "meals"
    SUPPLIES = "supplies"
    SOFTWARE = "software"
    HARDWARE = "hardware"
    OTHER = "other" 