import os
from dotenv import load_dotenv
import yaml

load_dotenv()

# Azure OpenAI API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')
AZURE_OPENAI_MODEL_NAME = os.getenv('AZURE_OPENAI_MODEL_NAME')
AZURE_OPENAI_TTS_ENDPOINT = os.getenv('AZURE_OPENAI_TTS_ENDPOINT')
AZURE_OPENAI_TTS_API_KEY = os.getenv('AZURE_OPENAI_TTS_API_KEY')
AZURE_OPENAI_TTS_MODEL_NAME = os.getenv('AZURE_OPENAI_TTS_MODEL_NAME')
AZURE_OPENAI_TTS_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_TTS_DEPLOYMENT_NAME')

# Azure TTS
AZURE_TTS_API_KEY = os.getenv('AZURE_TTS_API_KEY')
AZURE_TTS_REGION = os.getenv('AZURE_TTS_REGION')

# Eleven Labs API key
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# Jina API key (if you're using it)
# JINA_API_KEY = os.getenv('JINA_API_KEY')

# Podcast settings
PODCAST_TITLE = os.getenv('PODCAST_TITLE')
PODCAST_DESCRIPTION = os.getenv('PODCAST_DESCRIPTION')
UPLOAD_SCHEDULE = os.getenv('UPLOAD_SCHEDULE')

# Backend authentication settings
DJANGO_BACKEND_URL = os.getenv("DJANGO_BACKEND_URL")
API_KEY = os.getenv("API_KEY")
FRONTENDURL = os.getenv("FRONTENDURL")

REQUIRE_LOGIN = True  # Set to False to disable login requirement


def load_llm_config(config_path='config.yaml'):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Inject API keys from environment variables into the config
    config['llm_provider']['azure']['api_key'] = AZURE_OPENAI_API_KEY
    config['llm_provider']['azure']['endpoint'] = AZURE_OPENAI_ENDPOINT
    config['llm_provider']['azure']['model_name'] = AZURE_OPENAI_MODEL_NAME
    config['llm_provider']['azure']['api_version'] = AZURE_OPENAI_API_VERSION

    config['llm_provider']['openai']['api_key'] = OPENAI_API_KEY

    return config


# Load configuration from YAML
config = load_llm_config()

# LLM Provider Configuration
LLM_PROVIDER = config['llm_provider']['provider']
AZURE_OPENAI_CONFIG = config['llm_provider'].get('azure', {})
OPENAI_CONFIG = config['llm_provider'].get('openai', {})
OLLAMA_CONFIG = config['llm_provider'].get('ollama', {})

# Load Podcast Music File Path
INTRO_MUSIC_PATH = config.get("INTRO_MUSIC_PATH")
OUTRO_MUSIC_PATH = config.get("OUTRO_MUSIC_PATH")

FIRST_EPISODE_FLAG_FILE = config.get("FIRST_EPISODE_FLAG_FILE")

# Extract the path to conversation_config.yaml
conversation_config_path = config.get("conversation_config_path", "conversation_config.yaml")

def load_conversation_config():
    with open(conversation_config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Inject API keys into the configuration
    config['text_to_speech']['elevenlabs']['api_key'] = ELEVENLABS_API_KEY
    config['text_to_speech']['openai']['api_key'] = AZURE_OPENAI_TTS_API_KEY
    config['text_to_speech']['openai']['api_base'] = AZURE_OPENAI_TTS_ENDPOINT
    config['text_to_speech']['openai']['api_version'] = AZURE_OPENAI_API_VERSION
    config['text_to_speech']['openai']['model'] = AZURE_OPENAI_TTS_MODEL_NAME
    config['text_to_speech']['openai']['deployment_name'] = AZURE_OPENAI_TTS_DEPLOYMENT_NAME
    config['text_to_speech']['azure']['api_key'] = AZURE_TTS_API_KEY
    config['text_to_speech']['azure'][
        'api_base'] = f"https://{AZURE_TTS_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

    return config
