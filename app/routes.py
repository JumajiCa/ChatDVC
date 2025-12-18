# app/routes.py
from flask import Blueprint, jsonify, request
from openai import OpenAI
import os

from app.models import User, db
from app.utils import error_handling as er, EncryptionManager
# Import the new service we created
from functions.insite_service import insite_manager

# Define Blueprint
main_bp = Blueprint('main', __name__)

# Initialize Encryption Manager
encryption_manager = EncryptionManager()

# Load API Config
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.deepseek.com")


def verify_insite_credentials(username, password):
    """
    Simple validation check.
    """
    if not username or not password:
        return False
    return True


@main_bp.route("/")
def home():
    return jsonify({"message": "Flask server is running!"})


# --- USER PROFILE ENDPOINT ---
@main_bp.route("/api/user", methods=['GET', 'POST'])
def handle_user():
    if request.method == 'GET':
        user = User.query.first()
        if user:
            # Convert to dict but DO NOT send the encrypted password back to frontend
            user_data = user.to_dict()
            user_data['insite_password'] = ""
            return jsonify(user_data)
        return jsonify({})

    if request.method == 'POST':
        data = request.get_json()
        user = User.query.first()
        if not user:
            user = User()
            db.session.add(user)

        # Update standard fields
        if 'name' in data: user.name = data['name']
        if 'major' in data: user.major = data['major']
        if 'discipline' in data: user.discipline = data['discipline']
        if 'expected_grad_date' in data: user.expected_grad_date = data['expected_grad_date']
        if 'counselor' in data: user.counselor = data['counselor']

        # Handle Insite Credentials
        if 'insite_username' in data:
            user.insite_username = data['insite_username']

        # Only update password if user typed a new one
        if 'insite_password' in data and data['insite_password']:
            if verify_insite_credentials(user.insite_username, data['insite_password']):
                # Encrypt before saving to DB
                user.insite_password = encryption_manager.encrypt(data['insite_password'])

        db.session.commit()
        return jsonify({"message": "Profile saved successfully", "user": user.to_dict()})


# --- 2FA SUBMISSION ENDPOINT ---
@main_bp.route("/api/submit_2fa", methods=['POST'])
def submit_2fa():
    """
    Receives the 4-digit code from the frontend modal.
    Passes it to the active Selenium driver to complete login.
    """
    data = request.get_json()
    code = data.get('code')

    if not code:
        return jsonify({"success": False, "message": "No code provided."})

    # Get the current user
    user = User.query.first()
    if not user:
        return jsonify({"success": False, "message": "User not found."})

    # Pass the user ID and code to the service manager
    # This finds the specific browser instance waiting for this user
    success, msg = insite_manager.login_step_2_submit_code(user.id, code)

    if success:
        return jsonify({
            "success": True,
            "message": "Verification successful! Login complete. Please ask your question again to see your data."
        })
    else:
        return jsonify({"success": False, "message": f"Verification failed: {msg}"})


