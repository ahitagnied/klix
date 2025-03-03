from dataclasses import dataclass
from typing import Optional
import sys
from pathlib import Path

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from config import DEFAULT_VOICE_ID

@dataclass
class Agent:
    """
    Initializes an agent with a name, scenario through prompt attribute and a voice id.

    Attributes:
        name (str): The name of the agent.
        prompt (str): The system prompt/instructions for the agent.
        voice_id (str): The voice id for the agent. Defaults to DEFAULT_VOICE_ID.
        api_key (str): OpenAI API key. If not provided, will try to get from config or environment.
    """
    name: str
    prompt: str
    voice_id: str = DEFAULT_VOICE_ID
    api_key: Optional[str] = None
    
    # Note: We're simplifying the Agent class to avoid OpenAI Assistants API integration
    # since the CallBot is using a direct chat completion approach