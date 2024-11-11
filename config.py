import os
from dotenv import load_dotenv
import yaml

load_dotenv()

# Azure OpenAI API settings
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

# Buzzsprout API settings
BUZZSPROUT_API_TOKEN = os.getenv('BUZZSPROUT_API_TOKEN')
BUZZSPROUT_PODCAST_ID = os.getenv('BUZZSPROUT_PODCAST_ID')

def load_conversation_config(conversation_config_path='conversation_config.yaml'):
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
    config['text_to_speech']['azure']['api_base'] = f"https://{AZURE_TTS_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"


    return config