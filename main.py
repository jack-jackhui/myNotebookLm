import sys
import os
import re
import asyncio
import traceback
import logging
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

# Import new modules for improved podcast generation
from story_arc import create_episode_arc, format_arc_for_prompt
from topic_curator import select_top_stories, format_curated_stories_for_prompt, format_single_story_for_prompt, curated_to_dict
from episode_memory import get_memory_manager

logger = logging.getLogger(__name__)


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

        # Display the fetched articles for verification
        print("\nFetched Article Titles:")
        for i, article in enumerate(articles, 1):
            print(f"  {i}. {article['title'][:70]}...")

        # Step 1: Curate and rank stories (combines similar, selects top 3-4)
        current_step = "Curating Stories"
        print("\n--- Curating and Ranking Stories ---")
        top_stories = select_top_stories(articles, max_stories=4, min_significance=2.0)
        print(f"Selected {len(top_stories)} top stories for in-depth coverage")

        if not top_stories:
            raise ValueError("No significant stories found after curation")

        # Step 2: Get episode memory for callbacks
        current_step = "Loading Episode Memory"
        print("\n--- Loading Episode Memory ---")
        memory_manager = get_memory_manager()
        past_predictions = memory_manager.get_unresolved_predictions()
        print(f"Found {len(past_predictions)} unresolved predictions from past episodes")

        # Convert curated stories back to dict format for story_arc
        story_dicts = [curated_to_dict(s) for s in top_stories]

        # Step 3: Create episode arc with themes and callbacks
        current_step = "Creating Episode Arc"
        print("\n--- Creating Episode Arc ---")
        episode_arc = create_episode_arc(
            stories=story_dicts,
            past_predictions=past_predictions,
            max_themes=3
        )
        print(f"Main theme: {episode_arc.main_theme.name}")
        print(f"Supporting themes: {[t.name for t in episode_arc.supporting_themes]}")
        if episode_arc.callbacks:
            print(f"Callbacks from past episodes: {len(episode_arc.callbacks)}")

        # Step 4: Check for callbacks from current stories
        callbacks = memory_manager.get_callbacks_for_stories(story_dicts)
        callback_text = memory_manager.format_callbacks_for_prompt(callbacks)

        # Step 5: Build enhanced prompt with arc structure
        current_step = "Building Enhanced Prompt"
        arc_prompt = format_arc_for_prompt(episode_arc)
        curated_prompt = format_curated_stories_for_prompt(top_stories)
        host_memory = memory_manager.get_host_memory_context()

        # Combine into structured content for generation
        combined_text = f"""
{callback_text}
{host_memory}

{arc_prompt}

{curated_prompt}

GENERATION INSTRUCTIONS:
- Structure the episode around the MAIN THEME: {episode_arc.main_theme.name}
- Cover each of the {len(top_stories)} stories IN DEPTH (not surface level)
- Use the CALLBACKS to reference past predictions if any matched
- Make the PREDICTIONS listed above during the discussion
- Hosts should DISAGREE on the debate points listed
"""

        # Create topics dict from curated stories for iterative generation
        topics = {
            f"Story {i+1}: {s.title[:50]}": format_single_story_for_prompt(s)
            for i, s in enumerate(top_stories)
        }
        print(f"\n--- Topics for Generation ---")
        for topic in topics.keys():
            print(f"  - {topic}")

        # Generate the conversation script
        current_step = "Generating Conversation Script"
        print("\nGenerating conversation script...")
        script = generate_conversation_script(
            combined_text=combined_text,
            podcast_title=PODCAST_TITLE,
            podcast_description=PODCAST_DESCRIPTION,
            is_first_episode=is_first_episode(),
            topics=topics
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

        # Record episode in memory for future callbacks
        current_step = "Recording Episode Memory"
        print("Recording episode in memory...")
        memory_manager.record_episode(
            main_theme=episode_arc.main_theme.name,
            topics_covered=[s.title for s in top_stories],
            predictions_made=episode_arc.predictions,
            key_stories=[s.title for s in top_stories],
            callbacks_used=[cb.get('prediction', '')[:50] for cb in callbacks]
        )

        # Send success notification
        notify_success(
            f"Podcast episode generated and uploaded!\n\n"
            f"<b>Articles:</b> {len(articles)}\n"
            f"<b>Theme:</b> {episode_arc.main_theme.name}\n"
            f"<b>Top Stories:</b> {len(top_stories)}\n"
            f"<b>Predictions:</b> {len(episode_arc.predictions)}\n"
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
