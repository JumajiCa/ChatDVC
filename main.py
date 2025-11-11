
import os
from dotenv import load_dotenv
from numpy import random as npr
from openai import OpenAI
from flask import Flask 

from util import error_handling as er

# Really Sketchy Flask code
app = Flask(__name__)

@app.route("/") 
def hello(): 
    return "<h1>Hello World!</h1>"

@app.route("/rand") 
def basic_rand(): 
    random_num_lst  = npr.rand(30)
    text = ""
    for num in random_num_lst: 
        text += f"<h1>{str(num)}</h1>"
    return text

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("BASE_URL")

def main():
    if DEEPSEEK_API_KEY == "": 
        er.print_error(error_text="Error: 'DEEPSEEK_API_KEY' not loaded or not set in the environment.\nPerhaps check your '.env' file?")
        return # Exit Program Pre-maturely

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
    # Success Exit Code
    return 0

if __name__ == "__main__": 
    app.run(debug=True)
