# content_generation.py

from azure_content_generator import AzureContentGenerator
from config import load_conversation_config

def generate_conversation_script(
    combined_text: str,
    podcast_title: str,
    podcast_description: str,
    azure_openai_config: dict,
    conversation_config_path: str = 'conversation_config.yaml',
    is_first_episode: bool = False,
    topics: dict = None
) -> str:
    if not azure_openai_config:
        raise ValueError("Azure OpenAI configuration is missing.")

    # Load the conversation configuration from the YAML file
    conversation_config = load_conversation_config(conversation_config_path)

    # Initialize AzureContentGenerator with the configurations
    content_generator = AzureContentGenerator(
        conversation_config=conversation_config
    )

    # Generate opening section
    print("Generating opening segment...")
    opening_script = content_generator.generate_qa_content(
        input_texts="Welcome to AI Unchained, where we explore AI, Web 3.0, and the latest in tech. "
                    "Today we’ll discuss various topics, so stay tuned!",
        is_first_episode=is_first_episode,
        is_segment=False,
        is_opening=True
    )

    # Generate the main content based on topics
    if topics:
        # If topics are provided, iterate over them
        print("Using iterative script generation for multiple topics...")
        main_content_script = content_generator.iterative_script_generation(
            input_segments=[text for topic, text in topics.items()],
            is_first_episode=False
        )
    else:
        # Generate a single continuous script without segmenting by topics
        print("Generating single continuous script...")
        main_content_script = content_generator.generate_qa_content(
            input_texts=combined_text,
            is_first_episode=is_first_episode,
            is_segment=True
        )

    # Generate closing section
    print("Generating closing segment...")
    closing_script = content_generator.generate_qa_content(
        input_texts="Thank you for joining us today on AI Unchained. We hope you enjoyed our discussions and gained insights. "
                    "See you next time!",
        is_first_episode=False,
        is_segment=False,
        is_ending=True
    )

    # Combine all parts into one cohesive script
    full_script = f"{opening_script}\n\n{main_content_script}\n\n{closing_script}"
    return full_script.strip()