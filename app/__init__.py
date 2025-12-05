from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from app.database import db
from app.routes import main_bp

def create_app():
    app = Flask(__name__)
    load_dotenv()

    # DB Config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Setup CORS
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://localhost:5174"]}})

    # Register Blueprints
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        
    return app
