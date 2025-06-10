from enum import Enum

class UserRole(Enum):
    """Enum representing the different user roles in the system."""
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"
    FINANCE = "finance" 