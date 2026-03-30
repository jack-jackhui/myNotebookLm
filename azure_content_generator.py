"""Azure OpenAI content generator."""

from openai import AzureOpenAI
from typing import Dict, Any, Optional
import logging

from generic_content_generator import ContentGenerator

logger = logging.getLogger(__name__)


class AzureContentGenerator(ContentGenerator):
    """Content generator using Azure OpenAI."""
    
    def __init__(self, conversation_config: Optional[Dict[str, Any]] = None, api_config: Optional[Dict[str, Any]] = None):
        super().__init__(config=conversation_config)
        
        api_config = api_config or {}
        self.azure_model = api_config.get('model_name')
        
        self.client = AzureOpenAI(
            api_key=api_config.get('api_key'),
            api_version=api_config.get('api_version'),
            azure_endpoint=api_config.get('endpoint'),
            azure_deployment=self.azure_model
        )
    
    @property
    def provider_name(self) -> str:
        return "azure"
    
    def _call_llm(self, messages: list, max_tokens: int, temperature: float = 0.7) -> str:
        """Make Azure OpenAI API call."""
        response = self.client.chat.completions.create(
            messages=messages,
            model=self.azure_model,
            temperature=temperature,
            max_completion_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
