"""Azure OpenAI content generator using Azure AI Inference SDK."""

import os
import re
import logging
from typing import Dict, Any, Optional

from generic_content_generator import ContentGenerator

logger = logging.getLogger(__name__)

# Try to import Azure AI Inference SDK (preferred for GPT-5.x models)
try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.core.credentials import AzureKeyCredential
    AZURE_INFERENCE_AVAILABLE = True
except ImportError:
    AZURE_INFERENCE_AVAILABLE = False
    logger.info("Azure AI Inference SDK not available, will use OpenAI SDK")

# Fallback to OpenAI SDK
try:
    from openai import AzureOpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False

# Reasoning models need more tokens for internal thinking
REASONING_MODEL_MULTIPLIER = 4
REASONING_MODEL_MIN_TOKENS = 1000


def remove_think_blocks(text: str) -> str:
    """Remove any <think>...</think> blocks from reasoning models."""
    pattern = r'<think>.*?</think>'
    return re.sub(pattern, '', text, flags=re.DOTALL).strip()


def is_reasoning_model(model_name: str) -> bool:
    """Check if a model is a reasoning model that needs extra tokens."""
    reasoning_patterns = ['gpt-5', 'o1', 'o3', 'o4', 'reasoning']
    model_lower = model_name.lower()
    return any(p in model_lower for p in reasoning_patterns)


class AzureContentGenerator(ContentGenerator):
    """Content generator using Azure OpenAI via Azure AI Inference SDK or OpenAI SDK."""
    
    def __init__(self, conversation_config: Optional[Dict[str, Any]] = None, api_config: Optional[Dict[str, Any]] = None):
        super().__init__(config=conversation_config)
        
        api_config = api_config or {}
        
        # Check for new Azure AI Inference config first
        self.azure_ai_endpoint = os.getenv("AZURE_AI_ENDPOINT")
        self.azure_ai_key = os.getenv("AZURE_AI_API_KEY")
        self.azure_deployment = os.getenv("AZURE_DEPLOYMENT")
        
        # Fall back to old config if new not available
        self.azure_endpoint = api_config.get('endpoint') or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_api_key = api_config.get('api_key') or os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_api_version = api_config.get('api_version') or os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
        self.azure_model = api_config.get('model_name') or os.getenv("AZURE_OPENAI_MODEL_NAME")
        
        # Determine which SDK to use
        self.use_inference_sdk = (
            AZURE_INFERENCE_AVAILABLE and 
            self.azure_ai_endpoint and 
            self.azure_ai_key and
            self.azure_deployment
        )
        
        if self.use_inference_sdk:
            logger.info(f"Using Azure AI Inference SDK with model: {self.azure_deployment}")
            self.client = ChatCompletionsClient(
                endpoint=self.azure_ai_endpoint,
                credential=AzureKeyCredential(self.azure_ai_key)
            )
            self.model_name = self.azure_deployment
            self.is_reasoning = is_reasoning_model(self.azure_deployment)
        elif OPENAI_SDK_AVAILABLE:
            logger.info(f"Using OpenAI SDK with model: {self.azure_model}")
            self.client = AzureOpenAI(
                api_key=self.azure_api_key,
                api_version=self.azure_api_version,
                azure_endpoint=self.azure_endpoint,
                azure_deployment=self.azure_model
            )
            self.model_name = self.azure_model
            self.use_inference_sdk = False
            self.is_reasoning = is_reasoning_model(self.azure_model)
        else:
            raise RuntimeError("Neither Azure AI Inference SDK nor OpenAI SDK is available")
        
        if self.is_reasoning:
            logger.info(f"Model {self.model_name} detected as reasoning model - will use higher token limits")
    
    @property
    def provider_name(self) -> str:
        return "azure"
    
    def _adjust_tokens_for_reasoning(self, max_tokens: int) -> int:
        """Adjust token count for reasoning models that need extra headroom."""
        if not self.is_reasoning:
            return max_tokens
        
        # Reasoning models use tokens for internal thinking before output
        # Multiply the requested tokens and enforce a minimum
        adjusted = max(max_tokens * REASONING_MODEL_MULTIPLIER, REASONING_MODEL_MIN_TOKENS)
        logger.debug(f"Adjusted tokens from {max_tokens} to {adjusted} for reasoning model")
        return adjusted
    
    def _call_llm(self, messages: list, max_tokens: int, temperature: float = 0.7) -> str:
        """Make Azure OpenAI API call using the appropriate SDK."""
        
        # Adjust tokens for reasoning models
        effective_tokens = self._adjust_tokens_for_reasoning(max_tokens)
        
        if self.use_inference_sdk:
            # Convert messages to Azure AI Inference format
            inference_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    inference_messages.append(SystemMessage(content=content))
                else:
                    inference_messages.append(UserMessage(content=content))
            
            response = self.client.complete(
                messages=inference_messages,
                model=self.model_name,
                model_extras={"max_completion_tokens": effective_tokens}
                # Note: temperature not supported by reasoning models like gpt-5.x
            )
            raw_content = response.choices[0].message.content or ""
            raw_content = raw_content.strip()
            # Remove thinking blocks from reasoning models
            return remove_think_blocks(raw_content)
        else:
            # Use OpenAI SDK with max_completion_tokens for newer models
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=temperature,
                max_completion_tokens=effective_tokens
            )
            content = response.choices[0].message.content or ""
            return content.strip()
