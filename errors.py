"""
Custom exception classes for MyNotebookLM.

Provides structured error handling with clear, user-friendly messages.
"""

from typing import Optional


class MyNotebookLMError(Exception):
    """Base exception for all MyNotebookLM errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        if self.details:
            return f"{self.message}\n  Details: {self.details}"
        return self.message
    
    def user_message(self) -> str:
        """Return a user-friendly error message."""
        return self.message


# =============================================================================
# TTS Errors
# =============================================================================

class TTSError(MyNotebookLMError):
    """Base exception for TTS-related errors."""
    
    def __init__(self, provider: str, message: str, segment_index: Optional[int] = None, details: Optional[str] = None):
        self.provider = provider
        self.segment_index = segment_index
        prefix = f"[{provider}]"
        if segment_index is not None:
            prefix += f" Segment {segment_index}:"
        super().__init__(f"{prefix} {message}", details)
    
    def user_message(self) -> str:
        return f"Voice generation failed ({self.provider}): {self.message}"


class TTSProviderError(TTSError):
    """Error from TTS provider API (rate limits, auth, etc)."""
    pass


class TTSTimeoutError(TTSError):
    """TTS request timed out."""
    
    def user_message(self) -> str:
        return f"Voice generation timed out ({self.provider}). The service may be slow - please try again."


class TTSQuotaError(TTSError):
    """TTS API quota/rate limit exceeded."""
    
    def user_message(self) -> str:
        return f"Voice generation quota exceeded ({self.provider}). Please wait a moment and try again."


class TTSVoiceNotFoundError(TTSError):
    """Requested voice not available."""
    
    def __init__(self, provider: str, voice_name: str):
        self.voice_name = voice_name
        super().__init__(provider, f"Voice '{voice_name}' not found")
    
    def user_message(self) -> str:
        return f"Voice '{self.voice_name}' is not available. Please check your configuration."


# =============================================================================
# LLM Errors  
# =============================================================================

class LLMError(MyNotebookLMError):
    """Base exception for LLM-related errors."""
    
    def __init__(self, provider: str, message: str, details: Optional[str] = None):
        self.provider = provider
        super().__init__(f"[{provider}] {message}", details)
    
    def user_message(self) -> str:
        return f"AI generation failed ({self.provider}): {self.message}"


class LLMProviderError(LLMError):
    """Error from LLM provider API."""
    pass


class LLMTimeoutError(LLMError):
    """LLM request timed out."""
    
    def user_message(self) -> str:
        return "AI generation timed out. The content may be too long - try with less text."


class LLMQuotaError(LLMError):
    """LLM API quota exceeded."""
    
    def user_message(self) -> str:
        return f"AI service quota exceeded ({self.provider}). Please try again later."


# =============================================================================
# Content Extraction Errors
# =============================================================================

class ContentExtractionError(MyNotebookLMError):
    """Error extracting content from source."""
    
    def __init__(self, source_type: str, message: str, details: Optional[str] = None):
        self.source_type = source_type
        super().__init__(f"[{source_type}] {message}", details)
    
    def user_message(self) -> str:
        return f"Could not extract content from {self.source_type}: {self.message}"


class UnsupportedFileTypeError(ContentExtractionError):
    """File type not supported."""
    
    def __init__(self, file_extension: str):
        self.file_extension = file_extension
        super().__init__("file", f"Unsupported file type: {file_extension}")
    
    def user_message(self) -> str:
        return f"File type '{self.file_extension}' is not supported. Please use PDF, DOCX, TXT, or PPTX."


class FileTooLargeError(ContentExtractionError):
    """File exceeds size limit."""
    
    def __init__(self, file_size_mb: float, max_size_mb: float):
        self.file_size_mb = file_size_mb
        self.max_size_mb = max_size_mb
        super().__init__("file", f"File too large: {file_size_mb:.1f}MB (max: {max_size_mb}MB)")
    
    def user_message(self) -> str:
        return f"File is too large ({self.file_size_mb:.1f}MB). Maximum size is {self.max_size_mb}MB."


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigurationError(MyNotebookLMError):
    """Configuration error."""
    
    def user_message(self) -> str:
        return f"Configuration error: {self.message}. Please check your settings."


class MissingAPIKeyError(ConfigurationError):
    """Required API key not configured."""
    
    def __init__(self, key_name: str):
        self.key_name = key_name
        super().__init__(f"Missing required API key: {key_name}")
    
    def user_message(self) -> str:
        return f"API key '{self.key_name}' is not configured. Please add it to your .env file."
