# upload_podcast.py

import requests
from requests.auth import HTTPBasicAuth
from generate_episode_details import generate_episode_details
import os
from config import load_conversation_config

# Load WordPress site and credentials from environment variables or .env
WORDPRESS_SITE = os.getenv("WORDPRESS_SITE")
USERNAME = os.getenv("WORDPRESS_USERNAME")
APPLICATION_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

# Ensure env variables are available
if not all([WORDPRESS_SITE, USERNAME, APPLICATION_PASSWORD]):
    raise ValueError("One or more environment variables are missing.")

def get_audio_file_size_and_type(audio_url):
    response = requests.head(audio_url)
    file_size = response.headers.get('Content-Length')
    mime_type = response.headers.get('Content-Type', 'audio/mpeg')  # default to 'audio/mpeg' if not found
    return file_size, mime_type

# Step 1: Upload the audio file to WordPress
def upload_audio(audio_file_path):
    media_url = f"{WORDPRESS_SITE}/wp-json/wp/v2/media"
    headers = {
        "Content-Disposition": f"attachment; filename={os.path.basename(audio_file_path)}"
    }
    with open(audio_file_path, 'rb') as audio_file:
        response = requests.post(
            media_url,
            headers=headers,
            auth=HTTPBasicAuth(USERNAME, APPLICATION_PASSWORD),
            files={"file": audio_file}
        )
    if response.status_code == 201:
        media_data = response.json()
        print("Audio file uploaded:", media_data)
        return media_data['id'], media_data['source_url']
    else:
        print("Failed to upload audio:", response.text)
        return None, None


# Step 2: Create a new podcast episode post
def create_episode_post(audio_id, audio_url, title, description):
    # API endpoint for podcast episodes
    post_url = f"{WORDPRESS_SITE}/wp-json/wp/v2/podcast"
    file_size, mime_type = get_audio_file_size_and_type(audio_url)

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
    response = requests.post(
        post_url,
        json=post_data,
        auth=HTTPBasicAuth(USERNAME, APPLICATION_PASSWORD)
    )
    if response.status_code == 201:
        print("Episode post created:", response.json())
    else:
        print("Failed to create episode post:", response.text)


# Combine upload and post creation into one function for easy calling
def upload_podcast_episode(audio_file_path, transcript_text):
    # Generate episode details
    title, description = generate_episode_details(transcript_text)

    # Upload audio file to WordPress
    audio_id, audio_url = upload_audio(audio_file_path)
    if audio_id and audio_url:
        # Create a new post with the generated title and description
        create_episode_post(audio_id, audio_url, title, description)