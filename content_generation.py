"""Content generation factory and utilities."""

from typing import Dict, Type, Optional
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


def generate_conversation_script(
    combined_text: str,
    podcast_title: str,
    podcast_description: str,
    is_first_episode: bool = False,
    topics: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate a conversation script for a podcast episode.
    
    This is a convenience function that wraps the content generator.
    
    Args:
        combined_text: The combined text content to generate script from
        podcast_title: Title of the podcast
        podcast_description: Description of the podcast
        is_first_episode: Whether this is the first episode
        topics: Optional dictionary of topic names to topic content
        
    Returns:
        Generated conversation script as a string
    """
    # Create the content generator using the factory
    generator = create_content_generator()
    
    # Generate opening segment
    print("Generating opening segment...")
    opening = generator.generate_qa_content(
        input_texts=combined_text[:2000],  # Use first part for context
        is_first_episode=is_first_episode,
        is_opening=True
    )
    
    full_script = opening + "\n\n" if opening else ""
    
    # If topics provided, generate script for each topic
    if topics:
        print("Using iterative script generation for multiple topics...")
        topic_segments = list(topics.values())
        for i, segment in enumerate(topic_segments):
            print(f"Generating script for segment {i + 1}: {segment[:30]}...")
            segment_script = generator.generate_qa_content(
                input_texts=segment,
                is_first_episode=False,
                is_segment=True
            )
            if segment_script:
                full_script += segment_script + "\n\n"
    else:
        # Generate single script from combined text
        script = generator.generate_qa_content(
            input_texts=combined_text,
            is_first_episode=is_first_episode
        )
        if script:
            full_script += script + "\n\n"
    
    # Generate closing segment
    print("Generating closing segment...")
    closing = generator.generate_qa_content(
        input_texts="Wrap up the episode",
        is_first_episode=False,
        is_ending=True
    )
    
    if closing:
        full_script += closing
    
    return full_script.strip()
