from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",  
        messages=[                
            {"role": "user", "content": "Hello, how are you?"}
        ],
        max_tokens=10
    )
    print("Test API Response:", response.choices[0].message.content) 
except Exception as e:
    print("API Error:", e)


