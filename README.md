# ResumeIQ — AI Resume Analyzer

A full-stack ML project that analyzes resumes using NLP, scores them against
ATS systems, recommends job roles, and provides AI-powered rewrite suggestions.

---

## Tech Stack

| Layer      | Technology                                   |
|------------|----------------------------------------------|
| Backend    | Python 3.11 + Flask                          |
| NLP        | spaCy (`en_core_web_sm`) + NLTK              |
| ML         | scikit-learn (TF-IDF, Logistic Regression, Cosine Similarity) |
| AI Add-ons | OpenAI GPT-4o · Google Gemini 1.5 Flash      |
| Database   | SQLite (default) · MongoDB (optional)        |
| Frontend   | HTML + CSS + Vanilla JS (no build step)      |

---

## Project Structure

```
ai-resume-analyzer/
├── app.py                      ← Flask entry point
├── config.py                   ← All configuration
├── requirements.txt
├── train_model.py              ← Train & save ATS classifier
│
├── backend/
│   ├── database.py             ← SQLAlchemy models (SQLite)
│   ├── mongo_db.py             ← PyMongo helpers (optional)
│   ├── ml/
│   │   ├── ats_scorer.py       ← ATS scoring engine (TF-IDF + rules)
│   │   ├── job_recommender.py  ← Job-role recommender (cosine similarity)
│   │   └── ai_advisor.py       ← OpenAI + Gemini suggestions
│   ├── utils/
│   │   ├── extractor.py        ← PDF / DOCX / TXT text extraction
│   │   └── parser.py           ← spaCy NLP parser (skills, contact, sections)
│   └── routes/
│       ├── resume_routes.py    ← /resume/* endpoints
│       ├── admin_routes.py     ← /admin/* endpoints
│       └── api_routes.py       ← /api/* endpoints
│
├── frontend/
│   ├── templates/
│   │   ├── index.html          ← Upload + results page
│   │   └── admin.html          ← Admin dashboard
│   └── static/
│       ├── css/style.css       ← Dark industrial UI
│       └── js/
│           ├── main.js         ← Upload form + results rendering
│           └── admin.js        ← Dashboard data loading
│
├── models/                     ← Saved ML models (joblib)
└── uploads/                    ← Temporary resume storage
```

---

## Setup

### 1 — Clone and install

```bash
git clone <your-repo>
cd ai-resume-analyzer

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2 — Download NLP models

```bash
python -m spacy download en_core_web_sm
python -m nltk.downloader stopwords punkt averaged_perceptron_tagger
```

### 3 — Environment variables

```bash
cp .env.example .env
# Edit .env with your keys
```

`.env` contents:
```
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...          # optional
GEMINI_API_KEY=AIza...         # optional
MONGO_URI=mongodb://...        # optional — uses SQLite by default
```

### 4 — Train the ML classifier

```bash
python train_model.py
```

### 5 — Initialise the database

```python
# Run once in a Python shell:
from app import create_app
from backend.database import db
app = create_app()
with app.app_context():
    db.create_all()
```

### 6 — Run

```bash
python app.py
# Open http://localhost:5000
```

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/resume/upload` | Upload resume + optional JD |
| POST | `/resume/skill-gap` | Skill gap for a target role |
| GET  | `/admin/stats` | Aggregate stats (JSON) |
| GET  | `/admin/resumes` | Paginated analysis list |
| DELETE | `/admin/resumes/<id>` | Delete a record |
| POST | `/api/ai-suggestions` | AI coach feedback |
| GET  | `/api/health` | Health check |

---

## Features

- **PDF / DOCX / TXT** resume parsing
- **ATS Score** (0–100) with grade (A–F)
- **Component breakdown**: Skills Match, Keyword Density, Formatting, Experience Quality
- **Skill extraction** via spaCy + curated taxonomy (50+ technologies)
- **Missing keyword detection** vs job description
- **Job role recommendation** — 14 roles, cosine similarity ranking
- **Skill gap analysis** for any target role
- **AI Coach** — GPT-4o or Gemini rewrite suggestions
- **Admin dashboard** — stats, grade distribution, full submission history

---

## Deployment (Render / Railway / Heroku)

```bash
# Procfile
web: gunicorn app:create_app()
```

Add `gunicorn` to requirements.txt and set environment variables in the platform dashboard.

---

## Resume Impact (for fresher portfolio)

This project demonstrates:
- **Machine Learning** — TF-IDF vectorization, cosine similarity, logistic regression
- **NLP** — spaCy NER, NLTK tokenization, regex-based parsing
- **Backend APIs** — RESTful Flask blueprints, file handling, JSON responses
- **Database** — SQLAlchemy ORM (SQLite) + PyMongo (MongoDB)
- **AI Integration** — OpenAI + Google Gemini API calls
- **Frontend** — Vanilla JS, drag-and-drop, SVG animation, responsive design
- **Deployment knowledge** — config management, WSGI, environment variables
