"""
Reimbly - A Reimbursement Management System
"""

# Import the root agent first
from .root_agent import root_agent

# Import sub-agents
from .sub_agents.request.agent import request_agent, collect_request_info
from .sub_agents.policy.agent import policy_agent, validate_policy
from .sub_agents.review.agent import review_agent, review_request, get_pending_approvals
from .sub_agents.reporting.agent import reporting_agent, generate_report
from .sub_agents.dashboard.agent import dashboard_agent

# Import the main processing function
from .root_agent import process_reimbursement

# This is what ADK looks for - must be named 'agent'
agent = root_agent

# Version information
__version__ = '0.1.0'

# Export all public components
__all__ = [
    'agent',           # The main agent that ADK looks for
    'root_agent',      # The root agent implementation
    'request_agent',   # Request handling sub-agent
    'policy_agent',    # Policy validation sub-agent
    'review_agent',    # Review and approval sub-agent
    'reporting_agent', # Reporting sub-agent
    'dashboard_agent', # Dashboard generation sub-agent
    'process_reimbursement',  # Main processing function
    'collect_request_info',   # Collect and validate request info
    'validate_policy',        # Policy validation function
    'review_request',         # Review request function
    'get_pending_approvals',  # Get pending approvals
    'generate_report'         # Generate reports
] 
