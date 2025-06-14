import os
from dotenv import load_dotenv
import yaml
import logging
# from typing import dict

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WORDPRESS Site settings
WORDPRESS_SITE = os.getenv("WORDPRESS_SITE")
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

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

# DeepSeek
AZURE_DEEPSEEK_API_KEY = os.getenv('AZURE_DEEPSEEK_API_KEY')
AZURE_DEEPSEEK_API_VERSION = os.getenv('AZURE_DEEPSEEK_API_VERSION')
AZURE_DEEPSEEK_ENDPOINT = os.getenv('AZURE_DEEPSEEK_ENDPOINT')

# Azure TTS
AZURE_TTS_API_KEY = os.getenv('AZURE_TTS_API_KEY')
AZURE_TTS_REGION = os.getenv('AZURE_TTS_REGION')

# Spark TTS
SPARK_TTS_API_KEY = os.getenv('SPARK_TTS_API_KEY')
SPARK_TTS_ENDPOINT = os.getenv('SPARK_TTS_ENDPOINT')
PERSON_1_VOICE_PATH = os.getenv('PERSON_1_VOICE_PATH')
PERSON_2_VOICE_PATH = os.getenv('PERSON_2_VOICE_PATH')

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

REQUIRE_LOGIN = False  # Set to False to disable login requirement

def resolve_path(relative_path):
    """Convert config-relative paths to absolute paths based on project root"""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    return os.path.join(root_dir, relative_path)


def load_llm_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    config['output_directories'] = {
        'transcripts': resolve_path(config['output_directories']['transcripts']),
        'audio': resolve_path(config['output_directories']['audio'])
    }
    config['INTRO_MUSIC_PATH'] = resolve_path(config['INTRO_MUSIC_PATH'])
    config['OUTRO_MUSIC_PATH'] = resolve_path(config['OUTRO_MUSIC_PATH'])
    config['FIRST_EPISODE_FLAG_FILE'] = resolve_path(config['FIRST_EPISODE_FLAG_FILE'])
    config['conversation_config_path'] = resolve_path(config['conversation_config_path'])

    # Inject API keys from environment variables into the config
    config['llm_provider']['azure']['api_key'] = AZURE_OPENAI_API_KEY
    config['llm_provider']['azure']['endpoint'] = AZURE_OPENAI_ENDPOINT
    config['llm_provider']['azure']['model_name'] = AZURE_OPENAI_MODEL_NAME
    config['llm_provider']['azure']['api_version'] = AZURE_OPENAI_API_VERSION

    config['llm_provider']['openai']['api_key'] = OPENAI_API_KEY

    # Add DeepSeek configuration injections
    config['llm_provider']['deepseek'] = config['llm_provider'].get('deepseek', {})
    config['llm_provider']['deepseek']['api_key'] = AZURE_DEEPSEEK_API_KEY
    config['llm_provider']['deepseek']['endpoint'] = AZURE_DEEPSEEK_ENDPOINT
    config['llm_provider']['deepseek']['api_version'] = AZURE_DEEPSEEK_API_VERSION

    return config


# Load configuration from YAML
config = load_llm_config()

os.makedirs(config['output_directories']['transcripts'], exist_ok=True)
os.makedirs(config['output_directories']['audio'], exist_ok=True)
os.makedirs(os.path.dirname(config['FIRST_EPISODE_FLAG_FILE']), exist_ok=True)

def validate_config_paths():
    required_paths = [
        config["INTRO_MUSIC_PATH"],
        config["OUTRO_MUSIC_PATH"],
        config["conversation_config_path"]
    ]

    for path in required_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Critical path missing: {path}")


validate_config_paths()

# LLM Provider Configuration
LLM_PROVIDER = config['llm_provider']['provider']
AZURE_OPENAI_CONFIG = config['llm_provider'].get('azure', {})
OPENAI_CONFIG = config['llm_provider'].get('openai', {})
OLLAMA_CONFIG = config['llm_provider'].get('ollama', {})
DEEPSEEK_CONFIG = config['llm_provider'].get('deepseek', {})

