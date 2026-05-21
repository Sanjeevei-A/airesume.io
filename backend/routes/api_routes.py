"""
backend/routes/api_routes.py
=============================
REST API Blueprint for advanced AI add-ons (ChatGPT / Gemini suggestions).
"""

from flask import Blueprint, request, jsonify
from backend.ml.ai_advisor import get_suggestions

api_bp = Blueprint('api', __name__)


@api_bp.route('/ai-suggestions', methods=['POST'])
def ai_suggestions():
    """
    POST JSON:
    {
      "resume_text":      "...",
      "job_description":  "...",   (optional)
      "ats_score":        72.5,    (optional)
      "provider":         "gemini" | "openai"  (optional, default: gemini)
    }
    Returns structured AI-generated improvement suggestions.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    resume_text     = data.get('resume_text', '').strip()
    job_description = data.get('job_description', '')
    ats_score       = float(data.get('ats_score', 0))
    provider        = data.get('provider', 'gemini')

    if not resume_text:
        return jsonify({'error': 'resume_text is required'}), 400

    result = get_suggestions(resume_text, job_description, ats_score, provider)
    return jsonify(result), 200


@api_bp.route('/health', methods=['GET'])
def health():
    """Simple health-check endpoint."""
    return jsonify({'status': 'ok', 'service': 'AI Resume Analyzer'}), 200
