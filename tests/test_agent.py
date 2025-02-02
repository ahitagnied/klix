import asyncio
from ..models.agent import Agent 

async def main():
    # create an agent instance with a name and a prompt
    agent = Agent(
        name="Test Agent",
        prompt="You are a helpful assistant. How can I assist you today?"
    )
    
    # define a sample user input
    user_input = "Hello, can you tell me a joke?"
    
    # call the asynchronous get_reponse method and await its result
    try:
        response = await agent.get_reponse(user_input)
        print("Assistant Response:", response)
    except Exception as e:
        print("An error occurred:", e)

# run the main function using asyncio
if __name__ == "__main__":
    asyncio.run(main())
