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

    def test_download_script_before_tts(self, webui_content):
        """Should allow downloading script before TTS (Task 5)."""
        assert 'Download Script as TXT' in webui_content or 'download_script_txt' in webui_content

    def test_download_script_as_markdown(self, webui_content):
        """Should allow downloading script as markdown (Task 5)."""
        assert 'Download Script as Markdown' in webui_content or 'download_script_md' in webui_content


class TestConfigurableHostNames:
    """Tests for configurable host names feature (Task 4)."""

    @pytest.fixture
    def webui_content(self):
        with open('webui.py', 'r') as f:
            return f.read()

    @pytest.fixture
    def tts_content(self):
        with open('text_to_speech_conversion.py', 'r') as f:
            return f.read()

    @pytest.fixture
    def settings_content(self):
        with open('settings.py', 'r') as f:
            return f.read()

    def test_host_names_imported_in_webui(self, webui_content):
        """WebUI should import host name settings."""
        assert 'HOST_1_NAME' in webui_content
        assert 'HOST_2_NAME' in webui_content

    def test_sidebar_host_configuration(self, webui_content):
        """WebUI should have sidebar host configuration."""
        assert 'st.sidebar' in webui_content
        assert 'Host 1 Name' in webui_content or 'host_1_name' in webui_content
        assert 'Host 2 Name' in webui_content or 'host_2_name' in webui_content

    def test_host_names_passed_to_tts(self, webui_content):
        """convert_script_to_audio should receive host names."""
        assert 'host_1_name=' in webui_content
        assert 'host_2_name=' in webui_content

    def test_tts_accepts_host_names(self, tts_content):
        """TTS functions should accept host name parameters."""
        assert 'host_1_name=None' in tts_content or 'host_1_name' in tts_content
        assert 'host_2_name=None' in tts_content or 'host_2_name' in tts_content

    def test_settings_has_host_names(self, settings_content):
        """Settings should define HOST_1_NAME and HOST_2_NAME."""
        assert 'HOST_1_NAME' in settings_content
        assert 'HOST_2_NAME' in settings_content
        assert 'host_1_name' in settings_content
        assert 'host_2_name' in settings_content

    def test_host_names_have_defaults(self, settings_content):
        """Host names should have default values."""
        assert 'default="Jack"' in settings_content
        assert 'default="Corr"' in settings_content
