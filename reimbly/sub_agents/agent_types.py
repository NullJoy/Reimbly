from enum import Enum

class AgentType(Enum):
    """Enum representing different types of agents in the system."""
    DASHBOARD = "dashboard"
    REQUEST = "request"
    POLICY = "policy"
    REVIEW = "review"
    REPORTING = "reporting"
    NOTIFICATION = "notification" 