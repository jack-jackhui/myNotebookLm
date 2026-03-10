"""Tests for the errors module."""

import pytest
from errors import (
    MyNotebookLMError,
    TTSError, TTSProviderError, TTSTimeoutError, TTSQuotaError, TTSVoiceNotFoundError,
    LLMError, LLMProviderError, LLMTimeoutError, LLMQuotaError,
    ContentExtractionError, UnsupportedFileTypeError, FileTooLargeError,
    ConfigurationError, MissingAPIKeyError,
)


class TestBaseError:
    """Tests for MyNotebookLMError base class."""
    
    def test_base_error_message(self):
        err = MyNotebookLMError("Test error")
        assert str(err) == "Test error"
    
    def test_base_error_with_details(self):
        err = MyNotebookLMError("Test error", details="More info")
        assert "More info" in str(err)
    
    def test_user_message(self):
        err = MyNotebookLMError("Test error")
        assert err.user_message() == "Test error"


class TestTTSErrors:
    """Tests for TTS error classes."""
    
    def test_tts_error_includes_provider(self):
        err = TTSError("azure", "Connection failed")
        assert "azure" in str(err)
        assert "Connection failed" in str(err)
    
    def test_tts_error_with_segment_index(self):
        err = TTSError("elevenlabs", "Timeout", segment_index=5)
        assert "5" in str(err)
        assert err.segment_index == 5
    
    def test_tts_timeout_user_message(self):
        err = TTSTimeoutError("azure", "30s timeout")
        msg = err.user_message()
        assert "azure" in msg.lower() or "timeout" in msg.lower()
        assert "try again" in msg.lower()
    
    def test_tts_quota_user_message(self):
        err = TTSQuotaError("elevenlabs", "Rate limit exceeded")
        msg = err.user_message()
        assert "quota" in msg.lower() or "exceeded" in msg.lower()
    
    def test_tts_voice_not_found(self):
        err = TTSVoiceNotFoundError("azure", "CustomVoice")
        assert err.voice_name == "CustomVoice"
        assert "CustomVoice" in err.user_message()


class TestLLMErrors:
    """Tests for LLM error classes."""
    
    def test_llm_error_includes_provider(self):
        err = LLMError("openai", "API error")
        assert "openai" in str(err)
    
    def test_llm_timeout_user_message(self):
        err = LLMTimeoutError("azure", "Timeout")
        msg = err.user_message()
        assert "timed out" in msg.lower() or "timeout" in msg.lower()
    
    def test_llm_quota_user_message(self):
        err = LLMQuotaError("openai", "Rate limit")
        msg = err.user_message()
        assert "quota" in msg.lower()


class TestContentExtractionErrors:
    """Tests for content extraction errors."""
    
    def test_unsupported_file_type(self):
        err = UnsupportedFileTypeError(".xyz")
        assert ".xyz" in str(err)
        assert "xyz" in err.user_message()
    
    def test_file_too_large(self):
        err = FileTooLargeError(150.5, 100.0)
        assert err.file_size_mb == 150.5
        assert err.max_size_mb == 100.0
        assert "150" in err.user_message()
        assert "100" in err.user_message()


class TestConfigurationErrors:
    """Tests for configuration errors."""
    
    def test_missing_api_key(self):
        err = MissingAPIKeyError("OPENAI_API_KEY")
        assert "OPENAI_API_KEY" in str(err)
        assert "OPENAI_API_KEY" in err.user_message()
