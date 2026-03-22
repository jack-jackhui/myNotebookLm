import re
import os
import logging
import asyncio
import httpx
from typing import List, Tuple, Dict, Any, Optional
from pydub import AudioSegment
from elevenlabs import ElevenLabs
import openai
from edge_tts import Communicate
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, SpeechSynthesisOutputFormat
from azure.cognitiveservices.speech.audio import AudioOutputConfig
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from errors import TTSProviderError, ConfigurationError

logger = logging.getLogger(__name__)

# Constants for speakers
PERSON1 = "Person1"
PERSON2 = "Person2"

# Retry decorator for TTS API calls
def tts_retry():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException, ConnectionError, Exception)),
        before_sleep=lambda retry_state: logger.warning(f"TTS retry attempt {retry_state.attempt_number} after error")
    )

class TTSResult:
    """Result of TTS generation containing success/failure details."""
    def __init__(self):
        self.successful_segments: List[int] = []
        self.failed_segments: List[Tuple[int, str, str]] = []  # (index, speaker, error_message)
        self.total_segments: int = 0

    @property
    def success_count(self) -> int:
        return len(self.successful_segments)

    @property
    def failure_count(self) -> int:
        return len(self.failed_segments)

    @property
    def all_succeeded(self) -> bool:
        return self.failure_count == 0

    def get_failure_summary(self) -> str:
        if not self.failed_segments:
            return ""
        lines = [f"Failed {self.failure_count} of {self.total_segments} segments:"]
        for idx, speaker, error in self.failed_segments:
            lines.append(f"  - Segment {idx + 1} ({speaker}): {error}")
        return "\n".join(lines)

