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
    Generate a concise executive summary of the candidate's profile.
    """
    return "Candidate summary unavailable."


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
