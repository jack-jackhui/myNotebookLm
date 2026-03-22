"""
Unified configuration management using Pydantic Settings.

This module provides a centralized, type-safe configuration system that:
- Loads environment variables from .env file
- Loads YAML configuration from config.yaml
- Validates all settings at startup
- Provides type hints and IDE autocompletion

Backward Compatibility:
- Reads the same .env file format
- Reads the same config.yaml format  
- Exports the same variable names as config.py
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import lru_cache

import yaml
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Project root directory
ROOT_DIR = Path(__file__).parent.absolute()


class EnvSettings(BaseSettings):
    """Environment variables from .env file."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # WordPress settings
    wordpress_site: Optional[str] = Field(default=None, alias="WORDPRESS_SITE")
    wordpress_username: Optional[str] = Field(default=None, alias="WORDPRESS_USERNAME")
    wordpress_app_password: Optional[str] = Field(default=None, alias="WORDPRESS_APP_PASSWORD")
    
    # OpenAI settings
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    
    # Azure OpenAI settings
    azure_openai_api_key: Optional[str] = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: Optional[str] = Field(default=None, alias="AZURE_OPENAI_API_VERSION")
    azure_openai_model_name: Optional[str] = Field(default=None, alias="AZURE_OPENAI_MODEL_NAME")
    
    # Azure OpenAI TTS settings
    azure_openai_tts_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_TTS_ENDPOINT")
    azure_openai_tts_api_key: Optional[str] = Field(default=None, alias="AZURE_OPENAI_TTS_API_KEY")
    azure_openai_tts_model_name: Optional[str] = Field(default=None, alias="AZURE_OPENAI_TTS_MODEL_NAME")
    azure_openai_tts_deployment_name: Optional[str] = Field(default=None, alias="AZURE_OPENAI_TTS_DEPLOYMENT_NAME")
    
    # DeepSeek settings
    azure_deepseek_api_key: Optional[str] = Field(default=None, alias="AZURE_DEEPSEEK_API_KEY")
    azure_deepseek_api_version: Optional[str] = Field(default=None, alias="AZURE_DEEPSEEK_API_VERSION")
    azure_deepseek_endpoint: Optional[str] = Field(default=None, alias="AZURE_DEEPSEEK_ENDPOINT")
    
    # Azure TTS settings
    azure_tts_api_key: Optional[str] = Field(default=None, alias="AZURE_TTS_API_KEY")
    azure_tts_region: Optional[str] = Field(default=None, alias="AZURE_TTS_REGION")
    
    # Spark TTS settings
    spark_tts_api_key: Optional[str] = Field(default=None, alias="SPARK_TTS_API_KEY")
    spark_tts_endpoint: Optional[str] = Field(default=None, alias="SPARK_TTS_ENDPOINT")
    person_1_voice_path: Optional[str] = Field(default=None, alias="PERSON_1_VOICE_PATH")
    person_2_voice_path: Optional[str] = Field(default=None, alias="PERSON_2_VOICE_PATH")
    
    # ElevenLabs settings
    elevenlabs_api_key: Optional[str] = Field(default=None, alias="ELEVENLABS_API_KEY")
    
    # Podcast settings
    podcast_title: Optional[str] = Field(default=None, alias="PODCAST_TITLE")
    podcast_description: Optional[str] = Field(default=None, alias="PODCAST_DESCRIPTION")
    upload_schedule: Optional[str] = Field(default=None, alias="UPLOAD_SCHEDULE")

    # Host name settings (configurable podcast hosts)
    host_1_name: str = Field(default="Jack", alias="HOST_1_NAME")
    host_2_name: str = Field(default="Corr", alias="HOST_2_NAME")
    
    # Backend authentication settings
    django_backend_url: Optional[str] = Field(default=None, alias="DJANGO_BACKEND_URL")
    api_key: Optional[str] = Field(default=None, alias="API_KEY")
    frontend_url: Optional[str] = Field(default=None, alias="FRONTENDURL")


class YamlConfig:
    """YAML configuration loader."""
    
    def __init__(self, config_path: Path = ROOT_DIR / "config.yaml"):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {self.config_path}")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        return self._config[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self._config
    
    @property
    def raw(self) -> Dict[str, Any]:
        """Return raw config dict."""
        return self._config


