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


def _candidate_json_to_text(candidate_profile) -> str:
    """
    Convert a candidate profile into a single text string for embedding.
    Handles multiple input formats:
      - Plain string (returned as-is)
      - Dict with 'content' or 'text' key (raw CV text)
      - Dict with 'skills'/'experience'/'education' keys (structured)
      - Any other dict (all string values concatenated)
    """
    if isinstance(candidate_profile, str):
        return candidate_profile

    if not isinstance(candidate_profile, dict):
        return str(candidate_profile)

    # Check for raw text keys first (most common from cv_parser_tool)
    for key in ("content", "text", "cv_text", "raw_text"):
        val = candidate_profile.get(key)
        if isinstance(val, str) and len(val) > 50:
            return val

    # Structured format
    sections = []

    skills = candidate_profile.get("skills")
    if isinstance(skills, list) and skills:
        sections.append("Skills: " + ", ".join(str(s) for s in skills))
    elif isinstance(skills, str) and skills.strip():
        sections.append("Skills: " + skills)

    experience = candidate_profile.get("experience")
    if isinstance(experience, list) and experience:
        sections.append("Experience: " + ". ".join(str(e) for e in experience))
    elif isinstance(experience, str) and experience.strip():
        sections.append("Experience: " + experience)

    education = candidate_profile.get("education")
    if isinstance(education, str) and education.strip():
        sections.append("Education: " + education)
    elif isinstance(education, list) and education:
        sections.append("Education: " + ", ".join(str(e) for e in education))

    if sections:
        return ". ".join(sections)

    # Fallback: concatenate all string values in the dict
    all_text = " ".join(
        str(v) for v in candidate_profile.values()
        if isinstance(v, str) and len(v) > 2
    )
    return all_text if all_text.strip() else str(candidate_profile)


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
    Rank a list of candidates based on semantic similarity to a job description.

    Each candidate dict can have any of these formats:
    - {"name": "...", "content": "<raw CV text>"}
    - {"name": "...", "skills": [...], "experience": [...]}
    - {"name": "...", "text": "<raw CV text>"}

    Args:
        candidates: List of candidate dicts.
        job_description: The job description to rank against.

    Returns:
        Sorted list (highest score first) with a 'score' field added.
    """
    if _model is None:
        return [{"error": "Sentence-transformer model not loaded"}]

    ranked = []
    for cand in candidates:
        # Convert to text for embedding
        cand_text = _candidate_json_to_text(cand)

        if not cand_text.strip():
            cand["score"] = 0.0
            ranked.append(cand)
            continue

        # Direct embedding comparison (bypass similarity_matcher_tool for speed)
        embeddings = _model.encode(
            [cand_text, job_description],
            normalize_embeddings=True
        )
        sim = float(cosine_similarity(
            embeddings[0].reshape(1, -1),
            embeddings[1].reshape(1, -1)
        )[0][0])

        cand["score"] = round(sim * 100, 2)
        ranked.append(cand)

    return sorted(ranked, key=lambda x: x.get("score", 0), reverse=True)


@tool
def rank_uploaded_cvs(job_description: str, file_paths: Optional[List[str]] = None) -> List[Dict]:
    """
    Parse AND rank all uploaded CVs against a job description in a single step.

    This is the preferred tool for ranking CVs — it handles file parsing internally
    so the full CV text never needs to pass through the conversation.

    Args:
        job_description: The full job description text to rank against.
        file_paths: Optional explicit list of file paths. If omitted, ALL files
                    in data/uploads/ are used automatically.

    Returns:
        Sorted list (highest score first) with name, score, and file path.
    """
    from pathlib import Path as _Path
    from .parsers import cv_parser_tool

    # Resolve file list
    if not file_paths:
        upload_dir = _Path("data/uploads")
        if upload_dir.exists():
            file_paths = [str(f) for f in upload_dir.glob("*") if f.is_file()]
        else:
            return [{"error": "No upload directory found and no file_paths provided."}]

    if not file_paths:
        return [{"error": "No CV files found to rank."}]

    if _model is None:
        return [{"error": "Sentence-transformer model not loaded"}]

    # 1. Parse every CV
    candidates = []
    for fp in file_paths:
        parsed = cv_parser_tool.invoke({"file_path": fp})
        name = parsed.get("metadata", {}).get("name", _Path(fp).name)
        content = parsed.get("content", "")
        if not content or not content.strip():
            candidates.append({"name": name, "file": fp, "score": 0.0, "note": "Could not extract text"})
            continue
        candidates.append({"name": name, "file": fp, "content": content})

    # 2. Rank via embedding similarity
    job_emb = _model.encode([job_description], normalize_embeddings=True)[0].reshape(1, -1)

    ranked = []
    for cand in candidates:
        if "note" in cand:          # already marked as failed
            ranked.append(cand)
            continue
        cand_text = cand.pop("content")  # keep text out of the returned dict
        cand_emb = _model.encode([cand_text], normalize_embeddings=True)[0].reshape(1, -1)
        sim = float(cosine_similarity(cand_emb, job_emb)[0][0])
        cand["score"] = round(sim * 100, 2)
        ranked.append(cand)

    return sorted(ranked, key=lambda x: x.get("score", 0), reverse=True)
