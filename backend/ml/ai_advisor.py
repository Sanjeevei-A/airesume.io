"""
backend/ml/ai_advisor.py
========================
Advanced add-on: uses OpenAI GPT-4o or Google Gemini to generate
intelligent resume improvement suggestions.
"""

import os
import openai
import google.generativeai as genai
from config import Config


# ─────────────────────────────────────────────────────────────────────────────
# Initialise clients (lazy — only if keys are set)
# ─────────────────────────────────────────────────────────────────────────────

def _openai_client():
    key = Config.OPENAI_API_KEY
    if not key:
        raise EnvironmentError("OPENAI_API_KEY not set in environment.")
    openai.api_key = key
    return openai


def _gemini_model():
    key = Config.GEMINI_API_KEY
    if not key:
        raise EnvironmentError("GEMINI_API_KEY not set in environment.")
    genai.configure(api_key=key)
    return genai.GenerativeModel('gemini-1.5-flash')


# ─────────────────────────────────────────────────────────────────────────────
# Shared prompt builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_prompt(resume_text: str, job_description: str, ats_score: float) -> str:
    jd_section = f"\n\nJOB DESCRIPTION:\n{job_description}" if job_description.strip() else ""
    return f"""You are an expert career coach and resume writer.
A candidate has submitted their resume with an ATS score of {ats_score}/100.{jd_section}

RESUME:
{resume_text[:3000]}

Provide EXACTLY the following JSON structure (no markdown, no extra text):
{{
  "overall_feedback": "2-3 sentence summary of the resume strength",
  "top_strengths": ["strength 1", "strength 2", "strength 3"],
  "critical_improvements": [
    {{"issue": "...", "fix": "...", "example": "..."}},
    {{"issue": "...", "fix": "...", "example": "..."}},
    {{"issue": "...", "fix": "...", "example": "..."}}
  ],
  "bullet_rewrites": [
    {{"original": "...", "improved": "..."}},
    {{"original": "...", "improved": "..."}}
  ],
  "missing_sections": ["..."],
  "ats_tips": ["tip 1", "tip 2", "tip 3"]
}}"""


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_openai_suggestions(resume_text: str, job_description: str = "", ats_score: float = 0.0) -> dict:
    """
    Call OpenAI GPT-4o and return structured suggestions.
    """
    client = _openai_client()
    prompt = _build_prompt(resume_text, job_description, ats_score)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1200,
        response_format={"type": "json_object"},
    )
    import json
    raw = response.choices[0].message.content
    return json.loads(raw)


def get_gemini_suggestions(resume_text: str, job_description: str = "", ats_score: float = 0.0) -> dict:
    """
    Call Google Gemini and return structured suggestions.
    """
    model  = _gemini_model()
    prompt = _build_prompt(resume_text, job_description, ats_score)

    response = model.generate_content(prompt)
    import json, re
    raw = response.text
    # Strip any accidental markdown fences
    raw = re.sub(r'```(?:json)?', '', raw).strip()
    return json.loads(raw)


def get_suggestions(resume_text: str, job_description: str = "", ats_score: float = 0.0,
                    provider: str = "gemini") -> dict:
    """
    Unified entry point. Tries the requested provider, falls back to the other.
    provider: "openai" | "gemini"
    """
    try:
        if provider == "openai":
            return get_openai_suggestions(resume_text, job_description, ats_score)
        else:
            return get_gemini_suggestions(resume_text, job_description, ats_score)
    except Exception as primary_err:
        # Fallback
        try:
            if provider == "openai":
                return get_gemini_suggestions(resume_text, job_description, ats_score)
            else:
                return get_openai_suggestions(resume_text, job_description, ats_score)
        except Exception:
            return {
                "error": str(primary_err),
                "overall_feedback": "AI suggestions unavailable. Please set OPENAI_API_KEY or GEMINI_API_KEY.",
            }
