"""
backend/ml/job_recommender.py
==============================
Recommends job roles that best match the candidate's resume using
TF-IDF vectorization + cosine similarity against curated role profiles.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ─── Role profiles ────────────────────────────────────────────────────────────
# Each role is represented by a bag of relevant skills/keywords.
# Extend this dict freely to add more roles.

ROLE_PROFILES = {
    "Data Scientist": (
        "python machine learning deep learning scikit-learn tensorflow pytorch "
        "pandas numpy statistics data analysis visualization matplotlib seaborn "
        "sql regression classification clustering feature engineering nlp "
        "jupyter notebook model evaluation a/b testing"
    ),
    "ML Engineer": (
        "python machine learning model deployment mlops docker kubernetes "
        "fastapi flask tensorflow pytorch scikit-learn feature store "
        "pipeline automation ci/cd aws sagemaker gcp vertex ai monitoring "
        "model optimization quantization serving"
    ),
    "NLP Engineer": (
        "nlp natural language processing spacy nltk transformers huggingface "
        "bert gpt text classification named entity recognition sentiment analysis "
        "python pytorch tensorflow language models fine-tuning tokenization"
    ),
    "Frontend Developer": (
        "html css javascript typescript react angular vue nextjs tailwind "
        "webpack vite responsive design ui ux accessibility rest api "
        "git figma animation component library"
    ),
    "Backend Developer": (
        "python java nodejs golang flask django fastapi spring express "
        "rest api graphql sql postgresql mongodb redis microservices "
        "docker kubernetes ci/cd git authentication authorization"
    ),
    "Full Stack Developer": (
        "html css javascript react nodejs express python flask django "
        "sql mongodb rest api git docker aws deployment responsive "
        "typescript tailwind authentication jwt"
    ),
    "DevOps Engineer": (
        "docker kubernetes jenkins gitlab ci/cd terraform ansible aws azure "
        "gcp linux bash scripting monitoring prometheus grafana "
        "infrastructure as code cloud networking security"
    ),
    "Data Analyst": (
        "sql excel python pandas tableau power bi data visualization "
        "statistics business intelligence reporting dashboard "
        "data cleaning pivot tables data storytelling"
    ),
    "Cloud Architect": (
        "aws azure gcp cloud architecture microservices serverless "
        "terraform kubernetes docker networking security iam "
        "cost optimization disaster recovery scalability"
    ),
    "Cybersecurity Analyst": (
        "penetration testing vulnerability assessment security protocols "
        "firewall siem wireshark nmap metasploit python linux "
        "incident response threat intelligence compliance owasp"
    ),
    "Android Developer": (
        "android kotlin java jetpack compose xml retrofit room "
        "mvvm coroutines firebase google play api rest "
        "unit testing espresso git"
    ),
    "iOS Developer": (
        "swift objective-c xcode ios uikit swiftui core data "
        "combine rest api cocoapods spm wwdc app store "
        "unit testing xctest git"
    ),
    "Product Manager": (
        "product roadmap agile scrum user stories backlog prioritization "
        "stakeholder management a/b testing analytics kpi okr "
        "figma jira confluence market research"
    ),
    "UI/UX Designer": (
        "figma sketch adobe xd user research wireframing prototyping "
        "design systems accessibility usability testing information architecture "
        "typography color theory interaction design"
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def recommend_jobs(resume_text: str, top_n: int = 5) -> list[dict]:
    """
    Returns the top-N job role recommendations with similarity scores.

    Parameters
    ----------
    resume_text : str
        Full text of the candidate's resume.
    top_n : int
        Number of recommendations to return.

    Returns
    -------
    list of dicts with keys: role, score, match_pct, description
    """
    roles   = list(ROLE_PROFILES.keys())
    corpora = list(ROLE_PROFILES.values())

    # Fit TF-IDF on role corpora + resume together
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    all_docs = corpora + [resume_text]
    tfidf_matrix = vectorizer.fit_transform(all_docs)

    resume_vec = tfidf_matrix[-1]                  # last row = resume
    role_vecs  = tfidf_matrix[:-1]                 # all other rows = roles

    similarities = cosine_similarity(resume_vec, role_vecs).flatten()

    # Rank and build result
    ranked_indices = np.argsort(similarities)[::-1][:top_n]

    recommendations = []
    for idx in ranked_indices:
        score = float(similarities[idx])
        recommendations.append({
            'role':       roles[idx],
            'score':      round(score, 4),
            'match_pct':  round(score * 100, 1),
            'keywords':   _top_keywords(ROLE_PROFILES[roles[idx]]),
        })

    return recommendations


def get_skill_gap(resume_text: str, target_role: str) -> dict:
    """
    Given a target role, return the skills the candidate already has
    and those they should acquire.
    """
    if target_role not in ROLE_PROFILES:
        return {'error': f"Role '{target_role}' not found in profiles."}

    role_keywords = set(ROLE_PROFILES[target_role].lower().split())
    resume_words  = set(resume_text.lower().split())

    present = sorted(role_keywords & resume_words)
    missing = sorted(role_keywords - resume_words)

    return {
        'role':    target_role,
        'present': present,
        'missing': missing,
        'gap_pct': round(len(missing) / max(len(role_keywords), 1) * 100, 1),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _top_keywords(profile_text: str, n: int = 6) -> list[str]:
    """Return the first n keywords from the role profile."""
    words = profile_text.split()
    seen, result = set(), []
    for w in words:
        if w not in seen:
            seen.add(w)
            result.append(w)
        if len(result) == n:
            break
    return result
