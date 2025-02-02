# custom_text_to_speech.py

import re
import os
import logging
from pydub import AudioSegment
from elevenlabs import ElevenLabs
import openai
from edge_tts import Communicate
from typing import List, Tuple
import asyncio
import httpx
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioDataStream, SpeechSynthesisOutputFormat
from azure.cognitiveservices.speech.audio import AudioOutputConfig
from time import sleep

from config import AZURE_TTS_REGION

# Maximum number of retries
MAX_RETRIES = 3

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class TextToSpeechService:
    def __init__(self, config, temp_audio_dir='./temp_audio'):
        self.config = config
        self.provider = config.get('text_to_speech', {}).get('default_tts_provider', 'elevenlabs')
        self.temp_audio_dir = temp_audio_dir

        # Ensure temp_audio_dir exists
        os.makedirs(self.temp_audio_dir, exist_ok=True)

        # Initialize providers
        if self.provider == 'elevenlabs':
            self._init_elevenlabs(config)
        elif self.provider == 'openai':
            self._init_openai(config)
        elif self.provider == 'edge':
            self._init_edge(config)
        elif self.provider == 'azure':
            self._init_azure(config)
        else:
            logger.error(f"TTS provider '{self.provider}' is not supported.")
            raise ValueError(f"TTS provider '{self.provider}' is not supported.")

    def _init_elevenlabs(self, config):
        self.elevenlabs_client = ElevenLabs(api_key=config['text_to_speech']['elevenlabs']['api_key'])
        self.elevenlabs_model = config['text_to_speech']['elevenlabs']['model']
        self.voice_question = config['text_to_speech']['elevenlabs']['default_voices']['question']
        self.voice_answer = config['text_to_speech']['elevenlabs']['default_voices']['answer']
        try:
            self.available_voices = self.elevenlabs_client.voices.get_all().voices
            self.voice_name_to_id = {v.name: v.voice_id for v in self.available_voices}
            logger.info("Initialized ElevenLabs TTS with available voices.")
        except Exception as e:
            logger.error(f"Error retrieving voices from ElevenLabs: {e}")
            self.available_voices = []
            self.voice_name_to_id = {}

    def _init_openai(self, config):
        self.openai_api_key = config['text_to_speech']['openai']['api_key']
        self.openai_api_base = config['text_to_speech']['openai']['api_base']
        self.openai_model = config['text_to_speech']['openai']['model']
        self.openai_deployment_name = config['text_to_speech']['openai']['deployment_name']
        self.voice_question = config['text_to_speech']['openai']['default_voices']['question']
        self.voice_answer = config['text_to_speech']['openai']['default_voices']['answer']
        logger.info("Initialized Azure OpenAI TTS.")

    def _init_edge(self, config):
        self.edge_voice_question = config['text_to_speech']['edge']['default_voices']['question']
        self.edge_voice_answer = config['text_to_speech']['edge']['default_voices']['answer']
        logger.info("Initialized Edge TTS.")

    def _init_azure(self, config):
        self.azure_api_key = config['text_to_speech']['azure']['api_key']
        self.azure_api_base = config['text_to_speech']['azure']['api_base']
        self.azure_region = config['text_to_speech']['azure']['region']
        self.voice_question = config['text_to_speech']['azure']['default_voices']['question']
        self.voice_answer = config['text_to_speech']['azure']['default_voices']['answer']
        logger.info("Initialized Azure TTS with the provided configuration.")

    async def convert_to_speech(self, text, output_file):
        """Converts text with speaker tags to speech."""
        segments = self.split_script_by_speaker(text)
        audio_files = []

        # Check segment details
        if not segments:
            logger.error("No segments found. Ensure script format matches expected input.")
            return

        # Generate audio for each segment
        for i, (speaker, segment_text) in enumerate(segments):
            # Log the current segment details
            logger.info(f"Generating speech with {self.provider} for speaker {speaker} with text: {segment_text[:50]}...")

            # Skip empty or whitespace-only segments
            if not segment_text.strip():
                logger.warning(f"Empty text segment for {speaker}; skipping TTS generation.")
                continue

            temp_file = os.path.join(self.temp_audio_dir, f"segment_{i}.mp3")
            if self.provider == 'elevenlabs':
                voice_name = self.voice_question if speaker == 'Person1' else self.voice_answer
                voice_id = self.voice_name_to_id.get(voice_name)
                if not voice_id:
                    logger.error(f"Voice '{voice_name}' not found in ElevenLabs. Skipping segment.")
                    continue
                await self._convert_with_elevenlabs(segment_text, temp_file, voice_id)
            elif self.provider == 'openai':
                voice_name = self.voice_question if speaker == 'Person1' else self.voice_answer
                await self._convert_with_openai(segment_text, temp_file, voice_name)
            elif self.provider == 'edge':
                voice_name = self.edge_voice_question if speaker == 'Person1' else self.edge_voice_answer
                await self._convert_with_edge(segment_text, temp_file, voice_name)
            elif self.provider == 'azure':
                voice_name = self.config['text_to_speech']['azure']['default_voices'][
                    'question'] if speaker == 'Person1' else self.config['text_to_speech']['azure']['default_voices'][
                    'answer']
                await self._convert_with_azure(segment_text, temp_file, voice_name)
            else:
                logger.error(f"TTS provider '{self.provider}' is not supported.")
                continue

            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                audio_files.append(temp_file)
            else:
                logger.error(f"Audio segment {temp_file} is empty or was not created.")

        # Merge segments into final output if we have valid audio files
        if audio_files:
            self._merge_audio_files(audio_files, output_file)
        else:
            logger.error("No valid audio segments to merge.")

    async def _convert_with_azure(self, text, output_file, voice_name):
        """Generate speech using Azure TTS and save to file."""
        try:
            logger.info(f"Generating speech with Azure TTS for text segment: '{text[:50]}...'")

            """"
            # Old code using rest api call
            # Construct the request URL
            url = f"{self.config['text_to_speech']['azure']['api_base']}"
            logger.info(f"Azure TTS API url: {url}")

            # Prepare the headers for the request
            headers = {
                "Ocp-Apim-Subscription-Key": self.config['text_to_speech']['azure']['api_key'],
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3"
            }
            """

            # Construct SSML request body with customizations
            # ssml = f"""
            # <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis'
            #       xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='en-US'>
            #    <voice name='{voice_name}' parameters='temperature=0.8'>
            #        {text}
            #    </voice>
            # </speak>"""

            # Log the SSML for debugging
            # logger.debug(f"SSML Request Body: {ssml}")

            """
            # Make the request
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, data=ssml)
                # Log the full response for debugging
                logger.debug(f"Response Status Code: {response.status_code}")
                logger.debug(f"Response Headers: {response.headers}")
                logger.debug(f"Response Content: {response.text}")
                # Check if the request was successful
                if response.status_code == 200:
                    with open(output_file, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Azure TTS segment saved to {output_file}")
                else:
                    logger.error(f"Azure TTS request failed with status {response.status_code}: {response.text}")
            """

            # Configure the speech synthesizer
            speech_config = SpeechConfig(subscription=self.azure_api_key, region=self.azure_region)
            audio_config = AudioOutputConfig(filename=output_file)

            # Set the desired voice and output format
            speech_config.speech_synthesis_voice_name = voice_name
            speech_config.set_speech_synthesis_output_format(SpeechSynthesisOutputFormat.Audio24Khz96KBitRateMonoMp3)

            # Create a synthesizer
            synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

            # Synthesize the text to speech
            result = synthesizer.speak_text_async(text).get()

            # Check the result
            if result.reason == result.Reason.SynthesizingAudioCompleted:
                logger.info(f"Azure TTS segment saved to {output_file}")
            else:
                logger.error(f"Azure TTS synthesis failed: {result.reason}")

        except Exception as e:
            logger.error(f"Error generating speech with Azure TTS: {e}")

    async def _convert_with_elevenlabs(self, text, output_file, voice_id):
        """Generate speech using ElevenLabs API and save to file."""
        try:
            logger.info(
                f"Generating speech with ElevenLabs using voice ID '{voice_id}' for text segment: '{text[:30]}...'")

            # Generate audio with stream=False to receive bytes
            # ElevenLabs' generate method is synchronous; run it in a thread
            audio_generator = await asyncio.to_thread(
                self.elevenlabs_client.generate,
                text=text,
                voice=voice_id,
                model=self.elevenlabs_model,
                stream=False
            )

            # Collect audio bytes from generator
            audio_bytes = b''.join([chunk for chunk in audio_generator])

            # Log the type and length of audio
            logger.info(f"Type of audio: {type(audio_bytes)}, Length: {len(audio_bytes) if audio_bytes else 'N/A'}")

            # Check if audio data is present
            if audio_bytes and len(audio_bytes) > 0:
                with open(output_file, 'wb') as f:
                    f.write(audio_bytes)
                logger.info(f"Segment saved to {output_file}")
            else:
                logger.error(f"No audio data received from ElevenLabs for text segment: '{text[:30]}...'")

        except Exception as e:
            logger.error(f"Error generating speech with ElevenLabs: {e}")

    async def _convert_with_openai(self, text, output_file, voice_name):
        """Generate speech using Azure OpenAI TTS API and save to file."""
        try:
            logger.info(
                f"Generating speech with Azure OpenAI using voice '{voice_name}' for text segment: '{text[:30]}...'")

            # Prepare the request URL
            url = f"{self.openai_api_base}/openai/deployments/{self.openai_deployment_name}/audio/speech?api-version=2024-02-15-preview"

            # Prepare the headers
            headers = {
                "api-key": self.openai_api_key,
                "Content-Type": "application/json"
            }

            # Prepare the payload
            payload = {
                "model": self.openai_model,
                "input": text,
                "voice": voice_name
            }

            # Set timeout and retry logic
            async with httpx.AsyncClient(timeout=15) as client:  # Increased timeout to 15 seconds
                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        response = await client.post(url, headers=headers, json=payload)
                        if response.status_code == 200:
                            # Save the binary content to the output file
                            with open(output_file, 'wb') as f:
                                f.write(response.content)
                            logger.info(f"Segment saved to {output_file}")
                            return  # Exit after successful response
                        else:
                            logger.error(f"Azure OpenAI TTS API returned status code {response.status_code}: {response.text}")
                    except httpx.RequestError as e:
                        logger.error(f"Network error on attempt {attempt}: {e}")
                    except httpx.TimeoutException:
                        logger.error(f"Request timed out on attempt {attempt}")

                    # Exponential backoff
                    sleep(2 ** attempt)

            # If all attempts fail
            logger.error(f"Failed to generate speech after {MAX_RETRIES} attempts for text segment: '{text[:30]}...'")

        except Exception as e:
            logger.error(f"Unexpected error in generating speech with Azure OpenAI: {e}")

    async def _convert_with_edge(self, text, output_file, voice_name):
        """Generate speech using Edge TTS and save to file."""
        try:
            logger.info(
                f"Generating speech with Edge TTS using voice '{voice_name}' for text segment: '{text[:30]}...'")

            communicate = Communicate(text, voice_name)
            await communicate.save(output_file)
            logger.info(f"Segment saved to {output_file}")

        except Exception as e:
            logger.error(f"Error generating speech with Edge TTS: {e}")

    def _merge_audio_files(self, audio_files: List[str], output_file: str):
        """Merge the provided list of audio files into a single MP3 output file."""
        try:
            combined = AudioSegment.empty()
            for i, audio_file in enumerate(audio_files):
                try:
                    segment = AudioSegment.from_file(audio_file, format="mp3")
                    combined += segment
                    logger.info(f"Added segment {i + 1} with duration {len(segment)} ms")
                except Exception as e:
                    logger.error(f"Failed to load segment {i + 1} ({audio_file}): {e}")

            if len(combined) > 0:
                combined.export(output_file, format="mp3", bitrate="192k")
                logger.info(f"Merged audio saved to {output_file}")
                # Clean up temporary files
                for audio_file in audio_files:
                    try:
                        os.remove(audio_file)
                        logger.info(f"Deleted temporary file: {audio_file}")
                    except Exception as e:
                        logger.warning(f"Failed to delete temporary file {audio_file}: {e}")
            else:
                logger.error("No valid audio to export. Merged file not created.")
        except Exception as e:
            logger.error(f"Error merging audio files: {e}")

    def split_script_by_speaker(self, text) -> List[Tuple[str, str]]:
        """Splits script into segments based on speaker tags."""
        pattern = re.compile(r'<(Person1|Person2)>(.*?)</\1>', re.DOTALL)
        segments = [(speaker, dialogue.strip()) for speaker, dialogue in pattern.findall(text)]
        logger.info(f"Found {len(segments)} segments in the script.")
        return segments

    def _validate_mp3(self, file_path: str) -> bool:
        """
        Check if the MP3 file is valid by attempting to load it with pydub.
        """
        try:
            audio = AudioSegment.from_file(file_path, format="mp3")
            if len(audio) > 0:
                logger.info(f"The MP3 file '{file_path}' is valid.")
                return True
            else:
                logger.error(f"The MP3 file '{file_path}' is empty.")
                return False
        except Exception as e:
            logger.error(f"Failed to validate MP3 file '{file_path}': {e}")
            return False