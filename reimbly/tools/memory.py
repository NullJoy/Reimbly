
"""The 'memorize' tool for several agents to affect session states."""

from datetime import datetime
import json
import os
from typing import Dict, Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.sessions.state import State
from google.adk.tools import ToolContext


SAMPLE_SCENARIO_PATH = os.getenv(
    "REIMBURSEMENT_SCENARIO", "reimbly/profiles/reimburse_empty_default.json"
)


def _set_initial_states(source: Dict[str, Any], target: State | dict[str, Any]):
    """
    Setting the initial session state given a JSON object of states.

    Args:
        source: A JSON object of states.
        target: The session state object to insert into.
    """

    target.update(source)
    


def _load_prestored_user_profile(callback_context: CallbackContext):
    """
    Sets up the initial state.
    Set this as a callback as before_agent_call of the root_agent.
    This gets called before the system instruction is contructed.

    Args:
        callback_context: The callback context.
    """    
    data = {}
    with open(SAMPLE_SCENARIO_PATH, "r") as file:
        data = json.load(file)
        print(f"\nLoading Initial State: {data}\n")

    _set_initial_states(data["state"], callback_context.state)
