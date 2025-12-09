from flask import Blueprint, jsonify, request
from openai import OpenAI
import os

from app.models import User, db
from app.utils import error_handling as er, EncryptionManager
from functions import get_schedule, get_reg_date

# Define Blueprint
main_bp = Blueprint('main', __name__)

# Initialize Encryption Manager
encryption_manager = EncryptionManager()

# Load API Config
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.deepseek.com")

def verify_insite_credentials(username, password):
    """
    Stub for verifying Insite credentials. 
    """
    if not username or not password:
        return False
    return True

@main_bp.route("/")
def home():
    return jsonify({"message": "Flask server is running!"})

@main_bp.route("/api/user", methods=['GET', 'POST'])
def handle_user():
    if request.method == 'GET':
        user = User.query.first()
        if user:
            return jsonify(user.to_dict())
        return jsonify({})
    
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.first()
        if not user:
            user = User()
            db.session.add(user)
        
        # Update fields if provided
        if 'name' in data: user.name = data['name']
        if 'major' in data: user.major = data['major']
        if 'discipline' in data: user.discipline = data['discipline']
        if 'expected_grad_date' in data: user.expected_grad_date = data['expected_grad_date']
        if 'counselor' in data: user.counselor = data['counselor']

        # Handle Insite Credentials
        if 'insite_username' in data: 
            user.insite_username = data['insite_username']
        
        if 'insite_password' in data and data['insite_password']:
            u_name = data.get('insite_username', user.insite_username)
            if verify_insite_credentials(u_name, data['insite_password']):
                user.insite_password = encryption_manager.encrypt(data['insite_password'])
            else:
                pass 

        if 'registration_date' not in data: 
            user.registration_date = get_reg_date

        if 'schedule' not in data: 
            user.registration_date = get_schedule

        
        db.session.commit()
        return jsonify({"message": "Profile saved successfully", "user": user.to_dict()})

@main_bp.route("/api/ask", methods=['POST'])
def handle_ask():
    if not DEEPSEEK_API_KEY:
        error_msg = "Error: 'DEEPSEEK_API_KEY' not loaded or not set in the environment."
        er.print_error(error_text=error_msg)
        return jsonify({"answer": f"System Error: {error_msg}"})

    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"answer": "Error: No question provided."})
        
    question = data.get('question')
    if not question:
        return jsonify({"answer": "Error: Question cannot be empty."})

    print(f"Received question: {question}")
    
    # Fetch user context
    user = User.query.first()
    context_str = ""
    if user:
        context_str = (f"\nStudent Information:\nName: {user.name}\nMajor: {user.major}\n"
                       f"Discipline: {user.discipline}\nExpected Grad: {user.expected_grad_date}\n"
                       f"Assigned Counselor (for reference): {user.counselor}")

    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=BASE_URL)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                    {"role": "system", "content": f'''You are a helpful AI counselor assistant at Diablo Valley College (DVC), Pleasant Hill, CA.
                     You are NOT the student's specific assigned counselor, but you can refer to them if asked.
                     For the student's first message, please introduce yourself warmly as the DVC AI Assistant.
                     
                     Here is the student's file for your reference:
                     {context_str}'''},
                    {"role": "user", "content": question},
                ],
                stream=False
        )
        response_text = f"{response.choices[0].message.content}"
        return jsonify({"answer": response_text})
        
    except Exception as e:
        er.print_error(f"Deepseek API Error: {e}")
        return jsonify({"answer": "I'm currently having trouble connecting to my brain (Deepseek API). Please check the server logs."})
