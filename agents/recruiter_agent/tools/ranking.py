"""
Candidate Ranking Tools

This module contains tools for computing similarity between
candidates and job requirements, and explaining match results.

Group: Recruiter Agent (Group 1)

Tools:
- similarity_matcher_tool: BERT/sentence-transformers cosine similarity
- match_explainer: Gap analysis ("Matches Python, missing AWS")
- cv_ranker: Rank multiple candidates against a job description
"""

from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from .match_explainer import MatchExplainer, analyze_candidate_match

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    _model = SentenceTransformer("all-MiniLM-L6-v2")
except ImportError:
    _model = None
    print("Warning: sentence-transformers, sklearn or numpy not installed.")
except Exception as e:
    _model = None
    print(f"Warning: Could not load SentenceTransformer: {e}")


def _candidate_json_to_text(candidate_profile: dict) -> str:
    """
    Convert structured candidate JSON into a single text string
    suitable for semantic embedding.
    """
    sections = []

    skills = candidate_profile.get("skills")
    if isinstance(skills, list) and skills:
        sections.append("Skills: " + ", ".join(skills))

    experience = candidate_profile.get("experience")
    if isinstance(experience, list) and experience:
        sections.append("Experience: " + ". ".join(experience))

    education = candidate_profile.get("education")
    if isinstance(education, str) and education.strip():
        sections.append("Education: " + education)

    return ". ".join(sections)


@tool
def similarity_matcher_tool(
    candidate_skills: dict,
    job_description: str
) -> dict:
    """
    Compute cosine similarity between candidate skills and job description.
    
    Uses sentence-transformers (BERT) for semantic matching.
    
    Args:
        candidate_skills: JSON dict of candidate skills from skill_extractor.
        job_description: Job description text or markdown.
    
    Returns:
        A dictionary containing:
        - similarity_score: Float 0-100 cosine similarity
        - confidence: Confidence level of the match
    """
    if _model is None:
        return {"error": "Model not loaded", "similarity_score": 0.0}

    if not candidate_skills or not job_description:
        return {"similarity_score": 0.0}

    candidate_text = _candidate_json_to_text(candidate_skills)

    embeddings = _model.encode(
        [candidate_text, job_description],
        normalize_embeddings=True
    )

    candidate_embedding = embeddings[0].reshape(1, -1)
    job_embedding = embeddings[1].reshape(1, -1)

    similarity = cosine_similarity(candidate_embedding, job_embedding)[0][0]

    return {
        "similarity_score": round(float(similarity) * 100, 2)
    }


@tool
def match_explainer(
    candidate_skills: dict,
    job_requirements: dict,
    similarity_score: float = 0.0
) -> dict:
    """
    Explain the match with gap analysis.
    
    Don't just return a score (e.g., "85%"). Return the Gap Analysis:
    "Matches on Python and SQL, but missing AWS certification."
    
    Args:
        candidate_skills: Candidate's extracted skills dict.
        job_requirements: Required and preferred skills from JD.
        similarity_score: Pre-computed similarity score.
    
    Returns:
        A dictionary containing:
        - score_display: Formatted score (e.g., "85%")
        - matched_skills: List of matching skills
        - missing_skills: List of required skills candidate lacks
        - gap_summary: Human-readable gap analysis string
        - recommendation: Hire/Consider/Pass recommendation
    """
    # Assuming MatchExplainer handles dict inputs now or we need to adapt
    # The MatchExplainer in match_explainer.py seems to take lists
    
    # Extract lists from dicts
    c_skills = candidate_skills.get("skills", [])
    j_reqs = job_requirements.get("required", []) + job_requirements.get("preferred", [])
    
    explainer = MatchExplainer()
    result = explainer.explain(c_skills, j_reqs)
    
    match_score = result.get("match_score", 0)
    
    if match_score >= 80:
        recommendation = "Hire"
    elif match_score >= 60:
        recommendation = "Consider"
    else:
        recommendation = "Pass"
    
    return {
        "score_display": f"{match_score}%",
        "matched_skills": result.get("matches", []),
        "missing_skills": result.get("gaps", []),
        "gap_summary": result.get("explanation", ""),
        "recommendation": recommendation
    }

@tool
def cv_ranker(candidates: List[Dict], job_description: str) -> List[Dict]:
    """
    Rank a list of candidates based on similarity to job description.
    """
    ranked = []
    for cand in candidates:
        score = similarity_matcher_tool(cand, job_description).get("similarity_score", 0)
        cand["score"] = score
        ranked.append(cand)
    
    return sorted(ranked, key=lambda x: x["score"], reverse=True)
