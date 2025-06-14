"""
Reimbly - Reimbursement System Architecture Summary

High-Level Overview:
- Root Agent (root_agent.py): Orchestrates the entire reimbursement workflow.
- Sub-Agents:
  - Request Agent: Collects and validates reimbursement requests.
  - Policy Agent: Checks requests against company policies and determines approval routes.
  - Review Agent: Handles multi-step approval workflows and role-based access.
  - Reporting Agent: Aggregates data for analytics and reporting.
  - Dashboard Agent: Generates HTML dashboards for admins.
  - Notification Agent: Handles all notification logic.
- Tools:
  - Notification Tools: Email formatting and sending utilities.
  - Progress Tools: Status tracking and progress bar generation.
  - Validation Tools: Common validation utilities.
"""
from google.adk.agents import Agent
from typing import Dict, Any
import uuid
from datetime import datetime
import time

from reimbly import prompt
from reimbly.tools.memory import _load_prestored_user_profile

# Import sub-agents
from .sub_agents.request.agent import request_agent
from .sub_agents.policy.agent import policy_agent
from .sub_agents.review.agent import review_agent
from .sub_agents.reporting.agent import reporting_agent
from .sub_agents.dashboard.agent import dashboard_agent
from .sub_agents.notification.agent import notification_agent

# Import tools
from .tools.notification import send_notification
from .tools.progress import format_progress_bar

# Global in-memory storage for pending approvals and reporting data
pending_approvals: Dict[str, Dict[str, Any]] = {}
reporting_data: Dict[str, Dict[str, Any]] = {}


# Define the root agent
root_agent = Agent(
    name="root_agent",
    description="A reimbursement workflow AI agent",
    model="gemini-2.0-flash",
    sub_agents=[
        request_agent,
        policy_agent,
        notification_agent,
        review_agent,
        reporting_agent,
        dashboard_agent
    ],
    instruction=prompt.ROOT_AGENT_INSTR,
    before_agent_callback=_load_prestored_user_profile,
) 