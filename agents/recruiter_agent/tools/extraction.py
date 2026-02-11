from datetime import datetime
import re
from typing import Optional, List
from langchain_core.tools import tool


@tool
def skill_extractor_tool(cv_text: str) -> dict:
    """
    Extract structured skills, experience, and education from CV text.
    Returns a JSON compatible dictionary.
    """
    return {
        "skills": [],
        "experience_years": 0,
        "education": [],
        "certifications": [],
    }


def extract_skills(text: str) -> dict:
    return {
        "skills": [],
        "experience_years": 0,
        "education": [],
        "certifications": [],
    }


@tool
def candidate_summarizer(cv_text: str, extracted_skills: Optional[dict] = None) -> str:
    """
    Generate a 3-sentence executive summary of a candidate.
    """

    # Safety check: empty or unusable CV
    if not cv_text or len(cv_text.strip()) < 30:
        return "Insufficient information available to generate a candidate summary."

    # Defaults
    skills = []
    experience_years = None
    education = []

    # Use extracted skills if provided
    if extracted_skills:
        skills = extracted_skills.get("skills", [])
        experience_years = extracted_skills.get("experience_years")
        education = extracted_skills.get("education", [])

    # Build summary components
    skills_str = ", ".join(skills[:5]) if skills else "relevant technical skills"

    experience_str = (
        f"{experience_years} years of professional experience"
        if isinstance(experience_years, int)
        else "a professional background in the field"
    )

    education_str = ""
    if education and isinstance(education, list):
        degree = education[0].get("degree", "")
        field = education[0].get("field", "")
        if degree or field:
            education_str = f" Holds a {degree} in {field}."

    # Final 3-sentence summary
    summary = (
        f"Candidate with {experience_str}. "
        f"Key strengths include {skills_str}. "
        f"{education_str or 'Profile suitable for further technical assessment.'}"
    )

    return summary.strip()


def _parse_year(value: str) -> Optional[int]:
    match = re.search(r"\b(19|20)\d{2}\b", value)
    return int(match.group()) if match else None


def _parse_month_year(value: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value.strip(), "%b %Y")
    except ValueError:
        try:
            return datetime.strptime(value.strip(), "%B %Y")
        except ValueError:
            return None


def experience_normalizer(date_string: str) -> int:
    if not date_string:
        return 0

    text = date_string.lower().strip()
    now = datetime.now()

    match_years = re.search(r"(\d+)\s+years?", text)
    if match_years:
        return int(match_years.group(1))

    if "present" in text or "current" in text:
        parts = re.split(r"-|to", text)
        start = _parse_month_year(parts[0].title()) or (
            datetime(_parse_year(parts[0]), 1, 1)
            if _parse_year(parts[0])
            else None
        )
        if start:
            return max(0, now.year - start.year)

    years = re.findall(r"\b(19|20)\d{2}\b", text)
    if len(years) >= 2:
        return abs(int(years[1]) - int(years[0]))

    parts = re.split(r"-|to", text)
    if len(parts) == 2:
        start = _parse_month_year(parts[0].title())
        end = _parse_month_year(parts[1].title())
        if start and end:
            return max(0, end.year - start.year)

    year = _parse_year(text)
    if year:
        return max(0, now.year - year)

    return 0


def aggregate_experience(date_ranges: List[str]) -> int:
    total = 0
    for date_range in date_ranges:
        total += experience_normalizer(date_range)
    return total
