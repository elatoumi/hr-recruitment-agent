"""
Job Scraping Tools

This module contains tools for scraping job postings from
LinkedIn, Indeed, and other job boards using Crawl4AI.

Group: Recruiter Agent (Group 1)

Tools:
- job_scraper_tool: Scrape job description as Markdown from LinkedIn/Indeed URLs
"""

import asyncio
import re
from typing import Optional, Dict, List
from langchain_core.tools import tool

try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


# CSS selectors for major job boards
LINKEDIN_SELECTORS = [
    ".show-more-less-html__markup",
    ".description__text",
    ".jobs-description__container",
]

INDEED_SELECTORS = [
    "#jobDescriptionText",
    ".jobsearch-jobDescriptionText",
]

SUPPORTED_BOARDS = {
    "linkedin.com": "LinkedIn",
    "indeed.com": "Indeed",
    "glassdoor.com": "Glassdoor",
}


def validate_job_url(url: str) -> Dict:
    """
    Validate if a URL is a supported job posting URL.

    Args:
        url: URL to validate.

    Returns:
        Validation result with detected job board.
    """
    if not url or not isinstance(url, str):
        return {"valid": False, "board": None, "error": "Empty or invalid URL"}

    url_lower = url.lower()
    if not url_lower.startswith(("http://", "https://")):
        return {"valid": False, "board": None, "error": "URL must start with http:// or https://"}

    for domain, board_name in SUPPORTED_BOARDS.items():
        if domain in url_lower:
            return {"valid": True, "board": board_name}

    # Allow any URL but flag as generic
    return {"valid": True, "board": "Generic"}


async def _fetch_page(url: str) -> str:
    """Fetch page HTML using Crawl4AI async crawler."""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        return result.html


def _extract_job_description(html: str, url: str) -> str:
    """Extract job description from HTML and convert to Markdown."""
    soup = BeautifulSoup(html, "html.parser")

    # Pick selectors based on URL
    if "indeed" in url.lower():
        selectors = INDEED_SELECTORS
    elif "linkedin" in url.lower():
        selectors = LINKEDIN_SELECTORS
    else:
        selectors = LINKEDIN_SELECTORS + INDEED_SELECTORS

    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            for tag in node(["script", "style", "button"]):
                tag.decompose()
            return md(str(node))

    # Fallback: find largest <p> block
    paragraphs = soup.find_all("p")
    big_block = max(paragraphs, key=lambda p: len(p.get_text()), default=None)
    if big_block:
        return md(str(big_block))

    # Last resort: grab all body text
    body = soup.find("body")
    if body:
        text = body.get_text(separator="\n", strip=True)
        if len(text) > 200:
            return text[:5000]

    raise ValueError("Could not locate job description container")


async def _scrape_job_markdown(url: str) -> str:
    """Core async scrape → Markdown pipeline."""
    html = await _fetch_page(url)
    markdown = _extract_job_description(html, url)
    if len(markdown.strip()) < 100:
        raise ValueError("Extracted content too small — likely blocked or empty")
    return markdown


def parse_job_requirements(job_description_md: str) -> Dict:
    """
    Parse job requirements from scraped Markdown.

    Uses heuristics to extract skills, qualifications, and responsibilities.

    Args:
        job_description_md: Job description in Markdown format.

    Returns:
        Structured requirements dict.
    """
    if not job_description_md:
        return {"required_skills": [], "preferred_skills": [], "responsibilities": []}

    text = job_description_md.lower()

    # Common tech skills to look for
    tech_skills = [
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node.js", "aws", "azure", "gcp", "docker", "kubernetes", "sql",
        "nosql", "mongodb", "postgresql", "git", "ci/cd", "machine learning",
        "deep learning", "nlp", "tensorflow", "pytorch", "pandas", "numpy",
        "c++", "c#", ".net", "go", "rust", "ruby", "php", "swift", "kotlin",
        "html", "css", "rest api", "graphql", "microservices", "agile", "scrum",
    ]

    found_skills = [s for s in tech_skills if s in text]

    # Try to extract bullet-point items from requirement sections
    required = []
    preferred = []

    lines = job_description_md.split("\n")
    section = None
    for line in lines:
        line_lower = line.lower().strip()
        if any(kw in line_lower for kw in ["requirement", "qualif", "must have", "essential"]):
            section = "required"
        elif any(kw in line_lower for kw in ["nice to have", "prefer", "bonus", "plus"]):
            section = "preferred"
        elif any(kw in line_lower for kw in ["responsibilit", "duties", "what you"]):
            section = None  # skip responsibilities for skills
        elif line.strip().startswith(("-", "*", "•")) and section:
            item = line.strip().lstrip("-*• ").strip()
            if item:
                if section == "required":
                    required.append(item)
                elif section == "preferred":
                    preferred.append(item)

    return {
        "required_skills": required if required else found_skills,
        "preferred_skills": preferred,
        "detected_technologies": found_skills,
    }


@tool
def job_scraper_tool(url: str) -> dict:
    """
    Scrape a job posting from LinkedIn, Indeed, or any URL and return as Markdown.

    The agent uses this when the user provides a job URL, e.g.:
    "Rank these CVs against this job link: https://linkedin.com/jobs/..."

    Args:
        url: URL of the job posting.

    Returns:
        A dictionary with job_description_md, requirements, and metadata.
    """
    # Validate URL
    validation = validate_job_url(url)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}

    if not CRAWL4AI_AVAILABLE or not BS4_AVAILABLE:
        return {
            "success": False,
            "error": "Missing dependencies: crawl4ai, beautifulsoup4, or markdownify. "
                     "Install with: pip install crawl4ai beautifulsoup4 markdownify",
        }

    try:
        # Run the async scraper
        markdown = asyncio.run(_scrape_job_markdown(url))

        # Parse requirements from the markdown
        requirements = parse_job_requirements(markdown)

        return {
            "success": True,
            "job_description_md": markdown,
            "board": validation["board"],
            "requirements": requirements,
            "url": url,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Scraping failed: {str(e)}",
            "url": url,
        }
