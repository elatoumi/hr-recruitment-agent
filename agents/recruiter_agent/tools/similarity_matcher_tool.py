
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


_model = SentenceTransformer("all-MiniLM-L6-v2")


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


def similarity_matcher_tool(candidate_profile: dict, job_description: str) -> dict:
    """
    Compute semantic similarity score between a candidate profile
    and a job description.

    Returns:
    {
        "similarity_score": float (0–100)
    }
    """

    if not candidate_profile or not job_description:
        return {"similarity_score": 0.0}

    candidate_text = _candidate_json_to_text(candidate_profile)

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

