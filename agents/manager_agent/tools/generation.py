"""
Content Generation Tools

This module contains tools for generating and validating job offers,
and checking market salary ranges.

Group: Hiring Manager Agent (Group 2)

Tools:
- job_offer_generator: Generate personalized job offers from templates
- offer_validator_tool: Sanity check for placeholders
- market_salary_check: Validate salary against market ranges
"""

from typing import Optional
from langchain_core.tools import tool


@tool
def job_offer_generator(
    template: str,
    candidate_data: dict,
    job_data: dict
) -> dict:
    """
    Generate a personalized job offer from a template.
    
    Args:
        template: Template string with {variable} placeholders.
        candidate_data: Dict with candidate info.
        job_data: Dict with job info.
    
    Returns:
        Generated offer content.
    """
    # TODO: Implement template filling logic
    raise NotImplementedError("Implement job_offer_generator")


import re

@tool
def offer_validator_tool(generated_text):
    """
    Sanity check for generated offer text.
    
    Checks that placeholders like [INSERT SALARY] or [CANDIDATE NAME]
    have been properly replaced before sending.
    
    Args:
        generated_text: The generated offer/email text to validate.
    
    Returns:
        A dictionary containing:
        - valid: Boolean indicating if text is ready to send
        - unfilled_placeholders: List of placeholders still present
        - warnings: List of potential issues
        - suggestions: Recommended fixes
    """

    # Safety check for empty or too short text
    if not generated_text or len(generated_text.strip()) < 50:
        return {
            "valid": False,
            "unfilled_placeholders": [],
            "warnings": ["Offer text is empty or too short"],
            "suggestions": ["Provide a complete job offer text"]
        }

    # Detect placeholders like [INSERT SALARY], [CANDIDATE NAME], etc.
    placeholders = re.findall(r"\[.*?\]", generated_text)

    # Check for presence of critical fields
    critical_fields = ["salary", "job title", "location", "contract"]
    warnings = []
    text_lower = generated_text.lower()
    for field in critical_fields:
        if field not in text_lower:
            warnings.append(f"Missing critical field: {field}")

    # Build suggestions for placeholders
    suggestions = [f"Replace placeholder {ph}" for ph in placeholders]

    # Determine overall validity
    is_valid = len(placeholders) == 0 and len(warnings) == 0

    return {
        "valid": is_valid,
        "unfilled_placeholders": placeholders,
        "warnings": warnings,
        "suggestions": suggestions
    }


@tool
def market_salary_check(
    role: str,
    offered_salary: float,
    location: Optional[str] = None
) -> dict:
    """
    Check if offered salary is within market range.
    
    Uses a dictionary of salary ranges to flag if the 
    generated offer salary is too low (or too high).
    
    Args:
        role: Job role/title to check.
        offered_salary: The salary amount in the offer.
        location: Optional location for regional adjustment.
    
    Returns:
        A dictionary containing:
        - within_range: Boolean indicating if salary is acceptable
        - market_min: Minimum market salary for role
        - market_max: Maximum market salary for role
        - market_median: Median market salary
        - deviation_percent: How far from median (+ or -)
        - flag: 'low', 'high', or 'ok'
        - recommendation: Suggested action if out of range
    """
    # TODO: Create dictionary of salary ranges, compare and flag if too low/high
    raise NotImplementedError("Implement market_salary_check")



def validate_offer(content):
    # Check si le texte est vide ou trop court
    if not content or len(content.strip()) < 50:
        return {
            "valid": False,
            "unfilled_placeholders": [],
            "warnings": ["Offer text is empty or too short"],
            "suggestions": ["Provide a complete job offer text"]
        }

    # Trouver les placeholders
    placeholders = re.findall(r"\[.*?\]", content)

    # Vérifier les champs critiques
    critical_fields = ["salary", "job title", "location", "contract"]
    warnings = []
    text_lower = content.lower()
    for field in critical_fields:
        if field not in text_lower:
            warnings.append(f"Missing critical field: {field}")

    # Suggestions pour les placeholders
    suggestions = [f"Replace placeholder {ph}" for ph in placeholders]

    # Validation globale
    is_valid = len(placeholders) == 0 and len(warnings) == 0

    return {
        "valid": is_valid,
        "unfilled_placeholders": placeholders,
        "warnings": warnings,
        "suggestions": suggestions
    }


def get_salary_range(role: str, location: Optional[str] = None) -> dict:
    """
    Get market salary range for a role.
    
    Args:
        role: Job role/title.
        location: Optional location.
    
    Returns:
        Salary range dictionary.
    """
    # TODO: Implement salary lookup (mock data ok)
    raise NotImplementedError("Implement get_salary_range")
