import logging
from typing import Iterable

import httpx

from app.config import get_settings
from app.schemas.admin import AdminChatMessage
from app.services.ollama_client import ollama_endpoint, ollama_headers

logger = logging.getLogger(__name__)


class AdminChatService:
    """Direct admin chat wrapper around Ollama's chat endpoint."""

    def __init__(self):
        self.settings = get_settings()
        self.chat_url = ollama_endpoint(self.settings, "chat")

    def chat(
        self,
        messages: Iterable[AdminChatMessage],
        temperature: float = 0.3,
    ) -> dict:
        model = self.settings.OLLAMA_MODEL
        payload = {
            "model": model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in messages
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }

        response = httpx.post(
            self.chat_url,
            json=payload,
            headers=ollama_headers(self.settings),
            timeout=self.settings.OLLAMA_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        message = data.get("message") or {}
        content = str(message.get("content") or "").strip()
        if not content:
            logger.warning("Ollama chat returned no assistant content: %s", data)
            raise ValueError("Model returned an empty response")

        return {
            "model": data.get("model") or model,
            "message": {
                "role": "assistant",
                "content": content,
            },
        }
