"""
Skill Extraction Tools

This module contains tools for extracting skills, generating summaries,
and normalizing experience data from CV text.

Group: Recruiter Agent (Group 1)

Tools:
- skill_extractor_tool: Structured JSON output (Skills, Exp, Education, Certs)
- candidate_summarizer: 3-sentence executive summary for Supervisor
- experience_normalizer: Convert date formats to total_years_experience
"""

from typing import Optional
from langchain_core.tools import tool


# JSON Schema for structured skill extraction output
SKILL_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of technical and soft skills"
        },
        "experience_years": {
            "type": "integer",
            "description": "Total years of professional experience"
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "degree": {"type": "string"},
                    "field": {"type": "string"},
                    "institution": {"type": "string"},
                    "year": {"type": "integer"}
                }
            }
        },
        "certifications": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Professional certifications"
        }
    },
    "required": ["skills", "experience_years", "education", "certifications"]
}


@tool
def skill_extractor_tool(cv_text: str) -> dict:
    """
    Extract structured data from CV text using LLM with strict JSON Schema.
    
    Forces a structured output: Skills, Experience Years, Education, Certs.
    Must handle cases where the CV is empty or garbage.
    
    Args:
        cv_text: The CV text to analyze.
    
    Returns:
        A dictionary matching SKILL_EXTRACTION_SCHEMA containing:
        - skills: List of extracted skills
        - experience_years: Total years of experience (integer)
        - education: List of education entries
        - certifications: List of certifications
    """
    # TODO: Create Prompt Template, use with_structured_output, handle empty/garbage input
    raise NotImplementedError("Implement skill_extractor_tool")


def extract_skills(text: str) -> dict:
    """
    Core skill extraction function (non-tool version).
    
    Args:
        text: CV text to analyze.
    
    Returns:
        Extracted skills dictionary.
    """
    # TODO: Implement core extraction logic
    raise NotImplementedError("Implement extract_skills")


@tool
def candidate_summarizer(cv_text: str, extracted_skills: Optional[dict] = None) -> str:
    """
    Generate a 3-sentence executive summary of a candidate.
    
    Example output: "Senior Python dev with 5 years exp, lacking cloud skills."
    The Supervisor needs this summary to show the user in the chat.
    
    Args:
        cv_text: The full CV text.
        extracted_skills: Optional pre-extracted skills dict.
    
    Returns:
        A concise 3-sentence summary string.
    """
    # TODO: Create prompt for concise summarization, highlight strengths and gaps
    raise NotImplementedError("Implement candidate_summarizer")


def experience_normalizer(date_string: str) -> int:
    """
    Convert varied date formats to total years of experience.
    
    Handles formats like:
    - "Jan 2020 - Present"
    - "2019-2021"
    - "March 2018 - December 2022"
    - "5 years"
    
    Args:
        date_string: Raw date range string from CV.
    
    Returns:
        Integer representing total years of experience.
    """
    # TODO: Parse various date formats, handle "Present"/"Current", calculate duration
    raise NotImplementedError("Implement experience_normalizer")


def aggregate_experience(date_ranges: list[str]) -> int:
    """
    Aggregate multiple work experiences into total years.
    
    Args:
        date_ranges: List of date range strings from work history.
    
    Returns:
        Total years of experience (avoiding overlap if possible).
    """
    # TODO: Handle overlapping date ranges
    raise NotImplementedError("Implement aggregate_experience")
