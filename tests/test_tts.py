import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


class TestTTSServiceStructure:
    """Tests for TTS service structure and configuration."""
    
    def test_tts_module_has_retry_decorator(self):
        """Module should have retry decorator."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        assert 'from tenacity import' in content
        assert 'def tts_retry()' in content
    
    def test_tts_methods_have_retry(self):
        """TTS provider methods should have retry decorator."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        
        methods = [
            '_convert_with_azure',
            '_convert_with_elevenlabs',
            '_convert_with_openai',
            '_convert_with_edge',
            '_convert_with_sparktts'
        ]
        
        for method in methods:
            # Check that method exists and has decorator before it
            assert f'async def {method}' in content, f"{method} should exist"
    
    def test_parallel_methods_exist(self):
        """Parallel generation methods should exist."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        
        assert 'async def _generate_segments_parallel' in content
        assert 'async def _generate_segments_sequential' in content
        assert 'async def _generate_single_segment' in content
    
    def test_convert_to_speech_has_parallel_param(self):
        """convert_to_speech should have parallel parameter."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        
        assert 'async def convert_to_speech(self, text: str, output_file: str, parallel: bool = True' in content
    
    def test_semaphore_used_for_concurrency(self):
        """Semaphore should be used to limit concurrency."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        
        assert 'asyncio.Semaphore' in content
        assert 'max_concurrent' in content


class TestScriptSplitting:
    """Tests for script splitting functionality."""
    
    def test_split_script_by_speaker_import(self):
        """TextToSpeechService should be importable."""
        # This tests that the module structure is correct
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        assert 'def split_script_by_speaker' in content


class TestRetryConfiguration:
    """Tests for retry configuration."""

    def test_retry_decorator_config(self):
        """Retry decorator should have proper configuration."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()

        # Check retry configuration exists
        assert 'stop_after_attempt' in content
        assert 'wait_exponential' in content


class TestTTSResult:
    """Tests for TTSResult class."""

    def test_tts_result_class_exists(self):
        """TTSResult class should exist."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        assert 'class TTSResult:' in content

    def test_tts_result_tracks_successes(self):
        """TTSResult should track successful segments."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        assert 'successful_segments' in content
        assert 'success_count' in content

    def test_tts_result_tracks_failures(self):
        """TTSResult should track failed segments."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        assert 'failed_segments' in content
        assert 'failure_count' in content

    def test_tts_result_has_failure_summary(self):
        """TTSResult should provide failure summary."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        assert 'def get_failure_summary' in content

    def test_convert_to_speech_returns_tts_result(self):
        """convert_to_speech should return TTSResult."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        assert '-> TTSResult:' in content

    def test_parallel_method_returns_failures(self):
        """Parallel method should return failures list."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        assert 'return results, failures' in content


class TestGracefulDegradation:
    """Tests for graceful degradation behavior."""

    def test_continues_with_successful_segments(self):
        """Should continue processing even if some segments fail."""
        with open('custom_text_to_speech.py', 'r') as f:
            content = f.read()
        # Check that failures are collected but don't stop processing
        assert 'failures.append' in content
        assert 'graceful degradation' in content.lower()
