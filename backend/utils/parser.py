"""
backend/utils/parser.py
=======================
Uses spaCy + NLTK to parse structured information out of raw resume text.
Extracts: contact info, skills, education, experience, summary.
"""

import re
import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

# Download NLTK data on first run (silent if already present)
for resource in ['stopwords', 'punkt', 'averaged_perceptron_tagger']:
    try:
        nltk.data.find(f'tokenizers/{resource}')
    except LookupError:
        nltk.download(resource, quiet=True)

# Load spaCy model (python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    from spacy.cli import download as spacy_download
    spacy_download('en_core_web_sm')
    nlp = spacy.load('en_core_web_sm')

STOP_WORDS = set(stopwords.words('english'))

# ─── Skill taxonomy ───────────────────────────────────────────────────────────
SKILL_KEYWORDS = {
    # Programming languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
    'kotlin', 'swift', 'ruby', 'php', 'r', 'scala', 'matlab',
    # Web / Frontend
    'react', 'angular', 'vue', 'html', 'css', 'sass', 'tailwind', 'bootstrap',
    'nextjs', 'gatsby', 'svelte', 'webpack', 'vite',
    # Backend / APIs
    'flask', 'django', 'fastapi', 'express', 'spring', 'node.js', 'nodejs',
    'rest', 'graphql', 'grpc',
    # Data / ML
    'machine learning', 'deep learning', 'nlp', 'computer vision',
    'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'pandas', 'numpy',
    'matplotlib', 'seaborn', 'opencv', 'huggingface', 'transformers',
    'spacy', 'nltk', 'xgboost', 'lightgbm',
    # Databases
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
    'sqlite', 'cassandra', 'dynamodb',
    # Cloud / DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'ci/cd',
    'terraform', 'ansible', 'linux', 'git', 'github', 'gitlab',
    # Other tools
    'excel', 'tableau', 'power bi', 'jira', 'confluence', 'agile', 'scrum',
}

# ─── Section header patterns ──────────────────────────────────────────────────
SECTION_PATTERNS = {
    'education':   r'(education|academic|qualification)',
    'experience':  r'(experience|employment|work history|career)',
    'skills':      r'(skills|technologies|competencies|expertise)',
    'projects':    r'(projects|portfolio)',
    'summary':     r'(summary|objective|profile|about)',
    'certifications': r'(certif|license|credential)',
}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def parse_resume(text: str) -> dict:
    """
    Full parse pipeline. Returns a structured dict with all resume sections.
    """
    doc = nlp(text)
    return {
        'contact':          _extract_contact(text),
        'skills':           _extract_skills(text),
        'education':        _extract_section(text, 'education'),
        'experience':       _extract_section(text, 'experience'),
        'projects':         _extract_section(text, 'projects'),
        'summary':          _extract_section(text, 'summary'),
        'certifications':   _extract_section(text, 'certifications'),
        'entities':         _extract_named_entities(doc),
        'word_count':       len(text.split()),
        'sentence_count':   len(sent_tokenize(text)),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_contact(text: str) -> dict:
    """Pull email, phone, LinkedIn URL from raw text."""
    email_pattern    = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern    = r'(\+?\d[\d\s\-().]{7,}\d)'
    linkedin_pattern = r'linkedin\.com/in/[\w\-]+'
    github_pattern   = r'github\.com/[\w\-]+'

    return {
        'email':    re.findall(email_pattern, text),
        'phone':    re.findall(phone_pattern, text),
        'linkedin': re.findall(linkedin_pattern, text, re.IGNORECASE),
        'github':   re.findall(github_pattern, text, re.IGNORECASE),
    }


def _extract_skills(text: str) -> list[str]:
    """
    Match skill keywords against the resume text (case-insensitive).
    Also catches multi-word skills like 'machine learning'.
    """
    text_lower = text.lower()
    found = sorted({skill for skill in SKILL_KEYWORDS if skill in text_lower})
    return found


def _extract_section(text: str, section: str) -> str:
    """
    Extract the text block belonging to a resume section by finding its header
    and grabbing content until the next header.
    """
    pattern = SECTION_PATTERNS.get(section)
    if not pattern:
        return ""

    lines = text.split('\n')
    capture = False
    captured = []

    other_patterns = [p for k, p in SECTION_PATTERNS.items() if k != section]
    stop_re = re.compile('|'.join(other_patterns), re.IGNORECASE)

    for line in lines:
        if re.search(pattern, line, re.IGNORECASE):
            capture = True
            continue
        if capture:
            if stop_re.search(line) and len(line.strip()) < 40:
                break
            captured.append(line)

    return '\n'.join(captured).strip()


def _extract_named_entities(doc) -> dict:
    """Return spaCy NER results grouped by label."""
    entities: dict[str, list[str]] = {}
    for ent in doc.ents:
        entities.setdefault(ent.label_, []).append(ent.text)
    return entities
