from google.adk.agents import Agent
from typing import Dict, Any
from .prompt import POLICY_AGENT_INSTR
from google.adk.tools.agent_tool import AgentTool
from reimbly.sub_agents.policy import prompt

# TODO: Implement policy_document_import_agent to read and extract policies from external input
# 1. Create a function to read policy PDFs from Firestore
# 2. Extract policy rules, limits, and requirements from PDFs
# 3. Cache the extracted policy data for performance
# 4. Implement policy update detection and reloading
# 5. Add error handling for PDF parsing and Firestore access

amount_checker_agent = Agent(
    name="amount_checker_agent",
    description="Checks if the request amount exceeds category-specific limits",
    model="gemini-2.0-flash",
    instruction= prompt.AMOUNT_CHECKER_AGENT_INSTR
)

material_checker_agent = Agent(
    name="material_checker_agent",
    description="Checks if all required supporting materials are provided",
    model="gemini-2.0-flash",
    instruction= prompt.MATERIAL_CHECKER_AGENT_INSTR
)

approval_router_agent = Agent(
    name="approval_router_agent",
    description="Determines the approval route based on request metadata",
    model="gemini-2.0-flash",
    instruction= prompt.APPROVE_ROUTER_AGENT_INSTR
)

# Define the policy agent
policy_agent = Agent(
    name="policy_agent",
    description="Agent for validating reimbursement requests against company policies",
    model="gemini-2.0-flash",
    instruction=POLICY_AGENT_INSTR,
    tools=[
        AgentTool(agent=amount_checker_agent),
        AgentTool(agent=material_checker_agent),
        AgentTool(agent=approval_router_agent),
    ],
) 