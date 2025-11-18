
import os
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, jsonify, request
from flask_cors import CORS

from util import error_handling as er
# from app import app

app = Flask(__name__)

# Load Environment Variables 
load_dotenv()

# Load API Key 
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("BASE_URL")

# Set Up CORS to allow requests from Svelte, thereby creating the interface to connect
# both applications together.
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

@app.route("/")
def home():
    return jsonify({"message": "Flask server is running!"})

@app.route("/api/ask", methods=['POST'])
def handle_ask():
    # Get questions from Svelte Frontend. 
    data = request.get_json()
    question = data.get('question')

    # ----
    # TODO: Put the Deepseek Code here.
    # ----

    # For now, just send a simple response back
    print(f"Received question: {question}")
    response_text = f"The LLM's answer to '{question}' will go here."

    return jsonify({"answer": response_text})

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
    app.run(host="0.0.0.0", port=5000, debug=True)
