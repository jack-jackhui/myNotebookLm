"""Session history management for MyNotebookLM.

Provides functionality to save, load, and manage generation history.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Default history storage path
HISTORY_DIR = Path("./data/history")
HISTORY_FILE = HISTORY_DIR / "sessions.json"


class SessionEntry:
    """Represents a single generation session."""

    def __init__(
        self,
        session_id: str,
        timestamp: str,
        input_source: str,
        input_type: str,
        episode_length: str,
        host_1_name: str,
        host_2_name: str,
        script_preview: str,
        audio_path: Optional[str] = None,
        script_path: Optional[str] = None,
        custom_intro: Optional[str] = None,
        custom_outro: Optional[str] = None,
    ):
        self.session_id = session_id
        self.timestamp = timestamp
        self.input_source = input_source
        self.input_type = input_type
        self.episode_length = episode_length
        self.host_1_name = host_1_name
        self.host_2_name = host_2_name
        self.script_preview = script_preview[:500] if script_preview else ""
        self.audio_path = audio_path
        self.script_path = script_path
        self.custom_intro = custom_intro
        self.custom_outro = custom_outro

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "input_source": self.input_source,
            "input_type": self.input_type,
            "episode_length": self.episode_length,
            "host_1_name": self.host_1_name,
            "host_2_name": self.host_2_name,
            "script_preview": self.script_preview,
            "audio_path": self.audio_path,
            "script_path": self.script_path,
            "custom_intro": self.custom_intro,
            "custom_outro": self.custom_outro,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionEntry":
        """Create SessionEntry from dictionary."""
        return cls(
            session_id=data.get("session_id", ""),
            timestamp=data.get("timestamp", ""),
            input_source=data.get("input_source", ""),
            input_type=data.get("input_type", ""),
            episode_length=data.get("episode_length", "Auto"),
            host_1_name=data.get("host_1_name", "Jack"),
            host_2_name=data.get("host_2_name", "Corr"),
            script_preview=data.get("script_preview", ""),
            audio_path=data.get("audio_path"),
            script_path=data.get("script_path"),
            custom_intro=data.get("custom_intro"),
            custom_outro=data.get("custom_outro"),
        )

    @property
    def display_name(self) -> str:
        """Get a display-friendly name for the session."""
        dt = datetime.fromisoformat(self.timestamp)
        date_str = dt.strftime("%Y-%m-%d %H:%M")
        preview = self.script_preview[:50] + "..." if len(self.script_preview) > 50 else self.script_preview
        return f"{date_str} - {preview}"


class HistoryManager:
    """Manages session history storage and retrieval."""

    def __init__(self, history_file: Path = HISTORY_FILE):
        self.history_file = history_file
        self._ensure_dir()

    def _ensure_dir(self):
        """Ensure history directory exists."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_all(self) -> List[Dict[str, Any]]:
        """Load all sessions from file."""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load history: {e}")
            return []

    def _save_all(self, sessions: List[Dict[str, Any]]):
        """Save all sessions to file."""
        self._ensure_dir()
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2)

    def save_session(self, entry: SessionEntry):
        """Save a new session entry."""
        sessions = self._load_all()
        sessions.insert(0, entry.to_dict())  # Newest first
        # Keep only last 50 sessions
        sessions = sessions[:50]
        self._save_all(sessions)
        logger.info(f"Saved session: {entry.session_id}")

    def get_sessions(self, limit: int = 20) -> List[SessionEntry]:
        """Get recent sessions."""
        sessions = self._load_all()
        return [SessionEntry.from_dict(s) for s in sessions[:limit]]

    def get_session(self, session_id: str) -> Optional[SessionEntry]:
        """Get a specific session by ID."""
        sessions = self._load_all()
        for s in sessions:
            if s.get("session_id") == session_id:
                return SessionEntry.from_dict(s)
        return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        sessions = self._load_all()
        original_len = len(sessions)
        sessions = [s for s in sessions if s.get("session_id") != session_id]
        if len(sessions) < original_len:
            self._save_all(sessions)
            logger.info(f"Deleted session: {session_id}")
            return True
        return False

    def clear_all(self):
        """Clear all session history."""
        self._save_all([])
        logger.info("Cleared all session history")


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def create_session_entry(
    input_source: str,
    input_type: str,
    episode_length: str,
    host_1_name: str,
    host_2_name: str,
    script: str,
    audio_path: Optional[str] = None,
    script_path: Optional[str] = None,
    custom_intro: Optional[str] = None,
    custom_outro: Optional[str] = None,
) -> SessionEntry:
    """Helper function to create a session entry."""
    return SessionEntry(
        session_id=generate_session_id(),
        timestamp=datetime.now().isoformat(),
        input_source=input_source,
        input_type=input_type,
        episode_length=episode_length,
        host_1_name=host_1_name,
        host_2_name=host_2_name,
        script_preview=script,
        audio_path=audio_path,
        script_path=script_path,
        custom_intro=custom_intro,
        custom_outro=custom_outro,
    )


# Global instance for convenience
history_manager = HistoryManager()
