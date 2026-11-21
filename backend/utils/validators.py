import re
from typing import Dict, Any, Tuple

def validate_search_query(query: str, max_length: int = 300) -> Tuple[bool, str]:
    if not query or not isinstance(query, str):
        return False, "Query must be a non-empty string."
    cleaned = query.strip()
    if len(cleaned) < 2:
        return False, "Query must be at least 2 characters long."
    if len(cleaned) > max_length:
        return False, f"Query cannot exceed {max_length} characters."
    return True, cleaned

def sanitize_string(text: str) -> str:
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r'<[^>]*>', '', text)
    # Strip dangerous shell/SQL control characters safely
    clean = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', clean)
    return clean.strip()
