from google.adk.agents import Agent
from typing import Dict, Any, List
import uuid
from datetime import datetime
from reimbly.sub_agents.review import prompt
from google.adk.tools.agent_tool import AgentTool
from reimbly.tools.notification import send_notification_tool

# Define sub-step agents for the review agent
user_permission_validator_agent = Agent(
    name="user_permission_validator_agent",
    description="Validates if a user has permission to perform an action.",
    model="gemini-2.0-flash",
    instruction=prompt.VALIDATE_USER_PERMISSION_INSTR
)

review_action_processor_agent = Agent(
    name="review_action_processor_agent",
    description="Processes approval and rejection actions for reimbursement requests.",
    model="gemini-2.0-flash",
    instruction=prompt.PROCESS_REVIEW_ACTION_INSTR
)

pending_approvals_retriever_agent = Agent(
    name="pending_approvals_retriever_agent",
    description="Retrieves a list of pending approvals for a specific approver.",
    model="gemini-2.0-flash",
    instruction=prompt.GET_PENDING_APPROVALS_INSTR
)

# Create the review agent
review_agent = Agent(
    name="review_agent",
    description="Agent for handling reimbursement reviews",
    model="gemini-2.0-flash",
    instruction=prompt.REVIEW_AGENT_INSTR,
    tools=[
        AgentTool(agent=user_permission_validator_agent),
        AgentTool(agent=review_action_processor_agent),
        AgentTool(agent=pending_approvals_retriever_agent),
        send_notification_tool
    ],
)