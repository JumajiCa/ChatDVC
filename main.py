
import os

import openai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a counselor at Diablo Valley College, in Pleasant Hill California; for a student's first message, please introduce yourself!"},
        {"role": "user", "content": "Hello, when does the semester end?"},
    ],
    stream=False
)

print(response.choices[0].message.content)