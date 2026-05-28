import json
from typing import Any
from urllib.parse import urlparse

from app.config import Settings


def ollama_endpoint(settings: Settings, endpoint: str) -> str:
    """Build an Ollama API endpoint from either a host URL or /api URL."""
    base_url = settings.OLLAMA_URL.rstrip("/")
    if not base_url.endswith("/api"):
        base_url = f"{base_url}/api"
    return f"{base_url}/{endpoint.lstrip('/')}"


def ollama_headers(settings: Settings) -> dict[str, str]:
    """Return optional auth headers for direct Ollama Cloud API access."""
    if settings.OLLAMA_API_KEY:
        return {"Authorization": f"Bearer {settings.OLLAMA_API_KEY}"}
    return {}


def ollama_supports_structured_outputs(settings: Settings) -> bool:
    """Ollama Cloud does not currently support structured outputs."""
    if settings.OLLAMA_ENABLE_STRUCTURED_OUTPUTS is not None:
        return settings.OLLAMA_ENABLE_STRUCTURED_OUTPUTS

    host = urlparse(settings.OLLAMA_URL).netloc.lower()
    return host not in {"ollama.com", "www.ollama.com"}


def parse_ollama_json_response(raw_text: str) -> dict[str, Any]:
    """Parse JSON even when a cloud model wraps it in markdown or text."""
    text = (raw_text or "").strip()
    if not text:
        raise json.JSONDecodeError("Empty model response", raw_text, 0)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(text[start:end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("Expected Ollama JSON response to be an object")
    return parsed
