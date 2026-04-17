"""Tests for episode_memory module."""

import json
import os
import tempfile
import pytest
from datetime import datetime, timedelta

from episode_memory import (
    EpisodeMemoryManager,
    Prediction,
    EpisodeRecord,
    EpisodeMemory,
    get_memory_manager
)


@pytest.fixture
def temp_memory_file():
    """Create a temporary memory file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{}')
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def memory_manager(temp_memory_file):
    """Create a memory manager with a temporary file."""
    return EpisodeMemoryManager(memory_path=temp_memory_file)


class TestPrediction:
    """Tests for Prediction dataclass."""

    def test_prediction_creation(self):
        pred = Prediction(
            text="Bitcoin will hit $100k",
            episode_date="2024-01-15",
            topic="crypto"
        )
        assert pred.text == "Bitcoin will hit $100k"
        assert pred.resolved is False
        assert pred.confidence == "medium"


class TestEpisodeMemoryManager:
    """Tests for EpisodeMemoryManager."""

    def test_init_creates_empty_memory(self, memory_manager):
        assert memory_manager.memory.predictions == []
        assert memory_manager.memory.episodes == []

    def test_add_prediction(self, memory_manager):
        memory_manager.add_prediction(
            text="AI will replace 50% of coding jobs",
            topic="ai_revolution",
            confidence="high"
        )
        assert len(memory_manager.memory.predictions) == 1
        pred = memory_manager.memory.predictions[0]
        assert pred['text'] == "AI will replace 50% of coding jobs"
        assert pred['confidence'] == "high"

    def test_get_unresolved_predictions(self, memory_manager):
        memory_manager.add_prediction("Prediction 1", "topic1")
        memory_manager.add_prediction("Prediction 2", "topic2")

        unresolved = memory_manager.get_unresolved_predictions()
        assert len(unresolved) == 2

    def test_resolve_prediction(self, memory_manager):
        memory_manager.add_prediction("Test prediction", "test_topic")

        result = memory_manager.resolve_prediction(
            prediction_text="Test prediction",
            outcome="correct",
            notes="This came true!"
        )
        assert result is True

        pred = memory_manager.memory.predictions[0]
        assert pred['resolved'] is True
        assert pred['outcome'] == "correct"

    def test_record_episode(self, memory_manager):
        memory_manager.record_episode(
            main_theme="The AI Revolution",
            topics_covered=["OpenAI GPT-5", "Claude 4"],
            predictions_made=["GPT-5 will dominate"],
            key_stories=["OpenAI announces GPT-5"],
            callbacks_used=[]
        )

        assert len(memory_manager.memory.episodes) == 1
        ep = memory_manager.memory.episodes[0]
        assert ep['main_theme'] == "The AI Revolution"
        assert len(ep['topics_covered']) == 2

    def test_get_recent_episodes(self, memory_manager):
        for i in range(7):
            memory_manager.record_episode(
                main_theme=f"Theme {i}",
                topics_covered=[f"Topic {i}"],
                predictions_made=[],
                key_stories=[]
            )

        recent = memory_manager.get_recent_episodes(count=5)
        assert len(recent) == 5
        assert recent[-1]['main_theme'] == "Theme 6"

    def test_get_callbacks_for_stories(self, memory_manager):
        # Add a prediction about Bitcoin
        memory_manager.add_prediction(
            text="Bitcoin will reach new highs this quarter",
            topic="crypto"
        )

        # Current stories that match
        stories = [{
            'title': 'Bitcoin Reaches Record Highs',
            'content': 'Bitcoin surged to new record highs this quarter, exceeding expectations.'
        }]

        callbacks = memory_manager.get_callbacks_for_stories(stories)
        assert len(callbacks) == 1
        assert 'Bitcoin' in callbacks[0]['prediction']

    def test_format_callbacks_for_prompt(self, memory_manager):
        callbacks = [{
            'prediction': 'AI will dominate the market',
            'episode_date': '2024-01-01',
            'related_story': 'AI Companies See Record Growth',
            'match_strength': 3
        }]

        formatted = memory_manager.format_callbacks_for_prompt(callbacks)
        assert 'CALLBACKS FROM PAST EPISODES' in formatted
        assert '2024-01-01' in formatted

    def test_empty_callbacks_format(self, memory_manager):
        formatted = memory_manager.format_callbacks_for_prompt([])
        assert formatted == ""

    def test_topic_frequency(self, memory_manager):
        memory_manager.record_episode(
            main_theme="AI",
            topics_covered=["AI News", "Tech"],
            predictions_made=[],
            key_stories=[]
        )
        memory_manager.record_episode(
            main_theme="AI",
            topics_covered=["AI News", "Crypto"],
            predictions_made=[],
            key_stories=[]
        )

        assert memory_manager.get_topic_frequency("AI News") == 2
        assert memory_manager.get_topic_frequency("Tech") == 1
        assert memory_manager.get_topic_frequency("Unknown") == 0

    def test_persistence(self, temp_memory_file):
        # Create and populate memory
        manager1 = EpisodeMemoryManager(memory_path=temp_memory_file)
        manager1.add_prediction("Test prediction", "test")
        manager1.record_episode(
            main_theme="Test Theme",
            topics_covered=["Topic 1"],
            predictions_made=["Pred 1"],
            key_stories=["Story 1"]
        )

        # Create new manager with same file
        manager2 = EpisodeMemoryManager(memory_path=temp_memory_file)

        # Verify data persisted
        assert len(manager2.memory.predictions) >= 1
        assert len(manager2.memory.episodes) == 1

    def test_host_memory_context(self, memory_manager):
        memory_manager.record_episode(
            main_theme="AI Revolution",
            topics_covered=["GPT-5", "Claude"],
            predictions_made=["AI will transform coding"],
            key_stories=["OpenAI releases GPT-5"]
        )

        context = memory_manager.get_host_memory_context()
        assert "EPISODE HISTORY" in context
        assert "AI Revolution" in context
