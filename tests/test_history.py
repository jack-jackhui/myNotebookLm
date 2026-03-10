"""Tests for session history module."""

import pytest
import json
import tempfile
from pathlib import Path


class TestHistoryModule:
    """Tests for history module structure."""

    def test_history_module_exists(self):
        """history.py should exist."""
        assert Path('history.py').exists()

    def test_session_entry_class(self):
        """SessionEntry class should exist."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'class SessionEntry:' in content

    def test_history_manager_class(self):
        """HistoryManager class should exist."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'class HistoryManager:' in content

    def test_save_session_method(self):
        """HistoryManager should have save_session method."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'def save_session' in content

    def test_get_sessions_method(self):
        """HistoryManager should have get_sessions method."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'def get_sessions' in content

    def test_get_session_method(self):
        """HistoryManager should have get_session method."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'def get_session' in content

    def test_delete_session_method(self):
        """HistoryManager should have delete_session method."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'def delete_session' in content


class TestSessionEntryFields:
    """Tests for SessionEntry fields."""

    def test_has_session_id(self):
        """SessionEntry should have session_id field."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'session_id' in content

    def test_has_timestamp(self):
        """SessionEntry should have timestamp field."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'timestamp' in content

    def test_has_input_source(self):
        """SessionEntry should have input_source field."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'input_source' in content

    def test_has_episode_length(self):
        """SessionEntry should have episode_length field."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'episode_length' in content

    def test_has_host_names(self):
        """SessionEntry should have host name fields."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'host_1_name' in content
        assert 'host_2_name' in content

    def test_has_script_preview(self):
        """SessionEntry should have script_preview field."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'script_preview' in content

    def test_has_to_dict_method(self):
        """SessionEntry should have to_dict method for JSON serialization."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'def to_dict' in content

    def test_has_from_dict_method(self):
        """SessionEntry should have from_dict class method."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'def from_dict' in content


class TestHistoryIntegration:
    """Tests for history integration in webui."""

    def test_webui_imports_history(self):
        """WebUI should import history module."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'from history import' in content

    def test_webui_has_history_section(self):
        """WebUI should have session history section in sidebar."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'Session History' in content

    def test_webui_displays_sessions(self):
        """WebUI should display previous sessions."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'get_sessions' in content
        assert 'Previous Sessions' in content

    def test_webui_saves_sessions(self):
        """WebUI should save sessions after audio generation."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'save_session' in content
        assert 'create_session_entry' in content

    def test_webui_allows_loading_settings(self):
        """WebUI should allow loading settings from history."""
        with open('webui.py', 'r') as f:
            content = f.read()
        assert 'Load Settings' in content


class TestHistoryStorage:
    """Tests for history storage format."""

    def test_uses_json_storage(self):
        """History should use JSON for storage."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'json.load' in content
        assert 'json.dump' in content

    def test_has_history_file_path(self):
        """Should have configurable history file path."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'HISTORY_FILE' in content

    def test_has_helper_function(self):
        """Should have create_session_entry helper function."""
        with open('history.py', 'r') as f:
            content = f.read()
        assert 'def create_session_entry' in content
