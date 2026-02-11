from typing import List, Dict
from pathlib import Path
from langchain_core.tools import tool
import re
import unicodedata


@tool
def cv_parser_tool(file_path: str) -> dict:
    try:
        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "content": "",
                "metadata": {},
                "error": "File not found"
            }

        text = path.read_text(encoding="utf-8", errors="ignore")

        return {
            "success": True,
            "content": text,
            "metadata": {
                "name": path.name,
                "format": path.suffix.lower(),
                "size": path.stat().st_size
            },
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "content": "",
            "metadata": {},
            "error": str(e)
        }


@tool
def text_cleaner_pipeline(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub("", text)

    text = re.sub(r"\s+", " ", text).strip()
    return text


@tool
def anonymizer_tool(text: str) -> dict:
    if not text:
        return {
            "anonymized_text": "",
            "removed_entities": [],
            "entity_count": 0
        }

    removed = []

    # Patterns combined from PRs
    email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    phone_pattern = re.compile(r"(\+?\d{1,3}[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{3,4}")
    name_pattern = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})\b")

    if email_pattern.search(text):
        removed.append("email")
        text = email_pattern.sub("[REDACTED_EMAIL]", text)

    if phone_pattern.search(text):
        removed.append("phone")
        text = phone_pattern.sub("[REDACTED_PHONE]", text)

    if name_pattern.search(text):
        removed.append("name")
        text = name_pattern.sub("[REDACTED_NAME]", text)

    return {
        "anonymized_text": text,
        "removed_entities": removed,
        "entity_count": len(removed)
    }


@tool
def batch_upload_handler(files: List[str]) -> List[Dict]:
    results = []

    for file_path in files:
        parsed = cv_parser_tool(file_path)
        if parsed["success"]:
            parsed["content"] = text_cleaner_pipeline(parsed["content"])
        results.append(parsed)

    return results
