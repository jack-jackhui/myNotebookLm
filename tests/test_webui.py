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


class TestEpisodeLengthControl:
    """Tests for episode length control feature."""

    def test_episode_length_options_defined(self):
        """Episode length options should be defined."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'EPISODE_LENGTH_OPTIONS' in content

    def test_episode_length_has_all_options(self):
        """Should have Auto, 5min, 15min, 30min options."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert '"Auto"' in content
        assert '"5 min"' in content
        assert '"15 min"' in content
        assert '"30 min"' in content

    def test_episode_length_selectbox(self):
        """Should have a selectbox for episode length."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'st.selectbox' in content
        assert 'Target Duration' in content

    def test_estimate_audio_duration_function(self):
        """Should have audio duration estimation function."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'def estimate_audio_duration' in content

    def test_length_estimation_displayed(self):
        """Length estimation should be displayed to user."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'estimated_duration' in content
        assert 'Estimated duration' in content

    def test_target_word_count_passed_to_generator(self):
        """Target word count should be passed to script generator."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'target_word_count=' in content


class TestContentGeneratorLength:
    """Tests for content generator length parameter."""

    def test_azure_generator_inherits_target_word_count(self):
        """Azure content generator should inherit target_word_count handling."""
        from azure_content_generator import AzureContentGenerator
        from generic_content_generator import ContentGenerator
        assert issubclass(AzureContentGenerator, ContentGenerator)

    def test_openai_generator_inherits_target_word_count(self):
        """OpenAI content generator should inherit target_word_count handling."""
        from openai_content_generator import OpenAIContentGenerator
        from generic_content_generator import ContentGenerator
        assert issubclass(OpenAIContentGenerator, ContentGenerator)

    def test_deepseek_generator_inherits_target_word_count(self):
        """DeepSeek content generator should inherit target_word_count handling."""
        from deepseek_content_generator import DeepSeekContentGenerator
        from generic_content_generator import ContentGenerator
        assert issubclass(DeepSeekContentGenerator, ContentGenerator)

    def test_ollama_generator_inherits_target_word_count(self):
        """Ollama content generator should inherit target_word_count handling."""
        from ollama_content_generator import OllamaContentGenerator
        from generic_content_generator import ContentGenerator
        assert issubclass(OllamaContentGenerator, ContentGenerator)

    def test_base_generator_accepts_target_word_count(self):
        """Base content generator should accept target_word_count."""
        with open('generic_content_generator.py', 'r') as f:
            content = f.read()
        assert 'target_word_count' in content


class TestCustomIntroOutro:
    """Tests for custom intro/outro upload feature."""

    def test_custom_intro_upload_exists(self):
        """Should have file uploader for custom intro."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'custom_intro_upload' in content
        assert 'Upload Intro Audio' in content

    def test_custom_outro_upload_exists(self):
        """Should have file uploader for custom outro."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'custom_outro_upload' in content
        assert 'Upload Outro Audio' in content

    def test_accepts_mp3_wav_formats(self):
        """Should accept MP3 and WAV formats."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert '"mp3"' in content
        assert '"wav"' in content

    def test_custom_paths_stored_in_session(self):
        """Custom paths should be stored in session state."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'custom_intro_path' in content
        assert 'custom_outro_path' in content

    def test_custom_paths_used_in_tts(self):
        """Custom intro/outro paths should be used when generating audio."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert "intro_path = session_state.get('custom_intro_path')" in content
        assert "outro_path = session_state.get('custom_outro_path')" in content

    def test_falls_back_to_defaults(self):
        """Should fall back to default intro/outro if not uploaded."""
        with open('webui.py', 'r') as f:
            content = f.read()
        # Check fallback pattern: custom_path or DEFAULT_PATH
        assert 'or INTRO_MUSIC_PATH' in content
        assert 'or OUTRO_MUSIC_PATH' in content


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
