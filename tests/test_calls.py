import pytest
from ..models.agent import Agent
from ..services.bot import CallBot
from ..services.evaluator import ConversationEvaluator

@pytest.mark.asyncio
async def test_basic_conversation():
    agent = Agent(
        name="TestAgent",
        prompt="You are a helpful assistant making a phone call."
    )
    bot = CallBot()
    evaluator = ConversationEvaluator()
    
    # Make test call
    call_sid = await bot.handle_call(agent, "TEST_PHONE_NUMBER")
    
    # Get conversation results
    conversation = await bot.get_conversation(call_sid)
    
    # Evaluate results
    results = await evaluator.evaluate(conversation, ["politeness", "task_completion"])
    
    assert results["passed"]