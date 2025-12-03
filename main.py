
import os
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, jsonify, request
from flask_cors import CORS

from util import error_handling as er, EncryptionManager
from app.database import db
from app.models import User

def verify_insite_credentials(username, password):
    """
    Stub for verifying Insite credentials. 
    In a production environment, this would use Selenium or an API request to
    log in to the Insite portal and verify the credentials are valid.
    """
    # TODO: Implement actual scraping/login logic here
    if not username or not password:
        return False
    
    # Mock verification: Assume any non-empty credential pair is valid for now.
    # You would replace this with: return scraper.try_login(username, password)
    return True

def get_student_id(name: str, campus: str) -> None: 
    '''
    Parameters: 
    name: The Student's name
    campus: Either the San Ramon or Pleasant Hill Campus 

    Descriptions:
    Function that gets a student's id from the Insite Website. 
    '''
    # Calls selenium to get html data
    # Implement a way to scrape the html for the information. 
    # return this to the AI 
    

app = Flask(__name__)

# Load Environment Variables 
load_dotenv()

# DB Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

encryption_manager = EncryptionManager()

# Load API Key 
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.deepseek.com")

# Set Up CORS to allow requests from Svelte, thereby creating the interface to connect
# both applications together.
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://localhost:5174"]}})

@app.route("/")
def home():
    return jsonify({"message": "Flask server is running!"})

@app.route("/api/user", methods=['GET', 'POST'])
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
            # Verify credentials before saving (Mock check)
            # Note: we use the username from data if present, else from existing user record
            u_name = data.get('insite_username', user.insite_username)
            if verify_insite_credentials(u_name, data['insite_password']):
                user.insite_password = encryption_manager.encrypt(data['insite_password'])
            else:
                # If verification fails (though our mock is permissive), you might want to return an error.
                # For now, we'll just log it or proceed. 
                pass 
        
        db.session.commit()
        return jsonify({"message": "Profile saved successfully", "user": user.to_dict()})

@app.route("/api/ask", methods=['POST'])
def handle_ask():
    if not DEEPSEEK_API_KEY:
        error_msg = "Error: 'DEEPSEEK_API_KEY' not loaded or not set in the environment. Please check your .env file."
        er.print_error(error_text=error_msg)
        return jsonify({"answer": f"System Error: {error_msg}"})

    # Get questions from Svelte Frontend. 
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

if __name__ == "__main__": 
    app.run(host="0.0.0.0", port=5000, debug=True)
