"""Ollama content generator."""

import requests
from typing import Dict, Any, Optional
import logging

from generic_content_generator import ContentGenerator

logger = logging.getLogger(__name__)


class OllamaContentGenerator(ContentGenerator):
    """Content generator using Ollama."""
    
    def __init__(self, conversation_config: Optional[Dict[str, Any]] = None, api_config: Optional[Dict[str, Any]] = None):
        super().__init__(config=conversation_config)
        
        api_config = api_config or {}
        self.host = api_config.get('host', 'localhost')
        self.port = api_config.get('port', 11434)
        self.model_name = api_config.get('model_name')
    
    @property
    def provider_name(self) -> str:
        return "ollama"
    
    def _call_llm(self, messages: list, max_tokens: int, temperature: float = 0.7) -> str:
        """Make Ollama API call."""
        # Convert messages to single prompt for Ollama
        prompt = "\n".join(
            f"{m[role]}: {m[content]}" for m in messages
        )
        
        url = f"http://{self.host}:{self.port}/api/generate"
        response = requests.post(url, json={
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        })
        
        if response.status_code == 200:
            return response.json().get("text", "").strip()
        else:
            raise RuntimeError(f"Ollama API error: {response.text}")
