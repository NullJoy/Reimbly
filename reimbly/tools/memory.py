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

def memorize(key: str, value: str, tool_context: ToolContext):
    """
    Memorize pieces of information, one key-value pair at a time.

    Args:
        key: the label indexing the memory to store the value.
        value: the information to be stored.
        tool_context: The ADK tool context.

    Returns:
        A status message.
    """
    print(f"\n[DEBUG] Memorize called with key: {key}, value: {value}")
    print(f"[DEBUG] Current state before update: {tool_context.state}")
    
    # Parse the key to handle nested state updates
    key_parts = key.split('.')
    current = tool_context.state
    
    # Navigate to the nested location
    for part in key_parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    
    # Update the value at the final location
    current[key_parts[-1]] = value
    
    print(f"[DEBUG] State after update: {tool_context.state}")
    return {"status": f'Stored "{key}": "{value}"'}


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
