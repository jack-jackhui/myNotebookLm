"""Content generation factory and utilities."""

from typing import Dict, Type
from generic_content_generator import ContentGenerator
from azure_content_generator import AzureContentGenerator
from openai_content_generator import OpenAIContentGenerator
from ollama_content_generator import OllamaContentGenerator
from deepseek_content_generator import DeepSeekContentGenerator
from settings import load_conversation_config, load_llm_config
from errors import ConfigurationError

# Provider registry
GENERATORS: Dict[str, Type[ContentGenerator]] = {
    'azure': AzureContentGenerator,
    'openai': OpenAIContentGenerator,
    'ollama': OllamaContentGenerator,
    'deepseek': DeepSeekContentGenerator,
}


def create_content_generator(provider: str = None) -> ContentGenerator:
    """
    Create a content generator for the specified or configured provider.
    
    Args:
        provider: Optional provider override. If None, uses config.
        
    Returns:
        ContentGenerator instance
        
    Raises:
        ConfigurationError: If provider is unknown or config is invalid
    """
    config = load_llm_config()
    provider = provider or config.get('llm_provider', {}).get('provider')
    
    print(f"Selected LLM Provider: {provider}")
    
    if provider not in GENERATORS:
        available = ", ".join(GENERATORS.keys())
        raise ConfigurationError(f"Unknown LLM provider: '{provider}'. Available: {available}")
    
    generator_class = GENERATORS[provider]
    provider_config = config.get('llm_provider', {}).get(provider, {})
    conversation_config = load_conversation_config()
    
    # Validate required config
    if not provider_config:
        raise ConfigurationError(f"{provider} configuration is missing or incomplete")
    
    return generator_class(
        conversation_config=conversation_config,
        api_config=provider_config
    )


def register_generator(name: str, generator_class: Type[ContentGenerator]) -> None:
    """Register a custom content generator."""
    GENERATORS[name] = generator_class
