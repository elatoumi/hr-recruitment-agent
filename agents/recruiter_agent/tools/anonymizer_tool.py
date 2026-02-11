import re

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

PHONE_PATTERN = re.compile(
    r"(\+?\d{1,3}[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{3,4}"
)

NAME_PATTERN = re.compile(
    r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})\b"
)


def anonymizer_tool(cv_text: str) -> dict:
    """
    Anonymize CV text by removing names, emails, and phone numbers.

    Args:
        cv_text (str): The text content of the CV.

    Returns:
        dict: {
            "anonymized_text": str
        }
    """

    if not cv_text or not cv_text.strip():
        return {"anonymized_text": ""}

    anonymized = cv_text
    anonymized = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", anonymized)
    anonymized = PHONE_PATTERN.sub("[REDACTED_PHONE]", anonymized)
    anonymized = NAME_PATTERN.sub("[REDACTED_NAME]", anonymized)

    return {"anonymized_text": anonymized}
