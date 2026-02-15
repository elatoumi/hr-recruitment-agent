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

import re
from typing import Optional
from langchain_core.tools import tool


# ============================================================
# SALARY DATA (mock – replace with API / DB in production)
# ============================================================

SALARY_RANGES = {
    "engineer":   {"min": 80000,  "max": 150000, "median": 115000},
    "developer":  {"min": 75000,  "max": 145000, "median": 110000},
    "manager":    {"min": 100000, "max": 200000, "median": 150000},
    "director":   {"min": 130000, "max": 250000, "median": 190000},
    "sales":      {"min": 50000,  "max": 120000, "median": 85000, "commission": True},
    "analyst":    {"min": 60000,  "max": 110000, "median": 85000},
    "designer":   {"min": 65000,  "max": 130000, "median": 95000},
    "intern":     {"min": 25000,  "max": 45000,  "median": 35000},
    "default":    {"min": 60000,  "max": 100000, "median": 80000},
}

LOCATION_MULTIPLIERS = {
    "san francisco": 1.25,
    "new york": 1.20,
    "london": 1.15,
    "berlin": 0.95,
    "remote": 1.00,
    "tunis": 0.55,
    "paris": 1.10,
}


def _match_role_key(role: str) -> str:
    """Find the best matching salary key for a role string."""
    role_lower = role.lower()
    for key in SALARY_RANGES:
        if key in role_lower:
            return key
    return "default"


def _get_multiplier(location: Optional[str]) -> float:
    if not location:
        return 1.0
    loc_lower = location.lower()
    for key, mult in LOCATION_MULTIPLIERS.items():
        if key in loc_lower:
            return mult
    return 1.0


def get_salary_range(role: str, location: Optional[str] = None) -> dict:
    """
    Get market salary range for a role (non-tool helper).

    Args:
        role: Job role/title.
        location: Optional location for regional adjustment.

    Returns:
        Salary range dictionary with min, max, median, currency.
    """
    key = _match_role_key(role)
    base = SALARY_RANGES[key]
    mult = _get_multiplier(location)

    return {
        "min": int(base["min"] * mult),
        "max": int(base["max"] * mult),
        "median": int(base["median"] * mult),
        "currency": "USD",
        "location": location or "US (Remote)",
        "source": "Mock Market Data",
    }


# ============================================================
# TOOLS
# ============================================================

@tool
def job_offer_generator(
    template: str,
    candidate_data: dict,
    job_data: dict,
) -> dict:
    """
    Generate a personalized job offer by filling a template with candidate and job data.

    Replaces {{placeholder}} and {placeholder} style variables with matching values
    from candidate_data and job_data.

    Args:
        template: Template string with {{variable}} or {variable} placeholders.
        candidate_data: Dict with candidate info (e.g. name, email, skills).
        job_data: Dict with job info (e.g. title, salary, location, start_date).

    Returns:
        A dictionary with the filled offer text and validation info.
    """
    if not template:
        return {"success": False, "error": "No template provided", "offer_text": ""}

    # Merge both dicts so any key can be resolved
    context = {}
    if candidate_data:
        context.update({k.lower(): v for k, v in candidate_data.items()})
    if job_data:
        context.update({k.lower(): v for k, v in job_data.items()})

    offer_text = template

    # Replace {{key}} style placeholders
    for key, value in context.items():
        offer_text = offer_text.replace(f"{{{{{key}}}}}", str(value))
        offer_text = offer_text.replace(f"{{{key}}}", str(value))

    # Also try with original case keys
    if candidate_data:
        for key, value in candidate_data.items():
            offer_text = offer_text.replace(f"{{{{{key}}}}}", str(value))
            offer_text = offer_text.replace(f"{{{key}}}", str(value))
    if job_data:
        for key, value in job_data.items():
            offer_text = offer_text.replace(f"{{{{{key}}}}}", str(value))
            offer_text = offer_text.replace(f"{{{key}}}", str(value))

    # Detect remaining unfilled placeholders
    remaining = re.findall(r"\{\{.*?\}\}|\{[^}]+\}", offer_text)

    return {
        "success": True,
        "offer_text": offer_text,
        "unfilled_placeholders": remaining,
        "complete": len(remaining) == 0,
    }


@tool
def offer_validator_tool(content: str) -> dict:
    """
    Validate a generated job offer for completeness.
    Checks for unfilled placeholders and missing critical sections.

    Args:
        content: The generated offer / email text to validate.

    Returns:
        A dictionary with validity status, warnings, and suggestions.
    """
    if not content or len(content.strip()) < 50:
        return {
            "valid": False,
            "unfilled_placeholders": [],
            "warnings": ["Offer text is empty or too short (must be ≥50 chars)"],
            "suggestions": ["Provide a complete job offer text"],
        }

    # Detect {{…}}, {…}, and [INSERT …] style placeholders
    placeholders = re.findall(r"\{\{.*?\}\}|\{[^}]+\}|\[INSERT.*?\]|\[CANDIDATE.*?\]|\[SALARY.*?\]", content, re.IGNORECASE)

    # Check critical fields
    critical_fields = ["salary", "title", "location", "contract"]
    warnings = []
    text_lower = content.lower()
    for field in critical_fields:
        if field not in text_lower:
            warnings.append(f"Missing critical field: {field}")

    is_valid = len(placeholders) == 0 and len(warnings) == 0

    return {
        "valid": is_valid,
        "unfilled_placeholders": placeholders,
        "warnings": warnings,
        "suggestions": [f"Fill placeholder {ph}" for ph in placeholders],
    }


@tool
def market_salary_check(role: str, offered_salary: Optional[float] = None, location: Optional[str] = None) -> dict:
    """
    Check if offered salary is within market range for a given role.

    If offered_salary is provided, flags whether it is low/high/ok.
    Otherwise just returns the market range.

    Args:
        role: Job role or title.
        offered_salary: (Optional) The salary amount to compare.
        location: (Optional) Location for regional adjustment.

    Returns:
        Market range, deviation info, and recommendations.
    """
    salary_range = get_salary_range(role, location)
    result = {
        "market_min": salary_range["min"],
        "market_max": salary_range["max"],
        "market_median": salary_range["median"],
        "market_range": f"${salary_range['min']:,} – ${salary_range['max']:,}",
        "currency": salary_range["currency"],
        "location": salary_range["location"],
        "source": salary_range["source"],
    }

    if offered_salary is not None:
        median = salary_range["median"]
        deviation = ((offered_salary - median) / median) * 100 if median else 0

        if offered_salary < salary_range["min"]:
            flag = "low"
            recommendation = f"Offered salary ${offered_salary:,.0f} is below market minimum. Consider raising to at least ${salary_range['min']:,}."
        elif offered_salary > salary_range["max"]:
            flag = "high"
            recommendation = f"Offered salary ${offered_salary:,.0f} exceeds market maximum. Verify budget approval."
        else:
            flag = "ok"
            recommendation = "Salary is within market range."

        result.update({
            "offered_salary": offered_salary,
            "within_range": flag == "ok",
            "deviation_percent": round(deviation, 1),
            "flag": flag,
            "recommendation": recommendation,
        })

    return result


# Legacy helper
def validate_offer(content: str) -> dict:
    """Legacy wrapper around offer_validator_tool."""
    return offer_validator_tool.invoke({"content": content})
