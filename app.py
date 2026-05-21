"""
AI Resume Analyzer - Main Flask Application
==========================================
Entry point for the Flask web application.
"""

from flask import Flask
from flask_cors import CORS
from backend.routes.resume_routes import resume_bp
from backend.routes.admin_routes import admin_bp
from backend.routes.api_routes import api_bp
from config import Config
import os

def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder='frontend/templates',
        static_folder='frontend/static'
    )
    app.config.from_object(config_class)

    # Enable CORS for API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register Blueprints
    app.register_blueprint(resume_bp, url_prefix='/resume')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MODEL_FOLDER'], exist_ok=True)

    # Root route
    from flask import render_template
    @app.route('/')
    def index():
        return render_template('index.html')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
