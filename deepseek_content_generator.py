"""DeepSeek content generator."""

import re
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from typing import Dict, Any, Optional
import logging

from generic_content_generator import ContentGenerator

logger = logging.getLogger(__name__)


class DeepSeekContentGenerator(ContentGenerator):
    """Content generator using DeepSeek via Azure AI."""
    
    def __init__(self, conversation_config: Optional[Dict[str, Any]] = None, api_config: Optional[Dict[str, Any]] = None):
        super().__init__(config=conversation_config)
        
        api_config = api_config or {}
        self.endpoint = api_config.get('endpoint')
        self.model_name = api_config.get('model_name')
        
        self.client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(api_config.get('api_key'))
        )
    
    @property
    def provider_name(self) -> str:
        return "deepseek"
    
    @staticmethod
    def clean_script(text: str) -> str:
        """Remove thinking tags and stage directions from DeepSeek output."""
        # Remove <think>...</think> blocks
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # Remove stray tags
        text = re.sub(r"</?think>", "", text, flags=re.IGNORECASE)
        # Remove stage directions **[...]**
        text = re.sub(r"\*\*\[.*?\]\*\*", "", text, flags=re.DOTALL)
        # Clean up empty lines
        text = re.sub(r"\n\s*\n", "\n", text)
        return text.strip()
    
    def _call_llm(self, messages: list, max_tokens: int, temperature: float = 0.7) -> str:
        """Make DeepSeek API call."""
        # Convert to DeepSeek message format
        deepseek_messages = []
        for msg in messages:
            if msg["role"] == "system":
                deepseek_messages.append(SystemMessage(content=msg["content"]))
            else:
                deepseek_messages.append(UserMessage(content=msg["content"]))
        
        response = self.client.complete(
            messages=deepseek_messages,
            model=self.model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        content = response.choices[0].message.content
        if content:
            content = self.clean_script(content)
        return content.strip() if content else ""
