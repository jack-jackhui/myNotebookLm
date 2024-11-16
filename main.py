import sys
import os
import re
import asyncio
from config import (
    PODCAST_TITLE,
    PODCAST_DESCRIPTION,
    conversation_config_path,
    INTRO_MUSIC_PATH,
    OUTRO_MUSIC_PATH,
    FIRST_EPISODE_FLAG_FILE
)
from content_extraction import extract_content_from_sources
from content_generation import generate_conversation_script
from text_to_speech_conversion import convert_script_to_audio
from upload_podcast import upload_podcast_episode
from news_tracker import get_recent_articles
from datetime import datetime

def is_first_episode():
    """Check if this is the first episode."""
    return not os.path.exists(FIRST_EPISODE_FLAG_FILE)


def clean_html(raw_html):
    """Remove HTML tags from a string."""
    clean_text = re.sub(r'<.*?>', '', raw_html)
    return clean_text


def set_first_episode_done():
    """Set that the first episode has been published."""
    with open(FIRST_EPISODE_FLAG_FILE, 'w') as f:
        f.write("First episode published.")


def split_topics(combined_text):
    """Split combined text into topics based on keywords."""
    topics = {
        'crypto': r'\bcrypto|cryptocurrency|bitcoin|ethereum|blockchain|distributed ledger|solana|coin\b',
        'AI': r'\bAI|artificial intelligence|machine learning|deep learning|chatgpt|nvidia|openai\b',
        'Web3': r'\bweb3|decentralized web|dweb|defi|decentralized finance|nft\b',
        'Fintech': r'\bpayment|digital|bank|money|stripe\b',
        # Add more topics with flexible keywords as needed
    }

    # Initialize dictionary to hold the content for each topic
    topic_content = {topic: [] for topic in topics}

    # Iterate through each line in the combined text
    for line in combined_text.splitlines():
        # Check each topic and add matching lines
        for topic, pattern in topics.items():
            if re.search(pattern, line, re.IGNORECASE):
                topic_content[topic].append(line)
                break  # Avoid adding the same line to multiple topics

    # Remove empty topics and format them as a dictionary of text
    return {topic: " ".join(lines) for topic, lines in topic_content.items() if lines}


async def generate_and_upload_podcast():
    try:
        # Ensure API keys are available
        # if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, ELEVENLABS_API_KEY]):
        #    raise ValueError("One or more API keys are missing.")

        print(f"Fetching recent articles for podcast generation at {datetime.now()}...")

        # Fetch recent articles from news sources
        articles = get_recent_articles()
        print(f"Fetched {len(articles)} articles.\n")

        # Combine text by checking if 'content' exists, and clean HTML tags if needed
        article_texts = " ".join(clean_html(article.get('content', '')) for article in articles)

        # Display the fetched articles for verification
        print("\nFetched Article Titles and Content for Verification:")
        for i, article in enumerate(articles, 1):
            print(f"Article {i}: {article['title']}")
            # print(f"Content:\n{article['content']}\n")

        # Add paths to any local files you want to include
        local_files = [
            # "./source_files/Galapago_Investor_Deck_SeedRound_18092023.pdf",
            # Add more local PDFs or documents as needed
        ]

        # Extract content from both news articles and local files
        print("Extracting content...")
        combined_text = article_texts + "\n" + extract_content_from_sources(local_files)

        # Split the combined text into topics
        topics = split_topics(combined_text)
        print("\n--- Topics and Content Verification ---")
        for topic, content in topics.items():
            print(f"Topic: {topic}")
            # print(f"Content: {content}\n" if content else "No content found for this topic.\n")

        """
        # Azure OpenAI configuration dictionary
        azure_openai_config = {
            'openai_api_key': AZURE_OPENAI_API_KEY,
            'openai_api_base': AZURE_OPENAI_ENDPOINT,
            'openai_api_version': AZURE_OPENAI_API_VERSION,
            'deployment_name': AZURE_OPENAI_MODEL_NAME,
            'model_name': AZURE_OPENAI_MODEL_NAME
        }

        conversation_config_path: str = 'conversation_config.yaml'
        """

        # Generate the conversation script, passing topics for iterative generation
        print("Generating conversation script...")
        script = generate_conversation_script(
            combined_text=combined_text,
            podcast_title=PODCAST_TITLE,
            podcast_description=PODCAST_DESCRIPTION,
            is_first_episode=is_first_episode(),
            topics=topics  # Pass the topics to enable iterative generation
        )

        """
        # Generate the conversation script
        print("Generating conversation script...")
        script = generate_conversation_script(
            combined_text=combined_text,
            podcast_title=PODCAST_TITLE,
            podcast_description=PODCAST_DESCRIPTION,
            azure_openai_config=azure_openai_config,  # Pass the Azure OpenAI config
            conversation_config_path=conversation_config_path,
            is_first_episode=is_first_episode()
        )
        """

        # Save the script to a file (optional)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        script_file_path = './data/transcripts/'
        script_filename = os.path.join(script_file_path, f"{timestamp}_final_conversation_script.txt")
        with open(script_filename, 'w', encoding='utf-8') as f:
            f.write(script)

        output_directory = './data/audio/podcast'
        os.makedirs(output_directory, exist_ok=True)  # Create the directory if it doesn’t exist
        # timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_audio_file = os.path.join(output_directory, f"{timestamp}_podcast_episode.mp3")

        # Convert the script to audio
        print("Converting script to audio...")
        output_audio_file = output_audio_file
        await convert_script_to_audio(
            script_text=script,
            output_audio_file=output_audio_file,
            conversation_config_path=conversation_config_path,
            intro_music_path=INTRO_MUSIC_PATH,
            outro_music_path=OUTRO_MUSIC_PATH
        )

        print(f"Podcast generated and saved as: {output_audio_file}")

        # Set the first episode flag if this was the first episode
        if is_first_episode():
            set_first_episode_done()

        # Upload the podcast episode

        print("Uploading podcast episode...")
        upload_podcast_episode(
            audio_file_path=output_audio_file,
            transcript_text=script
        )
        print("Podcast episode created and uploaded successfully!")


    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(generate_and_upload_podcast())
