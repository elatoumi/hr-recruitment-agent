import asyncio
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from crawl4ai import AsyncWebCrawler
from langchain.tools import tool

LINKEDIN_SELECTORS = [
    ".show-more-less-html__markup",
    ".description__text",
    ".jobs-description__container"
]

INDEED_SELECTORS = [
    "#jobDescriptionText",
    ".jobsearch-jobDescriptionText"
]

async def fetch_page(url: str) -> str:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"}
        )
        return result.html

def extract_job_description(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    
    selectors = INDEED_SELECTORS if "indeed" in url else LINKEDIN_SELECTORS
    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            for tag in node(["script", "style", "button"]):
                tag.decompose()
            return md(str(node))
    
    paragraphs = soup.find_all("p")
    big_block = max(paragraphs, key=lambda p: len(p.get_text()), default=None)
    if big_block:
        return md(str(big_block))
    
    raise ValueError("Could not locate job description container")

async def scrape_job_markdown(url: str) -> str:
    try:
        html = await fetch_page(url)
        markdown = extract_job_description(html, url)
        if len(markdown.strip()) < 200:
            raise ValueError("Extracted content too small — likely blocked")
        return markdown
    except Exception as e:
        return f"ERROR: Failed to scrape job description — {str(e)}"

@tool("job_scraper_tool")
def job_scraper_tool(url: str) -> str:
    """
    Takes a LinkedIn or Indeed job URL and returns the job description as Markdown.
    """
    return asyncio.run(scrape_job_markdown(url))