class CustomTextToSpeech:
    def __init__(self, config, temp_audio_dir="./temp_audio"):
        self.config = config
        self.provider = config.get("text_to_speech", {}).get("default_tts_provider", "elevenlabs")
        self.temp_audio_dir = temp_audio_dir
        os.makedirs(self.temp_audio_dir, exist_ok=True)

        # Provider dispatch dictionary
        self._converters = {
            "elevenlabs": self._convert_with_elevenlabs,
            "openai": self._convert_with_openai,
            "azure": self._convert_with_azure,
            "edge": self._convert_with_edge,
            "sparktts": self._convert_with_sparktts,
        }
        
        # Provider initialization dispatch
        init_methods = {
            "elevenlabs": self._init_elevenlabs,
            "openai": self._init_openai,
            "edge": self._init_edge,
            "azure": self._init_azure,
            "sparktts": self._init_sparktts,
        }
        
        if self.provider not in init_methods:
            raise ConfigurationError(f"TTS provider {self.provider} is not supported. Available: {list(init_methods.keys())}")
        
        init_methods[self.provider](config)

    def _init_elevenlabs(self, config):
        tts_config = config.get("text_to_speech", {}).get("elevenlabs", {})
        self.api_key = tts_config.get("api_key")
        self.model = tts_config.get("model", "eleven_multilingual_v2")
        self.voice_question = tts_config.get("default_voices", {}).get("question")
        self.voice_answer = tts_config.get("default_voices", {}).get("answer")
        self.elevenlabs_client = ElevenLabs(api_key=self.api_key)
        try:
            voices = self.elevenlabs_client.voices.get_all().voices
            self.voice_name_to_id = {v.name: v.voice_id for v in voices}
        except Exception as e:
            logger.error(f"Error retrieving voices from ElevenLabs: {e}")
            self.voice_name_to_id = {}

    def _init_openai(self, config):
        tts_config = config.get("text_to_speech", {}).get("openai", {})
        self.api_key = tts_config.get("api_key")
        self.api_base = tts_config.get("api_base")
        self.model = tts_config.get("model", "tts-1")
        self.deployment_name = tts_config.get("deployment_name")
        self.voice_question = tts_config.get("default_voices", {}).get("question")
        self.voice_answer = tts_config.get("default_voices", {}).get("answer")

    def _init_edge(self, config):
        tts_config = config.get("text_to_speech", {}).get("edge", {})
        self.voice_question = tts_config.get("default_voices", {}).get("question")
        self.voice_answer = tts_config.get("default_voices", {}).get("answer")

    def _init_azure(self, config):
        tts_config = config.get("text_to_speech", {}).get("azure", {})
        self.api_key = tts_config.get("api_key")
        self.region = tts_config.get("region")
        self.voice_question = tts_config.get("default_voices", {}).get("question")
        self.voice_answer = tts_config.get("default_voices", {}).get("answer")

    def _init_sparktts(self, config):
        tts_config = config.get("text_to_speech", {}).get("sparktts", {})
        self.api_url = tts_config.get("api_url")
        self.auth_token = tts_config.get("api_token")
        self.default_prompts = tts_config.get("default_prompts", {"question": "default", "answer": "default"})

    async def convert_to_speech(self, text: str, output_file: str, parallel: bool = True, max_concurrent: int = 3) -> TTSResult:
        """Converts text with speaker tags to speech."""
        result = TTSResult()
        segments = self.split_script_by_speaker(text)

        if not segments:
            logger.error("No segments found. Ensure script format matches expected input.")
            return result

        logger.info(f"Processing {len(segments)} segments with {'parallel' if parallel else 'sequential'} generation")
        segment_tasks = [(i, speaker, segment_text) for i, (speaker, segment_text) in enumerate(segments) if segment_text.strip()]
        result.total_segments = len(segment_tasks)

        if parallel and len(segment_tasks) > 1:
            audio_files, failures = await self._generate_segments_parallel(segment_tasks, max_concurrent)
        else:
            audio_files, failures = await self._generate_segments_sequential(segment_tasks)

        result.successful_segments = [idx for idx, _ in audio_files]
        result.failed_segments = failures

        if audio_files:
            audio_files.sort(key=lambda x: x[0])
            ordered_files = [f[1] for f in audio_files]
            self._merge_audio_files(ordered_files, output_file)
        else:
            logger.error("No valid audio segments to merge.")

        return result

    async def _generate_segments_parallel(self, segment_tasks, max_concurrent=3):
        semaphore = asyncio.Semaphore(max_concurrent)
        async def process_with_semaphore(task):
            async with semaphore:
                return await self._generate_single_segment(*task)
        tasks = [process_with_semaphore(task) for task in segment_tasks]
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        
        results, failures = [], []
        for i, res in enumerate(completed):
            idx, speaker, _ = segment_tasks[i]
            if isinstance(res, Exception):
                failures.append((idx, speaker, str(res)))  # Graceful degradation
            elif res:
                results.append(res)
            else:
                failures.append((idx, speaker, "No audio generated"))
        return results, failures

    async def _generate_segments_sequential(self, segment_tasks):
        results, failures = [], []
        for task in segment_tasks:
            idx, speaker, _ = task
            try:
                res = await self._generate_single_segment(*task)
                if res: results.append(res)
                else: failures.append((idx, speaker, "No audio generated"))
            except Exception as e:
                failures.append((idx, speaker, str(e)))  # Graceful degradation
        return results, failures

    async def _generate_single_segment(self, index, speaker, segment_text):
        ext = "wav" if self.provider == "sparktts" else "mp3"
        temp_file = os.path.join(self.temp_audio_dir, f"segment_{index}.{ext}")
        
        converter = self._converters.get(self.provider)
        if not converter:
            raise ConfigurationError(f"Unknown TTS provider: {self.provider}")
        
        voice = self._get_voice_for_speaker(speaker)
        await converter(segment_text, temp_file, voice)
        
        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
            return (index, temp_file)
        return None

    def _get_voice_for_speaker(self, speaker: str) -> str:
        if self.provider == "elevenlabs":
            voice_name = self.voice_question if speaker == PERSON1 else self.voice_answer
            return self.voice_name_to_id.get(voice_name, voice_name)
        elif self.provider == "sparktts":
            return self.default_prompts.get("question") if speaker == PERSON1 else self.default_prompts.get("answer")
        elif self.provider == "openai":
            return self.voice_question if speaker == PERSON1 else self.voice_answer
        elif self.provider == "edge":
            return self.voice_question if speaker == PERSON1 else self.voice_answer
        elif self.provider == "azure":
            return self.voice_question if speaker == PERSON1 else self.voice_answer
        return "default"

    @tts_retry()
    async def _convert_with_elevenlabs(self, text, file_path, voice):
        audio_generator = await asyncio.to_thread(
            self.elevenlabs_client.generate,
            text=text,
            voice=voice,
            model=self.model,
            stream=False
        )
        audio_bytes = b''.join([chunk for chunk in audio_generator])
        if audio_bytes:
            with open(file_path, 'wb') as f:
                f.write(audio_bytes)

    @tts_retry()
    async def _convert_with_openai(self, text, file_path, voice):
        url = f"{self.api_base}/openai/deployments/{self.deployment_name}/audio/speech?api-version=2024-02-15-preview"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        payload = {"model": self.model, "input": text, "voice": voice}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                f.write(response.content)

    @tts_retry()
    async def _convert_with_azure(self, text, file_path, voice):
        speech_config = SpeechConfig(subscription=self.api_key, region=self.region)
        audio_config = AudioOutputConfig(filename=file_path)
        speech_config.speech_synthesis_voice_name = voice
        speech_config.set_speech_synthesis_output_format(SpeechSynthesisOutputFormat.Audio24Khz96KBitRateMonoMp3)
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        result = await asyncio.to_thread(synthesizer.speak_text_async(text).get)
        if result.reason != result.reason.SynthesizingAudioCompleted:
            raise TTSProviderError("azure", f"Azure TTS synthesis failed: {result.reason}")

    @tts_retry()
    async def _convert_with_edge(self, text, file_path, voice):
        communicate = Communicate(text, voice)
        await communicate.save(file_path)

    @tts_retry()
    async def _convert_with_sparktts(self, text, file_path, voice):
        headers = {"Authorization": f"Bearer {self.auth_token}", "Content-Type": "application/json"}
        payload = {"text": text, "prompt_speech_path": voice, "temperature": 0.8}
        async with httpx.AsyncClient(timeout=60) as client:
            gen_response = await client.post(self.api_url, headers=headers, json=payload)
            gen_response.raise_for_status()
            result = gen_response.json()
            download_url = result.get("download_url")
            if not download_url: raise TTSProviderError("sparktts", "No download URL")
            if not download_url.startswith(("http://", "https://")):
                download_url = f"{self.api_url.rsplit('/tts', 1)[0]}{download_url}"
            response = await client.get(download_url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                f.write(response.content)

    def _merge_audio_files(self, audio_files: List[str], output_file: str):
        combined = AudioSegment.empty()
        for audio_file in audio_files:
            try:
                file_format = os.path.splitext(audio_file)[1].lstrip('.').lower()
                segment = AudioSegment.from_file(audio_file, format=file_format)
                if len(segment) < 100: continue
                segment = segment.set_channels(2).set_frame_rate(44100)
                combined += segment
            except Exception as e:
                logger.error(f"Failed to merge {audio_file}: {e}")
        if len(combined) > 0:
            combined.export(output_file, format="mp3", bitrate="192k")
        for f in audio_files:
            if os.path.exists(f): os.remove(f)

    def split_script_by_speaker(self, text: str) -> List[Tuple[str, str]]:
        pattern = re.compile(r'<(Person1|Person2)>(.*?)</\1>', re.DOTALL)
        return [(speaker, dialogue.strip()) for speaker, dialogue in pattern.findall(text)]
