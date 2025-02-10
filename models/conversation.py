from dataclasses import dataclass
from typing import List, Optional
from openai.types.chat import ChatCompletionMessageParam

@dataclass
class Conversation:
    agent_name: str
    transcript: List[ChatCompletionMessageParam]
    recording_url: str
    success: bool
    error: Optional[str] = None