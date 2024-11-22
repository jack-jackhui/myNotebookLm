import os
import logging
from custom_text_to_speech import TextToSpeechService
from config import load_conversation_config
from pydub import AudioSegment
import re
import asyncio
from datetime import datetime


# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def add_speaker_tags(script_text):
    """
    Convert speaker labels like '**Host Jack**: ' into <Person1> ... </Person1> and <Person2> ... </Person2>.
    """
    # Define mapping from speaker to person tag
    speaker_mapping = {
        'Jack': 'Person1',
        'Corr': 'Person2'
    }

    # Function to replace speaker labels with tags
    def replace_speaker(match):
        # Check which group matched and use the appropriate speaker and dialogue groups
        if match.group(1):  # If '**Jack**:' or '**Corr**:' matched
            speaker = match.group(1).strip()
            dialogue = match.group(2).strip()
        elif match.group(3):  # If 'Jack:' or 'Corr:' matched
            speaker = match.group(3).strip()
            dialogue = match.group(4).strip()
        else:
            return match.group(0)  # Return the original text if no match

        # Get the person tag from the mapping
        person_tag = speaker_mapping.get(speaker, 'Person1')  # Default to Person1 if not found
        return f'<{person_tag}>{dialogue}</{person_tag}>'

    # Updated regex pattern to match both '**Speaker Name**: ' and 'Speaker Name: '
    pattern = r'\*\*(Jack|Corr)\*\*:\s*(.*?)\n|^(Jack|Corr):\s*(.*?)$'

    # Replace all matches with tagged dialogues
    tagged_text = re.sub(
        pattern,
        replace_speaker,
        script_text,
        flags=re.MULTILINE
    )
    return tagged_text


def validate_format_conversion(original_script, tagged_script_text):
    """
    Validate that the conversion from 'Jack:' to <Person1> and 'Corr:' to <Person2> is correct.
    """
    # Patterns to match the original speaker format
    original_person1_pattern = re.compile(r'^Jack:\s*(.*)', re.MULTILINE)
    original_person2_pattern = re.compile(r'^Corr:\s*(.*)', re.MULTILINE)

    # Patterns to match the converted speaker tags
    tagged_person1_pattern = re.compile(r'<Person1>(.*?)</Person1>', re.DOTALL)
    tagged_person2_pattern = re.compile(r'<Person2>(.*?)</Person2>', re.DOTALL)

    # Extract original dialogues
    original_person1_dialogues = original_person1_pattern.findall(original_script)
    original_person2_dialogues = original_person2_pattern.findall(original_script)

    # Extract tagged dialogues
    tagged_person1_dialogues = tagged_person1_pattern.findall(tagged_script_text)
    tagged_person2_dialogues = tagged_person2_pattern.findall(tagged_script_text)

    # Check if the number of dialogues match for each speaker
    if len(original_person1_dialogues) != len(tagged_person1_dialogues) or len(original_person2_dialogues) != len(
            tagged_person2_dialogues):
        logger.error("Validation failed: Mismatch in the number of dialogues after conversion.")
        return False

    # Check that each dialogue in the original matches the corresponding dialogue in the tagged format
    for orig_dialogue, tagged_dialogue in zip(original_person1_dialogues, tagged_person1_dialogues):
        if orig_dialogue.strip() != tagged_dialogue.strip():
            logger.error(
                f"Validation failed: Mismatch found for Jack's dialogue.\nOriginal: {orig_dialogue}\nTagged: {tagged_dialogue}")
            return False

    for orig_dialogue, tagged_dialogue in zip(original_person2_dialogues, tagged_person2_dialogues):
        if orig_dialogue.strip() != tagged_dialogue.strip():
            logger.error(
                f"Validation failed: Mismatch found for Corr's dialogue.\nOriginal: {orig_dialogue}\nTagged: {tagged_dialogue}")
            return False

    logger.info("Format conversion validation passed.")
    return True

def validate_mp3(file_path):
    try:
        # Attempt to load the MP3 using pydub
        audio = AudioSegment.from_file(file_path, format='mp3')
        return True
    except Exception as e:
        logger.warning(f"Invalid MP3 file '{file_path}': {e}")
        return False


async def convert_script_to_audio(script_text, output_audio_file, intro_music_path=None, outro_music_path=None):
    conversation_config = load_conversation_config()
    tts_provider = conversation_config.get('text_to_speech', {}).get('default_tts_provider', 'elevenlabs')

    logger.info(f"Using TTS provider: {tts_provider}")

    # Initialize our custom TextToSpeechService
    tts_service = TextToSpeechService(config=conversation_config, temp_audio_dir=conversation_config.get('text_to_speech', {}).get('temp_audio_dir', './temp_audio'))

    # Add speaker tags
    tagged_script_text = add_speaker_tags(script_text)

    # Validate the format conversion before proceeding
    if not validate_format_conversion(script_text, tagged_script_text):
        logger.error("Format conversion validation failed. Aborting audio generation.")
        return

    # Generate audio for the script
    temp_audio_file = 'temp_podcast_audio.mp3'
    try:
        await tts_service.convert_to_speech(tagged_script_text, temp_audio_file)
        logger.info(f"Script converted to audio and saved to: {temp_audio_file}")
    except Exception as e:
        logger.error(f"Failed to convert script to audio: {e}")
        return

    # Load intro, script, and outro audio segments
    combined_audio = AudioSegment.empty()
    if intro_music_path and validate_mp3(intro_music_path):
        intro_audio = AudioSegment.from_file(intro_music_path, format='mp3')
        combined_audio += intro_audio
        logger.info("Added intro music to the beginning of the podcast.")

    if validate_mp3(temp_audio_file):
        podcast_audio = AudioSegment.from_file(temp_audio_file, format='mp3')
        combined_audio += podcast_audio
    else:
        logger.error(f"Script audio file '{temp_audio_file}' is invalid.")
        return

    if outro_music_path and validate_mp3(outro_music_path):
        outro_audio = AudioSegment.from_file(outro_music_path, format='mp3')
        combined_audio += outro_audio
        logger.info("Added outro music to the end of the podcast.")

    # Define output directory and filename with date and time if not provided
    if output_audio_file is None:
        output_directory = 'data/audio'
        os.makedirs(output_directory, exist_ok=True)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_audio_file = os.path.join(output_directory, f"{timestamp}_podcast_episode.mp3")

    # Export final combined audio
    combined_audio.export(output_audio_file, format="mp3")
    logger.info(f"Final podcast audio saved to: {output_audio_file}")


    # Clean up temporary script audio file
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)
        logger.info(f"Deleted temporary file: {temp_audio_file}")