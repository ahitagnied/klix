from dataclasses import dataclass
from typing import Optional
from ..config import DEFAULT_VOICE_ID

@dataclass
class Scenario:
    """
    initialises a scenario or a test case with a name and a prompt

    attributes: 
        name: a string representing the name of the scenario
        prompt: a string representing the prompt used to define the scenarios
    """
    name: str
    prompt: str