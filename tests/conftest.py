"""Pytest configuration and shared fixtures."""

import os
import sys
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set up test environment before importing app modules
os.environ.setdefault('AZURE_OPENAI_API_KEY', 'test-key')
os.environ.setdefault('AZURE_OPENAI_ENDPOINT', 'https://test.openai.azure.com')
os.environ.setdefault('AZURE_OPENAI_API_VERSION', '2023-05-15')
os.environ.setdefault('AZURE_OPENAI_MODEL_NAME', 'gpt-4')
os.environ.setdefault('OPENAI_API_KEY', 'test-openai-key')
os.environ.setdefault('ELEVENLABS_API_KEY', 'test-elevenlabs-key')
os.environ.setdefault('AZURE_TTS_API_KEY', 'test-azure-tts-key')
os.environ.setdefault('AZURE_TTS_REGION', 'eastus')
os.environ.setdefault('AZURE_OPENAI_TTS_API_KEY', 'test-tts-key')
os.environ.setdefault('AZURE_OPENAI_TTS_ENDPOINT', 'https://test-tts.openai.azure.com')
os.environ.setdefault('AZURE_OPENAI_TTS_MODEL_NAME', 'tts-1')
os.environ.setdefault('AZURE_OPENAI_TTS_DEPLOYMENT_NAME', 'tts-deployment')
os.environ.setdefault('SPARK_TTS_API_KEY', 'test-spark-key')
os.environ.setdefault('SPARK_TTS_ENDPOINT', 'https://spark.example.com')
os.environ.setdefault('PERSON_1_VOICE_PATH', '/voices/p1.wav')
os.environ.setdefault('PERSON_2_VOICE_PATH', '/voices/p2.wav')


@pytest.fixture
def sample_script():
    """Sample podcast script for testing."""
    return """<Person1>Welcome to the show! Today we're discussing AI.</Person1>
<Person2>Thanks for having me. AI is fascinating.</Person2>
<Person1>What do you think about large language models?</Person1>
<Person2>They're transforming how we work with text and code.</Person2>"""


@pytest.fixture
def sample_content():
    """Sample content text for testing."""
    return """Artificial Intelligence (AI) is transforming industries worldwide.
    Machine learning enables computers to learn from data.
    Natural language processing allows machines to understand human language.
    These technologies are being applied in healthcare, finance, and more."""


@pytest.fixture
def temp_audio_dir(tmp_path):
    """Temporary directory for audio files."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    return audio_dir


@pytest.fixture
def mock_config(tmp_path):
    """Create mock config files for testing."""
    import yaml
    
    # Create directories
    (tmp_path / "configs").mkdir()
    (tmp_path / "music").mkdir()
    (tmp_path / "data" / "transcripts").mkdir(parents=True)
    (tmp_path / "data" / "audio").mkdir(parents=True)
    
    # Create dummy music files
    (tmp_path / "music" / "intro.mp3").touch()
    (tmp_path / "music" / "outro.mp3").touch()
    
    # Create config.yaml
    config = {
        'output_directories': {
            'transcripts': './data/transcripts',
            'audio': './data/audio'
        },
        'conversation_config_path': './configs/conversation_config.yaml',
        'INTRO_MUSIC_PATH': './music/intro.mp3',
        'OUTRO_MUSIC_PATH': './music/outro.mp3',
        'FIRST_EPISODE_FLAG_FILE': './data/first_episode_flag.txt',
        'llm_provider': {
            'provider': 'azure',
            'azure': {
                'endpoint': 'https://test.openai.azure.com',
                'model_name': 'gpt-4',
                'api_version': '2023-05-15'
            },
            'openai': {'model_name': 'gpt-4'},
            'ollama': {'model_name': 'llama3.2', 'host': 'localhost', 'port': 11434}
        }
    }
    
    with open(tmp_path / "config.yaml", 'w') as f:
        yaml.dump(config, f)
    
    # Create conversation_config.yaml
    conv_config = {
        'text_to_speech': {
            'default_tts_provider': 'edge',
            'elevenlabs': {
                'model': 'eleven_multilingual_v2',
                'default_voices': {'question': 'Brian', 'answer': 'Jessica'}
            },
            'openai': {
                'model': 'tts-1-hd',
                'default_voices': {'question': 'echo', 'answer': 'nova'}
            },
            'azure': {
                'default_voices': {'question': 'en-US-AndrewNeural', 'answer': 'en-US-AvaNeural'}
            },
            'edge': {
                'default_voices': {'question': 'en-US-GuyNeural', 'answer': 'en-US-JennyNeural'}
            },
            'sparktts': {
                'default_voices': {'question': 'male', 'answer': 'female'}
            }
        }
    }
    
    with open(tmp_path / "configs" / "conversation_config.yaml", 'w') as f:
        yaml.dump(conv_config, f)
    
    return tmp_path
