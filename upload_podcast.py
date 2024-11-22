# upload_podcast.py
import logging
import requests
from requests.auth import HTTPBasicAuth
from generate_episode_details import generate_episode_details
import os
from config import load_conversation_config
from config import WORDPRESS_SITE, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD

# Ensure env variables are available
if not all([WORDPRESS_SITE, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD]):
    raise ValueError("One or more environment variables are missing.")

logger = logging.getLogger(__name__)

def get_audio_file_size_and_type(audio_url):
    """Retrieve the file size and MIME type of an audio file from its URL."""
    try:
        response = requests.head(audio_url)
        if response.status_code == 200:
            file_size = response.headers.get('Content-Length')
            mime_type = response.headers.get('Content-Type', 'audio/mpeg')  # Default to 'audio/mpeg'
            return file_size, mime_type
        else:
            print(f"Failed to retrieve audio metadata. Status code: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Error in get_audio_file_size_and_type: {e}")
        return None, None

# Step 1: Upload the audio file to WordPress
def upload_audio(audio_file_path):
    """Upload an audio file to WordPress and return the media ID and URL."""
    media_url = f"{WORDPRESS_SITE}/wp-json/wp/v2/media"
    headers = {
        "Content-Disposition": f"attachment; filename={os.path.basename(audio_file_path)}"
    }

    if not os.path.exists(audio_file_path):
        logger.error(f"Audio file does not exist: {audio_file_path}")
        return None, None

    try:
        with open(audio_file_path, 'rb') as audio_file:
            response = requests.post(
                media_url,
                headers=headers,
                auth=HTTPBasicAuth(WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD),
                files={"file": audio_file}
            )

        # Debugging information
        logger.debug(f"Upload audio response status code: {response.status_code}")
        if response.status_code != 201:
            logger.error(f"Upload failed. Response content: {response.text}")
            return None, None

        try:
            media_data = response.json()
            logger.info("Audio file uploaded successfully: %s", media_data)
            audio_id = media_data.get('id')
            audio_url = media_data.get('source_url')
            if not audio_id or not audio_url:
                logger.error(f"Unexpected response structure: {media_data}")
                return None, None
            return audio_id, audio_url
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response.text}")
            return None, None
    except Exception as e:
        logger.exception(f"Error in upload_audio: {e}")
        return None, None

# Step 2: Create a new podcast episode post
def create_episode_post(audio_id, audio_url, title, description):
    # API endpoint for podcast episodes
    post_url = f"{WORDPRESS_SITE}/wp-json/wp/v2/podcast"
    file_size, mime_type = get_audio_file_size_and_type(audio_url)

    if not file_size or not mime_type:
        logger.error("Failed to retrieve audio file metadata. Aborting post creation.")
        return

    # Embed audio in post content
    post_content = (
        f"{description}\n"
        # f"<h3>Listen to the Episode</h3>"
        # f"<audio controls>"
        # f"  <source src='{audio_url}' type='audio/mpeg'>"
        # f"  Your browser does not support the audio element."
        # f"</audio>"
    )
    post_data = {
        "title": title,
        "content": post_content,
        #"categories": "Podcast",
        "status": "publish",  # Change to "draft" if you want to review first
        "meta": {
            "_ssp_media_url": audio_url,  # Seriously Simple Podcasting media URL meta key
            "_ssp_file_size": file_size,  # Optional: Add file size in bytes
            "_ssp_mime_type": mime_type,
            "episode_type": "audio",
            "audio_file": audio_url,      # Adds the audio file to the episode
        }
    }
    try:
        response = requests.post(
            post_url,
            json=post_data,
            auth=HTTPBasicAuth(WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD)
        )
        print(f"Create episode post response status code: {response.status_code}")
        if response.status_code != 201:
            logger.error(f"Failed to create episode post. Response content: {response.text}")
            return
        try:
            post_data = response.json()
            logger.info("Episode post created successfully:", post_data)
        except ValueError as e:
            logger.exception(f"Failed to parse JSON response for episode post: {e}")
            logger.debug(f"Response text: {response.text}")
    except Exception as e:
        logger.exception(f"Error in create_episode_post: {e}")


# Combine upload and post creation into one function for easy calling
def upload_podcast_episode(audio_file_path, transcript_text):
    try:
        # Generate episode details
        title, description = generate_episode_details(transcript_text)

        # Upload audio file to WordPress
        audio_id, audio_url = upload_audio(audio_file_path)
        if audio_id and audio_url:
            # Create a new post with the generated title and description
            create_episode_post(audio_id, audio_url, title, description)
        else:
            logger.error("Audio upload failed. Episode creation aborted.")
    except Exception as e:
        logger.exception(f"Error in upload_podcast_episode: {e}")
        raise