class Settings:
    """
    Unified settings manager combining environment variables and YAML config.
    
    Usage:
        from settings import settings
        
        # Access env vars
        api_key = settings.env.azure_openai_api_key
        
        # Access YAML config
        llm_provider = settings.yaml.get('llm_provider', {})
        
        # Access resolved paths
        intro_music = settings.intro_music_path
    """
    
    def __init__(self):
        self.env = EnvSettings()
        self.yaml = YamlConfig()
        self._resolved_config: Optional[Dict[str, Any]] = None
    
    def _resolve_path(self, relative_path: str) -> Path:
        """Convert relative path to absolute path based on project root."""
        return ROOT_DIR / relative_path
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get fully resolved configuration (cached)."""
        if self._resolved_config is not None:
            return self._resolved_config
        
        config = dict(self.yaml.raw)
        
        # Resolve output directories
        if 'output_directories' in config:
            config['output_directories'] = {
                'transcripts': str(self._resolve_path(config['output_directories']['transcripts'])),
                'audio': str(self._resolve_path(config['output_directories']['audio']))
            }
        
        # Resolve paths
        for path_key in ['INTRO_MUSIC_PATH', 'OUTRO_MUSIC_PATH', 'FIRST_EPISODE_FLAG_FILE', 'conversation_config_path']:
            if path_key in config:
                config[path_key] = str(self._resolve_path(config[path_key]))
        
        # Inject API keys into LLM provider config
        if 'llm_provider' in config:
            if 'azure' in config['llm_provider']:
                config['llm_provider']['azure'].update({
                    'api_key': self.env.azure_openai_api_key,
                    'endpoint': self.env.azure_openai_endpoint,
                    'model_name': self.env.azure_openai_model_name,
                    'api_version': self.env.azure_openai_api_version,
                })
            if 'openai' in config['llm_provider']:
                config['llm_provider']['openai']['api_key'] = self.env.openai_api_key
            if 'deepseek' not in config['llm_provider']:
                config['llm_provider']['deepseek'] = {}
            config['llm_provider']['deepseek'].update({
                'api_key': self.env.azure_deepseek_api_key,
                'endpoint': self.env.azure_deepseek_endpoint,
                'api_version': self.env.azure_deepseek_api_version,
            })
        
        self._resolved_config = config
        return config
    
    @property
    def llm_provider(self) -> str:
        """Get the configured LLM provider name."""
        return self.config.get('llm_provider', {}).get('provider', 'azure')
    
    @property
    def intro_music_path(self) -> Optional[str]:
        return self.config.get('INTRO_MUSIC_PATH')
    
    @property
    def outro_music_path(self) -> Optional[str]:
        return self.config.get('OUTRO_MUSIC_PATH')
    
    @property
    def conversation_config_path(self) -> Optional[str]:
        return self.config.get('conversation_config_path')
    
    @property
    def require_login(self) -> bool:
        """Whether login is required for the web UI."""
        return False  # Default, can be made configurable
    
    def load_conversation_config(self) -> Dict[str, Any]:
        """Load and validate conversation configuration with API key injection."""
        conv_config_path = self.conversation_config_path
        
        if not conv_config_path or not Path(conv_config_path).exists():
            raise FileNotFoundError(
                f"Conversation config file missing at: {conv_config_path}\n"
                f"Current working directory: {os.getcwd()}"
            )
        
        with open(conv_config_path, 'r') as f:
            conv_config = yaml.safe_load(f)
        
        # Validate required sections
        required_tts_providers = ['elevenlabs', 'openai', 'azure', 'sparktts']
        if 'text_to_speech' not in conv_config:
            raise KeyError("Missing required section: text_to_speech")
        for provider in required_tts_providers:
            if provider not in conv_config['text_to_speech']:
                raise KeyError(f"Missing TTS provider config: {provider}")
        
        # Inject API keys
        conv_config['text_to_speech']['elevenlabs']['api_key'] = self.env.elevenlabs_api_key
        
        conv_config['text_to_speech']['openai'].update({
            'api_key': self.env.azure_openai_tts_api_key,
            'api_base': self.env.azure_openai_tts_endpoint,
            'api_version': self.env.azure_openai_api_version,
            'model': self.env.azure_openai_tts_model_name,
            'deployment_name': self.env.azure_openai_tts_deployment_name,
        })
        
        conv_config['text_to_speech']['azure'].update({
            'api_key': self.env.azure_tts_api_key,
            'region': self.env.azure_tts_region,
            'api_base': f"https://{self.env.azure_tts_region}.tts.speech.microsoft.com/cognitiveservices/v1"
        })
        
        conv_config['text_to_speech']['sparktts'] = {
            'api_url': self.env.spark_tts_endpoint,
            'api_token': self.env.spark_tts_api_key,
            'default_prompts': {
                'question': self.env.person_1_voice_path,
                'answer': self.env.person_2_voice_path,
            }
        }
        
        logger.info(f"Loaded conversation config from: {conv_config_path}")
        return conv_config
    
    def load_rss_feeds(self) -> List[Dict[str, Any]]:
        """Load RSS feeds from configuration."""
        return self.config.get('rss_feeds', [])
    
    def ensure_directories(self) -> None:
        """Create required output directories."""
        if 'output_directories' in self.config:
            os.makedirs(self.config['output_directories']['transcripts'], exist_ok=True)
            os.makedirs(self.config['output_directories']['audio'], exist_ok=True)
        
        flag_file = self.config.get('FIRST_EPISODE_FLAG_FILE')
        if flag_file:
            os.makedirs(os.path.dirname(flag_file), exist_ok=True)


# Singleton instance
@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenient access
settings = get_settings()


# =============================================================================
# BACKWARD COMPATIBILITY EXPORTS
# These match the exact variable names from config.py for drop-in replacement
# =============================================================================

# Environment variables (direct access for backward compatibility)
WORDPRESS_SITE = settings.env.wordpress_site
WORDPRESS_USERNAME = settings.env.wordpress_username
WORDPRESS_APP_PASSWORD = settings.env.wordpress_app_password

OPENAI_API_KEY = settings.env.openai_api_key
AZURE_OPENAI_API_KEY = settings.env.azure_openai_api_key
AZURE_OPENAI_ENDPOINT = settings.env.azure_openai_endpoint
AZURE_OPENAI_API_VERSION = settings.env.azure_openai_api_version
AZURE_OPENAI_MODEL_NAME = settings.env.azure_openai_model_name
AZURE_OPENAI_TTS_ENDPOINT = settings.env.azure_openai_tts_endpoint
AZURE_OPENAI_TTS_API_KEY = settings.env.azure_openai_tts_api_key
AZURE_OPENAI_TTS_MODEL_NAME = settings.env.azure_openai_tts_model_name
AZURE_OPENAI_TTS_DEPLOYMENT_NAME = settings.env.azure_openai_tts_deployment_name

AZURE_DEEPSEEK_API_KEY = settings.env.azure_deepseek_api_key
AZURE_DEEPSEEK_API_VERSION = settings.env.azure_deepseek_api_version
AZURE_DEEPSEEK_ENDPOINT = settings.env.azure_deepseek_endpoint

AZURE_TTS_API_KEY = settings.env.azure_tts_api_key
AZURE_TTS_REGION = settings.env.azure_tts_region

SPARK_TTS_API_KEY = settings.env.spark_tts_api_key
SPARK_TTS_ENDPOINT = settings.env.spark_tts_endpoint
PERSON_1_VOICE_PATH = settings.env.person_1_voice_path
PERSON_2_VOICE_PATH = settings.env.person_2_voice_path

ELEVENLABS_API_KEY = settings.env.elevenlabs_api_key

PODCAST_TITLE = settings.env.podcast_title
PODCAST_DESCRIPTION = settings.env.podcast_description
UPLOAD_SCHEDULE = settings.env.upload_schedule

DJANGO_BACKEND_URL = settings.env.django_backend_url
API_KEY = settings.env.api_key
FRONTENDURL = settings.env.frontend_url

REQUIRE_LOGIN = settings.require_login

# Host names (configurable podcast hosts)
HOST_1_NAME = settings.env.host_1_name
HOST_2_NAME = settings.env.host_2_name

# Configuration objects
config = settings.config

# LLM Provider configs
LLM_PROVIDER = settings.llm_provider
AZURE_OPENAI_CONFIG = settings.config.get('llm_provider', {}).get('azure', {})
OPENAI_CONFIG = settings.config.get('llm_provider', {}).get('openai', {})
OLLAMA_CONFIG = settings.config.get('llm_provider', {}).get('ollama', {})
DEEPSEEK_CONFIG = settings.config.get('llm_provider', {}).get('deepseek', {})

# Paths
INTRO_MUSIC_PATH = settings.intro_music_path
OUTRO_MUSIC_PATH = settings.outro_music_path
FIRST_EPISODE_FLAG_FILE = settings.config.get('FIRST_EPISODE_FLAG_FILE')
conversation_config_path = settings.conversation_config_path

# Functions
load_conversation_config = settings.load_conversation_config
load_rss_feeds = settings.load_rss_feeds
load_llm_config = lambda: settings.config


# Initialize directories on import
try:
    settings.ensure_directories()
except Exception as e:
    logger.warning(f"Could not create directories: {e}")

def configure_logging(level: str = "INFO") -> None:
    """Configure application-wide logging."""
    import logging
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


# Initialize logging on import
configure_logging()
