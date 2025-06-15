from google.adk.agents import Agent
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from reimbly.sub_agents.reporting import prompt
from google.adk.tools.agent_tool import AgentTool

# Define sub-step agents for the reporting agent
summary_stats_generator_agent = Agent(
    name="summary_stats_generator_agent",
    description="Generates summary statistics from reimbursement data.",
    model="gemini-2.0-flash",
    instruction=prompt.GENERATE_SUMMARY_STATS_INSTR
)

time_series_analyzer_agent = Agent(
    name="time_series_analyzer_agent",
    description="Analyzes trends in reimbursement data over time.",
    model="gemini-2.0-flash",
    instruction=prompt.GENERATE_TIME_SERIES_INSTR
)

budget_utilization_checker_agent = Agent(
    name="budget_utilization_checker_agent",
    description="Tracks and reports budget utilization across categories.",
    model="gemini-2.0-flash",
    instruction=prompt.GENERATE_BUDGET_UTILIZATION_INSTR
)

filtered_report_generator_agent = Agent(
    name="filtered_report_generator_agent",
    description="Creates customized reports by applying filters to data.",
    model="gemini-2.0-flash",
    instruction=prompt.GENERATE_FILTERED_REPORT_INSTR
)

# Define the reporting agent
reporting_agent = Agent(
    name="reporting_agent",
    description="Agent for generating reimbursement reports and analytics",
    model="gemini-2.0-flash",
    instruction=prompt.REPORTING_AGENT_INSTR,
    tools=[
        AgentTool(agent=summary_stats_generator_agent),
        AgentTool(agent=time_series_analyzer_agent),
        AgentTool(agent=budget_utilization_checker_agent),
        AgentTool(agent=filtered_report_generator_agent),
    ],
) 