"""
backend/routes/resume_routes.py
================================
Flask Blueprint: handles resume upload → analysis → result display.
"""

import os
import uuid
from flask import (Blueprint, request, jsonify, render_template,
                   current_app, redirect, url_for, flash)
from werkzeug.utils import secure_filename

from backend.utils.extractor  import extract_text
from backend.utils.parser     import parse_resume
from backend.ml.ats_scorer    import compute_ats_score
from backend.ml.job_recommender import recommend_jobs, get_skill_gap

resume_bp = Blueprint('resume', __name__)


def _allowed(filename: str) -> bool:
    ext = filename.rsplit('.', 1)[-1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']


# ─────────────────────────────────────────────────────────────────────────────
# Upload + Analyze
# ─────────────────────────────────────────────────────────────────────────────

@resume_bp.route('/upload', methods=['POST'])
def upload_resume():
    """
    Accepts multipart/form-data with:
      - file: resume file (PDF / DOCX / TXT)
      - job_description: optional text (for ATS scoring)
    Returns JSON analysis result.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not _allowed(file.filename):
        return jsonify({'error': 'File type not allowed. Use PDF, DOCX, or TXT'}), 415

    # Save file safely
    filename  = secure_filename(file.filename)
    unique_fn = f"{uuid.uuid4().hex}_{filename}"
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_fn)
    file.save(save_path)

    try:
        result = _run_analysis(save_path, filename, request.form.get('job_description', ''))
    except Exception as e:
        os.remove(save_path)
        return jsonify({'error': str(e)}), 500

    # Optionally persist to DB (SQLite)
    _save_to_db(filename, result)

    return jsonify(result), 200


def _run_analysis(file_path: str, original_name: str, job_description: str) -> dict:
    """Core analysis pipeline."""
    text   = extract_text(file_path)
    parsed = parse_resume(text)
    ats    = compute_ats_score(text, job_description, parsed)
    jobs   = recommend_jobs(text, top_n=5)

    return {
        'filename':            original_name,
        'contact':             parsed['contact'],
        'skills':              parsed['skills'],
        'education':           parsed['education'],
        'experience_preview':  parsed['experience'][:500] if parsed['experience'] else '',
        'word_count':          parsed['word_count'],
        'sentence_count':      parsed['sentence_count'],
        'ats_score':           ats['overall_score'],
        'ats_grade':           ats['grade'],
        'ats_components':      ats['components'],
        'matched_keywords':    ats['matched_keywords'],
        'missing_keywords':    ats['missing_keywords'],
        'matched_skills':      ats['matched_skills'],
        'missing_skills':      ats['missing_skills'],
        'suggestions':         ats['suggestions'],
        'action_verbs':        ats['action_verbs_found'],
        'quantifiers':         ats['quantifiers_found'],
        'job_recommendations': jobs,
    }


def _save_to_db(filename: str, result: dict):
    """Persist summary to SQLite (best-effort — never crash the request)."""
    try:
        from backend.database import db, ResumeAnalysis
        analysis = ResumeAnalysis(
            filename    = filename,
            word_count  = result['word_count'],
            ats_score   = result['ats_score'],
            ats_grade   = result['ats_grade'],
        )
        analysis.skills              = result['skills']
        analysis.missing_skills      = result['missing_skills']
        analysis.suggestions         = result['suggestions']
        analysis.job_recommendations = result['job_recommendations']
        analysis.contact             = result['contact']
        db.session.add(analysis)
        db.session.commit()
    except Exception:
        pass  # DB not initialised in this request context


# ─────────────────────────────────────────────────────────────────────────────
# Skill gap endpoint
# ─────────────────────────────────────────────────────────────────────────────

@resume_bp.route('/skill-gap', methods=['POST'])
def skill_gap():
    """POST JSON: {resume_text, target_role}"""
    data = request.get_json(silent=True) or {}
    resume_text = data.get('resume_text', '')
    target_role = data.get('target_role', '')

    if not resume_text or not target_role:
        return jsonify({'error': 'resume_text and target_role are required'}), 400

    gap = get_skill_gap(resume_text, target_role)
    return jsonify(gap), 200


# ─────────────────────────────────────────────────────────────────────────────
# Result page (server-rendered)
# ─────────────────────────────────────────────────────────────────────────────

@resume_bp.route('/result')
def result_page():
    return render_template('result.html')
