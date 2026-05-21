"""
backend/database.py
===================
SQLAlchemy models for storing analysis results.
Switch to MongoDB by using PyMongo directly (see mongo_db.py).
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class ResumeAnalysis(db.Model):
    """Stores one full analysis result per uploaded resume."""
    __tablename__ = 'resume_analyses'

    id              = db.Column(db.Integer, primary_key=True)
    filename        = db.Column(db.String(255), nullable=False)
    upload_time     = db.Column(db.DateTime, default=datetime.utcnow)
    word_count      = db.Column(db.Integer)
    ats_score       = db.Column(db.Float)
    ats_grade       = db.Column(db.String(2))

    # JSON-serialised fields
    _skills         = db.Column('skills',       db.Text)
    _missing_skills = db.Column('missing_skills', db.Text)
    _suggestions    = db.Column('suggestions',  db.Text)
    _job_recs       = db.Column('job_recs',     db.Text)
    _contact        = db.Column('contact',      db.Text)

    # Convenience properties ──────────────────────────────────────────────────
    @property
    def skills(self):
        return json.loads(self._skills or '[]')

    @skills.setter
    def skills(self, v):
        self._skills = json.dumps(v)

    @property
    def missing_skills(self):
        return json.loads(self._missing_skills or '[]')

    @missing_skills.setter
    def missing_skills(self, v):
        self._missing_skills = json.dumps(v)

    @property
    def suggestions(self):
        return json.loads(self._suggestions or '[]')

    @suggestions.setter
    def suggestions(self, v):
        self._suggestions = json.dumps(v)

    @property
    def job_recommendations(self):
        return json.loads(self._job_recs or '[]')

    @job_recommendations.setter
    def job_recommendations(self, v):
        self._job_recs = json.dumps(v)

    @property
    def contact(self):
        return json.loads(self._contact or '{}')

    @contact.setter
    def contact(self, v):
        self._contact = json.dumps(v)

    def to_dict(self):
        return {
            'id':               self.id,
            'filename':         self.filename,
            'upload_time':      self.upload_time.isoformat(),
            'word_count':       self.word_count,
            'ats_score':        self.ats_score,
            'ats_grade':        self.ats_grade,
            'skills':           self.skills,
            'missing_skills':   self.missing_skills,
            'suggestions':      self.suggestions,
            'job_recommendations': self.job_recommendations,
            'contact':          self.contact,
        }


class AdminUser(db.Model):
    """Simple admin user table (extend with flask-login for full auth)."""
    __tablename__ = 'admin_users'

    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # store hashed
    created  = db.Column(db.DateTime, default=datetime.utcnow)
