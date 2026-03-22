"""OpenAI content generator."""

from openai import OpenAI
from typing import Dict, Any, Optional
import logging

from generic_content_generator import ContentGenerator

logger = logging.getLogger(__name__)


class OpenAIContentGenerator(ContentGenerator):
    """Content generator using OpenAI."""
    
    def __init__(self, conversation_config: Optional[Dict[str, Any]] = None, api_config: Optional[Dict[str, Any]] = None):
        super().__init__(config=conversation_config)
        
        api_config = api_config or {}
        self.model_name = api_config.get('model_name')
        self.client = OpenAI(api_key=api_config.get('api_key'))
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    def _call_llm(self, messages: list, max_tokens: int, temperature: float = 0.7) -> str:
        """Make OpenAI API call."""
        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
