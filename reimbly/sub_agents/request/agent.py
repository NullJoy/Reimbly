from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from reimbly.shared_libraries.types import ReimburseCase
from reimbly.sub_agents.request import prompt
from reimbly.tools.memory import memorize


init_case_agent = Agent(
    model="gemini-2.0-flash",
    name="init_case_agent",
    instruction=prompt.INIT_CASE_AGENT_INSTR,
    description="This agent initiate a new reimburse case",
    tools=[memorize]
)

validate_agent = Agent(
    model="gemini-2.0-flash",
    name="validate_agent",
    instruction=prompt.VALIDATE_AGENT_INSTR,
    description="This agent validates the information in a reimburse case is complete and valid",
)

info_collect_agent = Agent(
    model="gemini-2.0-flash",
    name="info_collect_agent",
    instruction=prompt.INFO_COLLECT_AGENT_INSTR,
    description="This agent collects information for a reimburse case from user",
    tools=[memorize]
)

save_agent = Agent(
    model="gemini-2.0-flash",
    name="save_agent",
    instruction=prompt.SAVE_AGENT_INSTR,
    description="This agent saves a reimburse case from state to database",
)


# Define the request agent
request_agent = Agent(
    name="request_agent",
    description="Agent for collecting info reimbursement requests",
    model="gemini-2.0-flash",
    instruction=prompt.REQUEST_AGENT_INSTR,
    tools=[
        AgentTool(agent=init_case_agent), 
        AgentTool(agent=info_collect_agent),
        AgentTool(agent=validate_agent),
        AgentTool(agent=save_agent)
    ]
) 