# --- CHAT / ASK ENDPOINT ---
@main_bp.route("/api/ask", methods=['POST'])
def handle_ask():
    if not DEEPSEEK_API_KEY:
        error_msg = "Error: 'DEEPSEEK_API_KEY' not loaded."
        er.print_error(error_text=error_msg)
        return jsonify({"answer": f"System Error: {error_msg}"})

    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"answer": "Error: No question provided."})

    question = data.get('question')

    # 1. Fetch User Context
    user = User.query.first()
    context_str = ""
    scraped_info = ""

    # 2. Check if we need to scrape data
    # Keywords that suggest the user wants real-time portal data
    keywords = ["schedule", "class", "registration", "date", "when can i register", "reg date"]
    should_scrape = any(word in question.lower() for word in keywords)

    if should_scrape and user:
        # Validate credentials exist
        if not user.insite_username or not user.insite_password:
            return jsonify({"answer": "I need your InSite username and password saved in your profile to check that."})

        try:
            # Decrypt password for Selenium use
            decrypted_pass = encryption_manager.decrypt(user.insite_password)

            # Attempt Login (Step 1)
            # This checks cookies first. If cookies fail, it tries login.
            status = insite_manager.login_step_1(user.id, user.insite_username, decrypted_pass)

            if status == "2FA_REQUIRED":
                # CRITICAL: Tell frontend to open the 2FA modal
                return jsonify({
                    "answer": "I am logging into the 4CD Portal. Please check your email for the verification code.",
                    "action_required": "2fa_input"
                })

            elif status == "LOGGED_IN":
                # If we are logged in (via cookies or fresh login without 2FA), fetch data immediately
                reg_date, schedule = insite_manager.fetch_data(user.id)
                scraped_info = f"\n[Real-time Portal Data]\nRegistration Date: {reg_date}\nSchedule: {schedule}\n"

        except Exception as e:
            er.print_error(f"Insite Scrape Error: {e}")
            scraped_info = f"\n[System Note: I tried to access InSite but failed: {str(e)}]\n"

    # 3. Build Context for AI
    if user:
        context_str = (f"\nStudent Information:\nName: {user.name}\nMajor: {user.major}\n"
                       f"Discipline: {user.discipline}\nExpected Grad: {user.expected_grad_date}\n"
                       f"Counselor: {user.counselor}\n"
                       f"{scraped_info}")

    print(f"Received question: {question}")

    # 4. Call DeepSeek
    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=BASE_URL)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f'''You are a helpful AI counselor assistant at Diablo Valley College (DVC).
                     You are NOT the student's specific assigned counselor, but you can refer to them if asked.
                     If "Real-time Portal Data" is present in the context, use it to answer the student's question accurately.

                     Student Context:
                     {context_str}'''},
                {"role": "user", "content": question},
            ],
            stream=False
        )
        response_text = response.choices[0].message.content
        return jsonify({"answer": response_text})

    except Exception as e:
        er.print_error(f"Deepseek API Error: {e}")
        return jsonify({
                           "answer": "I'm currently having trouble connecting to my brain (Deepseek API). Please check the server logs."})


