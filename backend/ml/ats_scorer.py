"""
backend/ml/ats_scorer.py
========================
Computes an ATS (Applicant Tracking System) compatibility score for a resume
against a job description using TF-IDF cosine similarity + rule-based checks.
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.utils.parser import SKILL_KEYWORDS


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

FORMATTING_POSITIVE = [
    r'\b(experience|education|skills|projects|summary|objective)\b',
    r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
    r'\d{4}',          # years
]
FORMATTING_NEGATIVE = [
    r'[^\x00-\x7F]',  # non-ASCII (tables/graphics that break ATS parsers)
]

ACTION_VERBS = {
    'developed', 'designed', 'implemented', 'built', 'led', 'managed',
    'created', 'improved', 'optimized', 'deployed', 'automated', 'analyzed',
    'researched', 'collaborated', 'mentored', 'architected', 'reduced',
    'increased', 'delivered', 'launched',
}

QUANTIFIER_PATTERN = re.compile(r'\d+\s*(%|x|times|users|customers|hours|days|months|years|projects|features|million|k\b)', re.IGNORECASE)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def compute_ats_score(resume_text: str, job_description: str, parsed: dict) -> dict:
    """
    Returns a detailed ATS report:
      - overall_score (0–100)
      - component scores
      - matched / missing keywords
      - improvement suggestions
    """
    skills_score,  skills_detail  = _score_skills_match(resume_text, job_description, parsed)
    keyword_score, keyword_detail = _score_keyword_density(resume_text, job_description)
    format_score,  format_detail  = _score_formatting(resume_text)
    exp_score,     exp_detail     = _score_experience_quality(resume_text, parsed)

    weights = {'skills': 0.40, 'keywords': 0.25, 'formatting': 0.20, 'experience': 0.15}

    overall = round(
        skills_score  * weights['skills']   +
        keyword_score * weights['keywords'] +
        format_score  * weights['formatting'] +
        exp_score     * weights['experience'],
        1
    )

    suggestions = _build_suggestions(skills_detail, keyword_detail, format_detail, exp_detail)

    return {
        'overall_score': overall,
        'grade':         _grade(overall),
        'components': {
            'skills_match':      round(skills_score,  1),
            'keyword_density':   round(keyword_score, 1),
            'formatting':        round(format_score,  1),
            'experience_quality': round(exp_score,    1),
        },
        'matched_keywords':  keyword_detail['matched'],
        'missing_keywords':  keyword_detail['missing'],
        'matched_skills':    skills_detail['matched'],
        'missing_skills':    skills_detail['missing'],
        'suggestions':       suggestions,
        'action_verbs_found': exp_detail['action_verbs'],
        'quantifiers_found':  exp_detail['quantifiers'],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Component scorers
# ─────────────────────────────────────────────────────────────────────────────

def _score_skills_match(resume_text: str, jd: str, parsed: dict):
    """TF-IDF cosine similarity between resume and job description."""
    if not jd.strip():
        return 70.0, {'matched': parsed.get('skills', []), 'missing': [], 'similarity': 0.70}

    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    try:
        tfidf = vectorizer.fit_transform([resume_text, jd])
        similarity = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
    except Exception:
        similarity = 0.5

    # Explicit skill matching against JD
    jd_lower = jd.lower()
    resume_skills = set(parsed.get('skills', []))
    jd_skills = {s for s in SKILL_KEYWORDS if s in jd_lower}
    matched = list(resume_skills & jd_skills)
    missing = list(jd_skills - resume_skills)

    skill_ratio = len(matched) / max(len(jd_skills), 1)
    score = (0.5 * similarity + 0.5 * skill_ratio) * 100
    score = max(0, min(100, score))

    return score, {'matched': matched, 'missing': missing[:10], 'similarity': round(similarity, 3)}


def _score_keyword_density(resume_text: str, jd: str):
    """Check how many important JD keywords appear in the resume."""
    if not jd.strip():
        return 65.0, {'matched': [], 'missing': [], 'density': 0}

    def tokenize(t):
        return set(re.findall(r'\b[a-zA-Z]{3,}\b', t.lower()))

    jd_words     = tokenize(jd)
    resume_words = tokenize(resume_text)

    # Remove generic stop words from JD terms
    stop = {'and', 'the', 'for', 'are', 'you', 'with', 'our', 'will', 'have',
            'this', 'that', 'from', 'your', 'not', 'but', 'can', 'all'}
    jd_keywords = jd_words - stop

    matched = list(jd_keywords & resume_words)
    missing = list(jd_keywords - resume_words)

    density = len(matched) / max(len(jd_keywords), 1)
    score = min(100, density * 120)  # allow over-match to reach 100

    return score, {
        'matched': sorted(matched)[:15],
        'missing': sorted(missing)[:15],
        'density': round(density, 3)
    }


def _score_formatting(resume_text: str):
    """Heuristic checks for ATS-friendly formatting."""
    score = 50.0
    detail = {'positives': [], 'negatives': []}

    # Positive signals
    for pattern in FORMATTING_POSITIVE:
        if re.search(pattern, resume_text, re.IGNORECASE):
            score += 10
            detail['positives'].append(pattern)

    # Negative signals
    for pattern in FORMATTING_NEGATIVE:
        hits = re.findall(pattern, resume_text)
        if len(hits) > 5:
            score -= 15
            detail['negatives'].append(f"Non-ASCII characters ({len(hits)} found)")

    # Word count check (ATS prefers 400–800 words)
    wc = len(resume_text.split())
    if wc < 200:
        score -= 20
        detail['negatives'].append(f"Too short ({wc} words)")
    elif wc > 1200:
        score -= 10
        detail['negatives'].append(f"Very long ({wc} words)")
    else:
        score += 10
        detail['positives'].append(f"Good length ({wc} words)")

    return max(0, min(100, score)), detail


def _score_experience_quality(resume_text: str, parsed: dict):
    """Check for action verbs and quantified achievements."""
    text_lower = resume_text.lower()
    words = set(text_lower.split())

    action_verbs_found = list(words & ACTION_VERBS)
    quantifiers = QUANTIFIER_PATTERN.findall(resume_text)

    verb_score  = min(100, len(action_verbs_found) * 10)
    quant_score = min(100, len(quantifiers) * 15)
    score = 0.5 * verb_score + 0.5 * quant_score

    return score, {
        'action_verbs': action_verbs_found,
        'quantifiers':  quantifiers,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _grade(score: float) -> str:
    if score >= 85: return 'A'
    if score >= 70: return 'B'
    if score >= 55: return 'C'
    if score >= 40: return 'D'
    return 'F'


def _build_suggestions(skills_d, keyword_d, format_d, exp_d) -> list[str]:
    tips = []
    if skills_d['missing']:
        tips.append(f"Add these missing skills: {', '.join(skills_d['missing'][:5])}")
    if keyword_d['missing']:
        tips.append(f"Include these JD keywords: {', '.join(keyword_d['missing'][:5])}")
    if format_d['negatives']:
        tips.extend(format_d['negatives'])
    if len(exp_d['action_verbs']) < 5:
        tips.append("Use more action verbs (e.g., developed, optimized, led)")
    if len(exp_d['quantifiers']) < 2:
        tips.append("Add quantified achievements (e.g., 'improved speed by 40%')")
    return tips
