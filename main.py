import sys
import os
import re
import asyncio
import traceback
from settings import (
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
from notifications import notify_error, notify_success
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
    current_step = "Initialization"
    try:
        print(f"Fetching recent articles for podcast generation at {datetime.now()}...")
        current_step = "Fetching Articles"

        # Fetch recent articles from news sources
        articles = get_recent_articles()
        print(f"Fetched {len(articles)} articles.\n")

        if not articles:
            raise ValueError("No articles fetched from news sources")

        # Combine text by checking if 'content' exists, and clean HTML tags if needed
        article_texts = " ".join(clean_html(article.get('content', '')) for article in articles)

        # Display the fetched articles for verification
        print("\nFetched Article Titles and Content for Verification:")
        for i, article in enumerate(articles, 1):
            print(f"Article {i}: {article['title']}")

        # Add paths to any local files you want to include
        local_files = []

        # Extract content from both news articles and local files
        current_step = "Extracting Content"
        print("Extracting content...")
        combined_text = article_texts + "\n" + extract_content_from_sources(local_files)

        # Split the combined text into topics
        topics = split_topics(combined_text)
        print("\n--- Topics and Content Verification ---")
        for topic, content in topics.items():
            print(f"Topic: {topic}")

        # Generate the conversation script, passing topics for iterative generation
        current_step = "Generating Conversation Script"
        print("Generating conversation script...")
        script = generate_conversation_script(
            combined_text=combined_text,
            podcast_title=PODCAST_TITLE,
            podcast_description=PODCAST_DESCRIPTION,
            is_first_episode=is_first_episode(),
            topics=topics  # Pass the topics to enable iterative generation
        )

        if not script or len(script.strip()) < 100:
            raise ValueError(f"Generated script is too short or empty: {len(script)} chars")

        # Save the script to a file
        current_step = "Saving Script"
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        script_file_path = './data/transcripts/'
        os.makedirs(script_file_path, exist_ok=True)
        script_filename = os.path.join(script_file_path, f"{timestamp}_final_conversation_script.txt")
        with open(script_filename, 'w', encoding='utf-8') as f:
            f.write(script)

        output_directory = './data/audio/podcast'
        os.makedirs(output_directory, exist_ok=True)
        output_audio_file = os.path.join(output_directory, f"{timestamp}_podcast_episode.mp3")

        # Convert the script to audio
        current_step = "Converting Script to Audio (TTS)"
        print("Converting script to audio...")
        await convert_script_to_audio(
            script_text=script,
            output_audio_file=output_audio_file,
            intro_music_path=INTRO_MUSIC_PATH,
            outro_music_path=OUTRO_MUSIC_PATH
        )

        # Verify audio file was created
        if not os.path.exists(output_audio_file) or os.path.getsize(output_audio_file) < 1000:
            raise ValueError(f"Audio file not created or too small: {output_audio_file}")

        print(f"Podcast generated and saved as: {output_audio_file}")

        # Set the first episode flag if this was the first episode
        if is_first_episode():
            set_first_episode_done()

        # Upload the podcast episode
        current_step = "Uploading Podcast Episode"
        print("Uploading podcast episode...")
        upload_podcast_episode(
            audio_file_path=output_audio_file,
            transcript_text=script
        )
        print("Podcast episode created and uploaded successfully!")

        # Send success notification
        notify_success(
            f"Podcast episode generated and uploaded!\n\n"
            f"<b>Articles:</b> {len(articles)}\n"
            f"<b>Topics:</b> {', '.join(topics.keys())}\n"
            f"<b>Audio:</b> {os.path.basename(output_audio_file)}",
            context="Podcast Generation"
        )

    except Exception as e:
        error_msg = f"Failed at step: {current_step}\n\nError: {str(e)}"
        print(f"An error occurred: {e}")
        print(f"Stack trace:\n{traceback.format_exc()}")
        
        # Send error notification
        notify_error(
            error_message=error_msg,
            exception=e,
            context=f"Podcast Generation - {current_step}"
        )
        
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(generate_and_upload_podcast())