# Load Podcast Music File Path
INTRO_MUSIC_PATH = config.get("INTRO_MUSIC_PATH")
OUTRO_MUSIC_PATH = config.get("OUTRO_MUSIC_PATH")
FIRST_EPISODE_FLAG_FILE = config.get("FIRST_EPISODE_FLAG_FILE")

# Extract the path to conversation_config.yaml
conversation_config_path = os.path.join(os.path.dirname(__file__), config.get("conversation_config_path", "conversation_config.yaml"))

def load_rss_feeds():
    """Load RSS feeds from the YAML configuration."""
    return config.get("rss_feeds", [])

def load_conversation_config() -> dict:
    """Load and validate conversation configuration with proper error handling"""
    # Get the resolved path from main config
    conv_config_path = config["conversation_config_path"]

    if not os.path.exists(conv_config_path):
        raise FileNotFoundError(
            f"Conversation config file missing at: {conv_config_path}\n"
            f"Current working directory: {os.getcwd()}"
        )

    try:
        with open(conv_config_path, 'r') as f:
            conv_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in conversation config: {str(e)}") from e
    except Exception as e:
        raise IOError(f"Error reading conversation config: {str(e)}") from e

    # Validate config structure
    required_keys = {
        'text_to_speech': ['elevenlabs', 'openai', 'azure', 'sparktts']
        # 'llm_settings': ['max_tokens', 'temperature']
    }

    for section, subsections in required_keys.items():
        if section not in conv_config:
            raise KeyError(f"Missing required section in conversation config: {section}")
        for subsection in subsections:
            if subsection not in conv_config[section]:
                raise KeyError(f"Missing required subsection '{subsection}' under '{section}'")

    # Validate API keys before injection
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY is not set in environment variables")
    if not AZURE_OPENAI_TTS_API_KEY:
        raise ValueError("AZURE_OPENAI_TTS_API_KEY is not set in environment variables")
    if not AZURE_TTS_API_KEY:
        raise ValueError("AZURE_TTS_API_KEY is not set in environment variables")

    # API key injection with type checking
    try:
        # ElevenLabs configuration
        conv_config['text_to_speech']['elevenlabs']['api_key'] = ELEVENLABS_API_KEY

        # OpenAI TTS configuration
        tts_openai = conv_config['text_to_speech']['openai']
        tts_openai.update({
            'api_key': AZURE_OPENAI_TTS_API_KEY,
            'api_base': AZURE_OPENAI_TTS_ENDPOINT,
            'api_version': AZURE_OPENAI_API_VERSION,
            'model': AZURE_OPENAI_TTS_MODEL_NAME,
            'deployment_name': AZURE_OPENAI_TTS_DEPLOYMENT_NAME
        })

        # Azure TTS configuration
        tts_azure = conv_config['text_to_speech']['azure']
        tts_azure.update({
            'api_key': AZURE_TTS_API_KEY,
            'region': AZURE_TTS_REGION,
            'api_base': f"https://{AZURE_TTS_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
        })

        conv_config['text_to_speech']['sparktts'] = {
            'api_url': SPARK_TTS_ENDPOINT,
            'api_token': SPARK_TTS_API_KEY,
            'default_prompts': {
                'question': PERSON_1_VOICE_PATH,
                'answer': PERSON_2_VOICE_PATH
            }
        }

    except KeyError as e:
        raise KeyError(f"Missing expected configuration section: {str(e)}") from e

    # Add debug logging
    logger.info(f"Successfully loaded conversation config from: {conv_config_path}")
    return conv_config


"""
def load_conversation_config():
    if not os.path.exists(conversation_config_path):
        raise FileNotFoundError(f"Conversation config file not found: {conversation_config_path}")

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
    config['text_to_speech']['azure']['region'] = AZURE_TTS_REGION
    config['text_to_speech']['azure'][
        'api_base'] = f"https://{AZURE_TTS_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

    return config
"""
