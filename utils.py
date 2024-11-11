import os
from pydub import AudioSegment
import re

def split_script_by_speaker(script):
    """
    Splits the script into a list of tuples (speaker, text).
    Assumes that the script uses speaker labels like 'Moderator:', 'Host 1:', etc.
    """
    pattern = r'^(.*?):\s*(.*)'
    segments = []
    current_speaker = None
    current_text = ''

    lines = script.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(pattern, line)
        if match:
            # New speaker found
            if current_speaker is not None and current_text:
                segments.append((current_speaker, current_text.strip()))
            current_speaker = match.group(1).strip()
            current_text = match.group(2).strip()
        else:
            # Continuation of current speaker's text
            if current_speaker is not None:
                current_text += ' ' + line
            else:
                # Handle lines without a speaker label (e.g., narration)
                pass  # You can choose to handle or ignore this
    # Add the last segment
    if current_speaker is not None and current_text:
        segments.append((current_speaker, current_text.strip()))

    return segments

def merge_audio_files(input_files, output_file):
    """
    Merges multiple audio files into a single audio file.
    Requires pydub library.
    """
    combined = AudioSegment.empty()
    for file in input_files:
        try:
            audio = AudioSegment.from_file(file)
            combined += audio
        except Exception as e:
            print(f"Error processing file {file}: {e}")
            # You might choose to skip this file or halt execution
            continue  # Skip the problematic file

    try:
        combined.export(output_file, format="mp3")
    except Exception as e:
        print(f"Error exporting merged audio: {e}")
        # Handle the error as needed