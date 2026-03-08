"""Tests for WebUI structure and features."""

import pytest


class TestWebUIStructure:
    """Tests for WebUI file structure."""
    
    @pytest.fixture
    def webui_content(self):
        with open('webui.py', 'r') as f:
            return f.read()
    
    def test_imports_progress_module(self, webui_content):
        """WebUI should import progress module."""
        assert 'from progress import' in webui_content
    
    def test_imports_errors_module(self, webui_content):
        """WebUI should import errors module."""
        assert 'from errors import' in webui_content
    
    def test_has_input_tabs(self, webui_content):
        """WebUI should have tabbed input interface."""
        assert 'st.tabs' in webui_content
        assert 'Upload Files' in webui_content
        assert 'URL / YouTube' in webui_content
        assert 'Paste Text' in webui_content


class TestURLInput:
    """Tests for URL/YouTube input feature."""
    
    @pytest.fixture
    def webui_content(self):
        with open('webui.py', 'r') as f:
            return f.read()
    
    def test_url_input_field(self, webui_content):
        """Should have URL input field."""
        assert 'st.text_input' in webui_content
        assert 'url_input' in webui_content.lower() or 'URL' in webui_content
    
    def test_extract_url_button(self, webui_content):
        """Should have extract from URL button."""
        assert 'Extract from URL' in webui_content or 'extract_url' in webui_content


class TestTextPasteInput:
    """Tests for text paste input feature."""
    
    @pytest.fixture
    def webui_content(self):
        with open('webui.py', 'r') as f:
            return f.read()
    
    def test_text_area(self, webui_content):
        """Should have text area for pasting."""
        assert 'st.text_area' in webui_content
    
    def test_use_text_button(self, webui_content):
        """Should have button to use pasted text."""
        assert 'Use This Text' in webui_content or 'use_text' in webui_content


class TestScriptPreview:
    """Tests for script preview/editor feature."""
    
    @pytest.fixture
    def webui_content(self):
        with open('webui.py', 'r') as f:
            return f.read()
    
    def test_script_preview_section(self, webui_content):
        """Should have script preview section."""
        assert 'Script Preview' in webui_content
    
    def test_generate_script_button(self, webui_content):
        """Should have generate script button."""
        assert 'Generate Script' in webui_content
    
    def test_script_editing(self, webui_content):
        """Should allow script editing before audio."""
        assert 'edited_script' in webui_content or 'podcast_script' in webui_content
    
    def test_generate_from_script_button(self, webui_content):
        """Should have generate audio from script button."""
        assert 'Generate Audio from Script' in webui_content or 'gen_audio_from_script' in webui_content


class TestProgressIndicators:
    """Tests for progress indicator feature."""
    
    @pytest.fixture
    def webui_content(self):
        with open('webui.py', 'r') as f:
            return f.read()
    
    def test_progress_bar(self, webui_content):
        """Should use st.progress for progress bar."""
        assert 'st.progress' in webui_content
    
    def test_progress_tracker_used(self, webui_content):
        """Should use ProgressTracker class."""
        assert 'ProgressTracker' in webui_content
    
    def test_progress_stages_used(self, webui_content):
        """Should use ProgressStage enum."""
        assert 'ProgressStage' in webui_content


class TestDownloadFeature:
    """Tests for transcript download feature."""
    
    @pytest.fixture
    def webui_content(self):
        with open('webui.py', 'r') as f:
            return f.read()
    
    def test_download_button(self, webui_content):
        """Should have download button."""
        assert 'st.download_button' in webui_content
    
    def test_download_transcript(self, webui_content):
        """Should allow downloading transcript."""
        assert 'Download Transcript' in webui_content or 'transcript' in webui_content.lower()
