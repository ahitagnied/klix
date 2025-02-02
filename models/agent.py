from dataclasses import dataclass
from typing import Optional
from ..config import DEFAULT_VOICE_ID

@dataclass
class Agent:
    name: str
    prompt: str
    voice_id: str = DEFAULT_VOICE_ID