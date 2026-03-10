"""Tests for the settings module."""

import pytest
import os


class TestEnvSettings:
    """Tests for environment variable loading."""
    
    def test_env_settings_loads(self):
        """EnvSettings should load without errors."""
        from settings import EnvSettings
        settings = EnvSettings()
        assert settings is not None
    
    def test_env_settings_reads_env_vars(self, monkeypatch):
        """EnvSettings should read environment variables."""
        # Force specific test values by setting them BEFORE import
        # Use monkeypatch.setenv which overrides any existing values
        monkeypatch.setenv('AZURE_OPENAI_API_KEY', 'test-key')
        monkeypatch.setenv('ELEVENLABS_API_KEY', 'test-elevenlabs-key')
        
        # Must create fresh instance to pick up new env vars
        from settings import EnvSettings
        settings = EnvSettings()
        
        assert settings.azure_openai_api_key == 'test-key'
        assert settings.elevenlabs_api_key == 'test-elevenlabs-key'
    
    def test_env_settings_optional_vars_default_none(self, monkeypatch):
        """Optional env vars should default to None when not set."""
        # Explicitly remove any existing WordPress settings
        monkeypatch.delenv('WORDPRESS_SITE', raising=False)
        monkeypatch.delenv('WORDPRESS_USERNAME', raising=False)
        monkeypatch.delenv('WORDPRESS_APP_PASSWORD', raising=False)
        
        # Must create fresh instance after env changes
        from settings import EnvSettings
        settings = EnvSettings()
        
        assert settings.wordpress_site is None


class TestSettings:
    """Tests for the main Settings class."""
    
    def test_settings_singleton(self):
        """get_settings() should return cached instance."""
        from settings import get_settings
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
    
    def test_settings_env_access(self):
        """Settings should provide access to env vars."""
        from settings import settings
        assert settings.env.azure_openai_api_key is not None
    
    def test_require_login_default_false(self):
        """REQUIRE_LOGIN should default to False."""
        from settings import REQUIRE_LOGIN
        assert REQUIRE_LOGIN is False


class TestBackwardCompatibility:
    """Tests for backward compatibility with config.py."""
    
    def test_module_level_exports(self):
        """Module should export same variables as config.py."""
        from settings import (
            AZURE_OPENAI_API_KEY,
            ELEVENLABS_API_KEY,
            AZURE_TTS_API_KEY,
            REQUIRE_LOGIN,
        )
        # Just verify they're importable
        assert AZURE_OPENAI_API_KEY is not None
        assert ELEVENLABS_API_KEY is not None
    
    def test_load_llm_config_function(self):
        """load_llm_config should be callable."""
        from settings import load_llm_config
        assert callable(load_llm_config)
    
    def test_load_rss_feeds_function(self):
        """load_rss_feeds should be callable and return list."""
        from settings import load_rss_feeds
        result = load_rss_feeds()
        assert isinstance(result, list)
