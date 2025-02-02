from dataclasses import dataclass
from typing import Optional
from ..config import DEFAULT_VOICE_ID

@dataclass
class Agent:
    """
    initialises an agent with a name, scenario through prompt attribute and a voice id through the voice_id attribute

    attributes: 
        name (str): a string representing the name of the agent.
        prompt (str): a string representing the prompt for the agent.
        voice_id (str): a string representing the voice id of the agent. defaults to DEFAULT_VOICE_ID.
    """
    name: str
    prompt: str
    voice_id: str = DEFAULT_VOICE_ID