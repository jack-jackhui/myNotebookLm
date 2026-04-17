"""Episode memory for tracking past episodes, predictions, and callbacks.

Provides continuity between episodes by storing:
- Past predictions and whether they came true
- Key topics covered to avoid repetition
- Running storylines to follow up on
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# Default memory file location
DEFAULT_MEMORY_PATH = "./data/episode_memory.json"


@dataclass
class Prediction:
    """A prediction made during an episode."""
    text: str
    episode_date: str
    topic: str
    confidence: str = "medium"  # low, medium, high
    resolved: bool = False
    outcome: Optional[str] = None  # "correct", "incorrect", "partially_correct"
    resolution_date: Optional[str] = None
    resolution_notes: Optional[str] = None


@dataclass
class EpisodeRecord:
    """Record of a past episode."""
    date: str
    main_theme: str
    topics_covered: List[str] = field(default_factory=list)
    predictions_made: List[Dict[str, Any]] = field(default_factory=list)
    key_stories: List[str] = field(default_factory=list)
    callbacks_used: List[str] = field(default_factory=list)


@dataclass
class EpisodeMemory:
    """Persistent memory across episodes."""
    predictions: List[Dict[str, Any]] = field(default_factory=list)
    episodes: List[Dict[str, Any]] = field(default_factory=list)
    recurring_topics: Dict[str, int] = field(default_factory=dict)  # topic -> count
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class EpisodeMemoryManager:
    """Manages episode memory persistence and retrieval."""

    def __init__(self, memory_path: str = DEFAULT_MEMORY_PATH):
        self.memory_path = memory_path
        self._ensure_directory()
        self.memory = self._load_memory()

    def _ensure_directory(self) -> None:
        """Ensure the memory directory exists."""
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)

    def _load_memory(self) -> EpisodeMemory:
        """Load memory from disk."""
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return EpisodeMemory(
                    predictions=data.get('predictions', []),
                    episodes=data.get('episodes', []),
                    recurring_topics=data.get('recurring_topics', {}),
                    last_updated=data.get('last_updated', datetime.now().isoformat())
                )
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load memory file: {e}. Starting fresh.")
        return EpisodeMemory()

    def _save_memory(self) -> None:
        """Save memory to disk."""
        self.memory.last_updated = datetime.now().isoformat()
        with open(self.memory_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.memory), f, indent=2, default=str)

    def add_prediction(
        self,
        text: str,
        topic: str,
        confidence: str = "medium"
    ) -> None:
        """Add a new prediction."""
        prediction = Prediction(
            text=text,
            episode_date=datetime.now().strftime("%Y-%m-%d"),
            topic=topic,
            confidence=confidence
        )
        self.memory.predictions.append(asdict(prediction))
        self._save_memory()
        logger.info(f"Added prediction: {text[:50]}...")

    def get_unresolved_predictions(
        self,
        max_age_days: int = 90
    ) -> List[Dict[str, Any]]:
        """Get predictions that haven't been resolved yet."""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        unresolved = []
        for pred in self.memory.predictions:
            if pred.get('resolved'):
                continue
            try:
                pred_date = datetime.strptime(pred['episode_date'], "%Y-%m-%d")
                if pred_date > cutoff:
                    unresolved.append(pred)
            except (ValueError, KeyError):
                continue
        return unresolved

    def resolve_prediction(
        self,
        prediction_text: str,
        outcome: str,
        notes: Optional[str] = None
    ) -> bool:
        """Mark a prediction as resolved."""
        for pred in self.memory.predictions:
            if pred['text'] == prediction_text:
                pred['resolved'] = True
                pred['outcome'] = outcome
                pred['resolution_date'] = datetime.now().strftime("%Y-%m-%d")
                pred['resolution_notes'] = notes
                self._save_memory()
                logger.info(f"Resolved prediction: {outcome}")
                return True
        return False

    def record_episode(
        self,
        main_theme: str,
        topics_covered: List[str],
        predictions_made: List[str],
        key_stories: List[str],
        callbacks_used: List[str] = None
    ) -> None:
        """Record a new episode."""
        episode = EpisodeRecord(
            date=datetime.now().strftime("%Y-%m-%d"),
            main_theme=main_theme,
            topics_covered=topics_covered,
            predictions_made=[{"text": p} for p in predictions_made],
            key_stories=key_stories,
            callbacks_used=callbacks_used or []
        )
        self.memory.episodes.append(asdict(episode))

        # Update recurring topics count
        for topic in topics_covered:
            self.memory.recurring_topics[topic] = \
                self.memory.recurring_topics.get(topic, 0) + 1

        # Add predictions to tracking
        for pred_text in predictions_made:
            self.add_prediction(pred_text, main_theme)

        self._save_memory()
        logger.info(f"Recorded episode with theme: {main_theme}")

    def get_recent_episodes(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent episodes."""
        return self.memory.episodes[-count:]

    def get_topic_frequency(self, topic: str) -> int:
        """Get how many times a topic has been covered."""
        return self.memory.recurring_topics.get(topic, 0)

    def get_callbacks_for_stories(
        self,
        current_stories: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Find potential callbacks from past predictions to current stories."""
        callbacks = []
        unresolved = self.get_unresolved_predictions()

        for pred in unresolved:
            pred_text = pred.get('text', '').lower()
            pred_keywords = [w for w in pred_text.split() if len(w) > 4]

            for story in current_stories:
                story_text = f"{story.get('title', '')} {story.get('content', '')}".lower()
                matches = sum(1 for kw in pred_keywords if kw in story_text)

                if matches >= 2:
                    callbacks.append({
                        "prediction": pred.get('text', ''),
                        "episode_date": pred.get('episode_date', 'a previous episode'),
                        "related_story": story.get('title', ''),
                        "match_strength": matches
                    })
                    break

        # Sort by match strength and return top 3
        callbacks.sort(key=lambda x: x['match_strength'], reverse=True)
        return callbacks[:3]

    def format_callbacks_for_prompt(
        self,
        callbacks: List[Dict[str, str]]
    ) -> str:
        """Format callbacks for inclusion in generation prompt."""
        if not callbacks:
            return ""

        lines = ["CALLBACKS FROM PAST EPISODES (Reference these for continuity):"]
        for cb in callbacks:
            lines.append(
                f"- In {cb['episode_date']}, we predicted: \"{cb['prediction'][:100]}...\" "
                f"Today's story \"{cb['related_story'][:50]}...\" relates to this!"
            )
        lines.append("")
        return "\n".join(lines)

    def get_host_memory_context(self) -> str:
        """Get context about past episodes for host dialogue."""
        recent = self.get_recent_episodes(3)
        if not recent:
            return ""

        lines = ["EPISODE HISTORY (for natural references):"]
        for ep in recent:
            lines.append(f"- {ep['date']}: Covered {ep['main_theme']}")
            if ep.get('predictions_made'):
                pred_texts = [p.get('text', '')[:50] for p in ep['predictions_made'][:2]]
                lines.append(f"  Predictions: {', '.join(pred_texts)}...")

        # Add running scores
        unresolved = self.get_unresolved_predictions()
        resolved_correct = sum(
            1 for p in self.memory.predictions
            if p.get('resolved') and p.get('outcome') == 'correct'
        )
        resolved_total = sum(1 for p in self.memory.predictions if p.get('resolved'))

        if resolved_total > 0:
            lines.append(f"\nPREDICTION TRACK RECORD: {resolved_correct}/{resolved_total} correct")
        if unresolved:
            lines.append(f"PENDING PREDICTIONS: {len(unresolved)} still waiting to be verified")

        return "\n".join(lines)


# Singleton instance for easy access
_memory_manager: Optional[EpisodeMemoryManager] = None


def get_memory_manager(memory_path: str = DEFAULT_MEMORY_PATH) -> EpisodeMemoryManager:
    """Get or create the memory manager singleton."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = EpisodeMemoryManager(memory_path)
    return _memory_manager
