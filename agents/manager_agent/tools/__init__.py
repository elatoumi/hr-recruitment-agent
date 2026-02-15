"""
Hiring Manager Agent Tools - Group 2 Workspace

This package contains all tools for the Hiring Manager Agent:
- retrieval.py: ChromaDB template retrieval
- generation.py: Offer generation and validation
"""

from .retrieval import (
    find_template,
    ingest_templates_to_chromadb,
    get_template,
    list_available_templates,
    add_template,
)
from .generation import (
    job_offer_generator,
    offer_validator_tool,
    market_salary_check,
    get_salary_range,
)

__all__ = [
    # Retrieval
    "find_template",
    "ingest_templates_to_chromadb",
    "get_template",
    "list_available_templates",
    "add_template",
    # Generation & Validation
    "job_offer_generator",
    "offer_validator_tool",
    "market_salary_check",
    "get_salary_range",
]