# from flask import Blueprint, jsonify, request
# from openai import OpenAI
# import os
#
# from app.models import User, db
# from app.utils import error_handling as er, EncryptionManager
# # from functions import get_schedule, get_reg_date
#
# # Define Blueprint
# main_bp = Blueprint('main', __name__)
#
# # Initialize Encryption Manager
# encryption_manager = EncryptionManager()
#
# # Load API Config
# DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# BASE_URL = os.getenv("BASE_URL", "https://api.deepseek.com")
#
# def verify_insite_credentials(username, password):
#     """
#     Stub for verifying Insite credentials.
#     """
#     if not username or not password:
#         return False
#     return True
#
# @main_bp.route("/")
# def home():
#     return jsonify({"message": "Flask server is running!"})
#
# @main_bp.route("/api/user", methods=['GET', 'POST'])
# def handle_user():
#     if request.method == 'GET':
#         user = User.query.first()
#         if user:
#             return jsonify(user.to_dict())
#         return jsonify({})
#
#     if request.method == 'POST':
#         data = request.get_json()
#         user = User.query.first()
#         if not user:
#             user = User()
#             db.session.add(user)
#
#         # Update fields if provided
#         if 'name' in data: user.name = data['name']
#         if 'major' in data: user.major = data['major']
#         if 'discipline' in data: user.discipline = data['discipline']
#         if 'expected_grad_date' in data: user.expected_grad_date = data['expected_grad_date']
#         if 'counselor' in data: user.counselor = data['counselor']
#
#         # Handle Insite Credentials
#         if 'insite_username' in data:
#             user.insite_username = data['insite_username']
#
#         if 'insite_password' in data and data['insite_password']:
#             u_name = data.get('insite_username', user.insite_username)
#             if verify_insite_credentials(u_name, data['insite_password']):
#                 user.insite_password = encryption_manager.encrypt(data['insite_password'])
#             else:
#                 pass
#
#
#         db.session.commit()
#         return jsonify({"message": "Profile saved successfully", "user": user.to_dict()})
#
# @main_bp.route("/api/ask", methods=['POST'])
# def handle_ask():
#     if not DEEPSEEK_API_KEY:
#         error_msg = "Error: 'DEEPSEEK_API_KEY' not loaded or not set in the environment."
#         er.print_error(error_text=error_msg)
#         return jsonify({"answer": f"System Error: {error_msg}"})
#
#     data = request.get_json()
#     if not data or 'question' not in data:
#         return jsonify({"answer": "Error: No question provided."})
#
#     question = data.get('question')
#     if not question:
#         return jsonify({"answer": "Error: Question cannot be empty."})
#
#     print(f"Received question: {question}")
#     registration_date = "Wednesday, Nov 19, 2025 - 8:30 AM"
#     schedule = "[{'title': 'COMM-163-1544 Forensics - Speech and Debate', 'date_range': '1/26/26 - 5/22/26', 'rooms': ['Bldg/Room: DVC    ', 'Bldg/Room: DVC ONLINE'], 'instructors': [['Villa, Paul', 'Hawkins, Robert'], ['Villa, Paul', 'Hawkins, Robert']]}, {'title': 'COMSC-165-5454 Advanced Programming with C and C++', 'date_range': '1/26/26 - 5/22/26', 'rooms': ['Bldg/Room: DVC    ', 'Bldg/Room: DVC ONLINE'], 'instructors': [['Pentcheva, Caterina'], ['Pentcheva, Caterina']]}, {'title': 'ENGL-C1001-5130 Critical Thinking and Writing', 'date_range': '1/26/26 - 5/22/26', 'rooms': ['Bldg/Room: DVC ONLINE'], 'instructors': [['Goen-Salter, Heidi']]}, {'title': 'MATH-193-2283 Analytic Geometry and Calculus II', 'date_range': '1/26/26 - 5/22/26', 'rooms': ['Bldg/Room: DVC MA 109'], 'instructors': [['Smith, Dan']]}, {'title': 'PHYS-130-1191 Physics for Engineers and Scientists A: Mechanics and Wave Motion', 'date_range': '1/26/26 - 5/22/26', 'rooms': ['Bldg/Room: DVC PS 177', 'Bldg/Room: DVC PS 113', 'Bldg/Room: DVC PS 113'], 'instructors': [['Large, Evan'], ['Large, Evan'], ['Large, Evan']]}]"
#     # Fetch user context
#     user = User.query.first()
#     context_str = ""
#     if user:
#         context_str = (f"\nStudent Information:\nName: {user.name}\nMajor: {user.major}\n"
#                        f"Discipline: {user.discipline}\nExpected Grad: {user.expected_grad_date}\n"
#                        f"Assigned Counselor (for reference): {user.counselor}\n"
#                        f"Registration Date: {registration_date}\n"
#                        f"Schedule: {schedule}")
#
#     try:
#         client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=BASE_URL)
#         response = client.chat.completions.create(
#             model="deepseek-chat",
#             messages=[
#                     {"role": "system", "content": f'''You are a helpful AI counselor assistant at Diablo Valley College (DVC), Pleasant Hill, CA.
#                      You are NOT the student's specific assigned counselor, but you can refer to them if asked.
#                      For the student's first message, please introduce yourself warmly as the DVC AI Assistant.
#
#                      Here is the student's file for your reference:
#                      {context_str}'''},
#                     {"role": "user", "content": question},
#                 ],
#                 stream=False
#         )
#         response_text = f"{response.choices[0].message.content}"
#         return jsonify({"answer": response_text})
#
#     except Exception as e:
#         er.print_error(f"Deepseek API Error: {e}")
#         return jsonify({"answer": "I'm currently having trouble connecting to my brain (Deepseek API). Please check the server logs."})
