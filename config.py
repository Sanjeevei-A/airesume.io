"""
Configuration Settings
======================
All environment-based configs for the Flask app.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'

    # File Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MODEL_FOLDER  = os.path.join(os.path.dirname(__file__), 'models')
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

    # Database (SQLite for simplicity; swap URI for MongoDB)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///resume_analyzer.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MongoDB (optional — set MONGO_URI in .env to enable)
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/resume_analyzer')

    # OpenAI / Gemini (Advanced add-ons)
    OPENAI_API_KEY  = os.environ.get('OPENAI_API_KEY', '')
    GEMINI_API_KEY  = os.environ.get('GEMINI_API_KEY', '')

    # ATS scoring weights
    ATS_WEIGHTS = {
        'skills_match':    0.40,
        'keyword_density': 0.25,
        'formatting':      0.20,
        'experience':      0.15,
    }
