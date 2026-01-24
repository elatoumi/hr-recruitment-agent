"""
Hiring Manager Agent Tools - Group 2 Workspace

This package contains all tools for the Hiring Manager Agent:
- retrieval.py: ChromaDB template retrieval
- generation.py: Offer generation and validation
"""

from .retrieval import template_retriever_tool, get_template, ingest_templates_to_chromadb
from .generation import job_offer_generator, offer_validator_tool, market_salary_check

__all__ = [
    # Retrieval
    "template_retriever_tool",
    "get_template",
    "ingest_templates_to_chromadb",
    # Generation & Validation
    "job_offer_generator",
    "offer_validator_tool",
    "market_salary_check",
]
