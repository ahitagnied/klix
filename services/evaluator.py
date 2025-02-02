from typing import List
from openai import OpenAI
from ..models.conversation import Conversation
from ..config import OPENAI_API_KEY

class ConversationEvaluator:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    async def evaluate(self, conversation: Conversation, criteria: List[str]) -> dict:
        # Evaluate conversation against criteria
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Evaluate this conversation against the given criteria."},
                    {"role": "user", "content": f"Conversation: {conversation.transcript}\nCriteria: {criteria}"}
                ]
            )
            return {
                "passed": True,
                "feedback": response.choices[0].message.content
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }