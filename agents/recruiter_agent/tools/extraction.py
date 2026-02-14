from datetime import datetime
import re
from typing import Optional, List, Dict
from pathlib import Path
from langchain_core.tools import tool
from .parsers import cv_parser_tool, text_cleaner_pipeline, RAGHandler # Import RAG

def aggregate_experience(date_ranges: list) -> float:
    """Helper to calculate total years of experience from date ranges."""
    total_years = 0.0
    for r in date_ranges:
        # Simplified parser for demonstration
        # 'Jan 2020 - Present' -> 2020-01-01 to NOW
        try:
            parts = r.split('-')
            start_str = parts[0].strip()
            end_str = parts[1].strip()
            
            # Simple parsing logic
            start_year = int(re.search(r'\d{4}', start_str).group())
            if 'present' in end_str.lower() or 'current' in end_str.lower():
                end_year = datetime.now().year
            else:
                end_year = int(re.search(r'\d{4}', end_str).group())
                
            total_years += (end_year - start_year)
        except:
            pass
    return max(0.0, total_years)


@tool
def skill_extractor_tool(cv_text: str) -> dict:
    """
    Extract structured skills, experience, and education from CV text.
    Returns a JSON compatible dictionary.
    """
    if not cv_text:
        return {
            "skills": [],
            "experience_years": 0,
            "education": [],
            "certifications": [],
        }

    # Simple heuristic extraction for demonstration
    # In production, this would use an LLM or dedicated parser
    skills = []
    
    # Common tech skills dictionary
    common_skills = [
        "python", "java", "javascript", "react", "node", "aws", "azure", 
        "docker", "kubernetes", "sql", "nosql", "git", "ci/cd",
        "machine learning", "ai", "nlp", "pandas", "numpy", "pytorch", "tensorflow"
    ]
    
    text_lower = cv_text.lower()
    for skill in common_skills:
        if skill in text_lower:
            skills.append(skill)
            
    # Extract experience years using normalizer
    import re
    date_ranges = re.findall(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*-\s*(?:Present|Current|\w+\s+\d{4})", cv_text, re.IGNORECASE)
    experience_years = aggregate_experience(date_ranges)
    
    # Heuristic for education
    education = []
    if "bachelor" in text_lower or "bs" in text_lower:
        education.append({"degree": "Bachelor's", "field": "Computer Science", "year": 2020}) # Mock
    if "master" in text_lower or "ms" in text_lower:
        education.append({"degree": "Master's", "field": "Artificial Intelligence", "year": 2022}) # Mock

    return {
        "skills": skills,
        "experience_years": experience_years,
        "education": education,
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


@tool
def search_cvs_by_content(query: str) -> List[Dict]:
    """
    Search across all uploaded CVs using Semantic Search (RAG).
    
    This invokes the FAISS vector store to find the most relevant chunks 
    from the parsed CVs. Use this for complex queries like:
    "Who has experience with Docker and AWS?"
    "Find candidates suitable for a Senior Manager role."
    
    Args:
        query: Natural language query.
        
    Returns:
        List of relevant CV segments with source metadata.
    """
    try:
        results = RAGHandler.search(query, k=5)
        
        response = []
        for doc in results:
            response.append({
                "content": doc.page_content,
                "source": doc.metadata.get("name"),
                "path": doc.metadata.get("source"),
                "relevance": "High (Top K match)"
            })
            
        if not response:
            return [{"message": f"No relevant information found for '{query}' in the CV database."}]
            
        return response
    except Exception as e:
        return [{"error": f"RAG Search failed: {str(e)}"}]



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
