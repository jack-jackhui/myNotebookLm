"""Story arc and theme identification for podcast episodes.

Identifies unifying themes across news stories and structures episodes
around narrative arcs rather than simple category dumps.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class StoryTheme:
    """Represents a unifying theme across multiple stories."""
    name: str
    description: str
    stories: List[Dict[str, Any]] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    narrative_hook: str = ""
    tension_points: List[str] = field(default_factory=list)

    @property
    def story_count(self) -> int:
        return len(self.stories)

    def add_story(self, story: Dict[str, Any]) -> None:
        self.stories.append(story)


@dataclass
class EpisodeArc:
    """Structured narrative arc for an episode."""
    main_theme: StoryTheme
    supporting_themes: List[StoryTheme] = field(default_factory=list)
    opening_hook: str = ""
    callbacks: List[str] = field(default_factory=list)  # References to past episodes
    predictions: List[str] = field(default_factory=list)  # New predictions to make

    def get_all_stories(self) -> List[Dict[str, Any]]:
        """Get all stories in narrative order."""
        stories = list(self.main_theme.stories)
        for theme in self.supporting_themes:
            stories.extend(theme.stories)
        return stories


# Theme keywords for categorization
THEME_KEYWORDS = {
    "ai_revolution": {
        "keywords": ["artificial intelligence", "ai", "machine learning", "llm", "chatgpt",
                     "gpt", "claude", "gemini", "neural", "deep learning", "openai", "anthropic"],
        "name": "The AI Revolution",
        "description": "How artificial intelligence is reshaping our world"
    },
    "crypto_finance": {
        "keywords": ["bitcoin", "ethereum", "crypto", "blockchain", "defi", "nft",
                     "stablecoin", "web3", "token", "mining", "wallet"],
        "name": "Crypto & Digital Finance",
        "description": "The evolving landscape of digital currencies and decentralized finance"
    },
    "tech_giants": {
        "keywords": ["apple", "google", "microsoft", "meta", "amazon", "tesla",
                     "nvidia", "earnings", "stock", "market cap", "antitrust"],
        "name": "Big Tech Moves",
        "description": "Major developments from technology giants"
    },
    "regulation": {
        "keywords": ["regulation", "sec", "fda", "eu", "ban", "lawsuit", "legal",
                     "compliance", "policy", "government", "law"],
        "name": "The Regulatory Landscape",
        "description": "How governments are responding to technology"
    },
    "privacy_security": {
        "keywords": ["privacy", "security", "hack", "breach", "data", "surveillance",
                     "encryption", "cybersecurity", "ransomware", "leak"],
        "name": "Privacy & Security",
        "description": "The ongoing battle for digital privacy and security"
    },
    "future_tech": {
        "keywords": ["quantum", "robotics", "autonomous", "space", "fusion", "biotech",
                     "ar", "vr", "metaverse", "self-driving"],
        "name": "The Future is Now",
        "description": "Emerging technologies that could change everything"
    },
    "startup_ecosystem": {
        "keywords": ["startup", "funding", "venture", "series a", "series b", "ipo",
                     "acquisition", "unicorn", "valuation", "layoffs"],
        "name": "Startup Scene",
        "description": "The pulse of the startup ecosystem"
    },
}


def identify_theme(story: Dict[str, Any]) -> Optional[str]:
    """Identify the primary theme of a story based on keywords."""
    text = f"{story.get('title', '')} {story.get('content', '')}".lower()

    theme_scores = {}
    for theme_id, theme_data in THEME_KEYWORDS.items():
        score = sum(1 for kw in theme_data["keywords"] if kw in text)
        if score > 0:
            theme_scores[theme_id] = score

    if not theme_scores:
        return None

    return max(theme_scores, key=theme_scores.get)


def extract_tension_points(stories: List[Dict[str, Any]]) -> List[str]:
    """Extract potential points of debate/tension from stories."""
    tension_keywords = {
        "controversy": ["controversial", "debate", "critics", "backlash", "concern"],
        "competition": ["versus", "competitor", "rival", "battle", "fight"],
        "risk": ["risk", "danger", "warning", "threat", "fear"],
        "opportunity": ["opportunity", "potential", "promise", "breakthrough"],
        "uncertainty": ["uncertain", "unclear", "question", "doubt", "skeptic"],
    }

    tensions = []
    for story in stories:
        text = f"{story.get('title', '')} {story.get('content', '')}".lower()
        for tension_type, keywords in tension_keywords.items():
            if any(kw in text for kw in keywords):
                tensions.append(f"{tension_type}: {story.get('title', 'Unknown')}")
                break

    return tensions[:5]  # Limit to top 5 tension points


def generate_narrative_hook(theme: StoryTheme) -> str:
    """Generate an engaging opening hook for a theme."""
    story_count = theme.story_count

    hooks = {
        "ai_revolution": [
            f"This week, AI made {story_count} major headlines - and they're all connected.",
            "The machines are learning faster than ever, and we've got the stories to prove it.",
            "AI is moving so fast, even AI can't keep up. Here's what you need to know.",
        ],
        "crypto_finance": [
            f"The crypto world never sleeps, and neither do we. {story_count} stories you can't miss.",
            "From Bitcoin to DeFi, the financial revolution continues.",
            "Digital money, real consequences. Let's break it down.",
        ],
        "tech_giants": [
            "Big Tech is making big moves this week. Here's the inside scoop.",
            f"When giants move, the earth shakes. {story_count} stories from the top.",
            "The titans of tech are at it again. Let's see who's winning.",
        ],
        "regulation": [
            "The regulators are circling, and tech is in the crosshairs.",
            "Laws are changing faster than code these days. Here's what matters.",
            "The government wants a word with Silicon Valley.",
        ],
        "privacy_security": [
            "Your data is under attack - and so is everyone else's.",
            "In the digital age, privacy is a luxury. Here's the latest.",
            "Hackers never rest, and neither does our coverage.",
        ],
        "future_tech": [
            "The future isn't coming - it's already here. Let's explore.",
            f"From sci-fi to reality: {story_count} stories that sound made up, but aren't.",
            "Buckle up. The tech of tomorrow is being built today.",
        ],
        "startup_ecosystem": [
            "Another week, another billion raised. Let's see who's hot.",
            "The startup grind never stops. Here's who's making moves.",
            "VCs are writing checks, founders are making pitches. What's new?",
        ],
    }

    theme_id = None
    for tid, tdata in THEME_KEYWORDS.items():
        if tdata["name"] == theme.name:
            theme_id = tid
            break

    if theme_id and theme_id in hooks:
        import random
        return random.choice(hooks[theme_id])

    return f"We've got {story_count} important stories to cover today. Let's dive in."


def group_stories_by_theme(stories: List[Dict[str, Any]]) -> Dict[str, StoryTheme]:
    """Group stories by their identified themes."""
    themes: Dict[str, StoryTheme] = {}

    for story in stories:
        theme_id = identify_theme(story)
        if not theme_id:
            theme_id = "general"

        if theme_id not in themes:
            theme_data = THEME_KEYWORDS.get(theme_id, {
                "name": "General Tech News",
                "description": "Important technology developments"
            })
            themes[theme_id] = StoryTheme(
                name=theme_data.get("name", "General"),
                description=theme_data.get("description", ""),
                keywords=theme_data.get("keywords", [])
            )

        themes[theme_id].add_story(story)

    return themes


def create_episode_arc(
    stories: List[Dict[str, Any]],
    past_predictions: Optional[List[Dict[str, Any]]] = None,
    max_themes: int = 3
) -> EpisodeArc:
    """Create a structured narrative arc from stories.

    Args:
        stories: List of news stories to structure
        past_predictions: Previous predictions to check against current news
        max_themes: Maximum number of themes to include

    Returns:
        EpisodeArc with structured narrative flow
    """
    if not stories:
        return EpisodeArc(
            main_theme=StoryTheme(name="No News", description="Nothing to report"),
            opening_hook="It's been a quiet week in tech..."
        )

    # Group stories by theme
    themes = group_stories_by_theme(stories)

    # Sort themes by story count (most stories = main theme)
    sorted_themes = sorted(themes.values(), key=lambda t: t.story_count, reverse=True)

    # Select main theme and supporting themes
    main_theme = sorted_themes[0]
    supporting_themes = sorted_themes[1:max_themes] if len(sorted_themes) > 1 else []

    # Extract tension points for debate
    all_stories = main_theme.stories + [s for t in supporting_themes for s in t.stories]
    main_theme.tension_points = extract_tension_points(all_stories)

    # Generate narrative hook
    main_theme.narrative_hook = generate_narrative_hook(main_theme)

    # Check past predictions against current stories
    callbacks = []
    if past_predictions:
        callbacks = check_predictions_against_stories(past_predictions, stories)

    # Generate new predictions based on current stories
    predictions = generate_predictions(all_stories)

    return EpisodeArc(
        main_theme=main_theme,
        supporting_themes=supporting_themes,
        opening_hook=main_theme.narrative_hook,
        callbacks=callbacks,
        predictions=predictions
    )


def check_predictions_against_stories(
    predictions: List[Dict[str, Any]],
    stories: List[Dict[str, Any]]
) -> List[str]:
    """Check if any past predictions came true in current stories."""
    callbacks = []

    for pred in predictions:
        pred_text = pred.get("prediction", "").lower()
        pred_keywords = [w for w in pred_text.split() if len(w) > 4]

        for story in stories:
            story_text = f"{story.get('title', '')} {story.get('content', '')}".lower()
            matches = sum(1 for kw in pred_keywords if kw in story_text)

            if matches >= 2:  # At least 2 keyword matches
                episode_ref = pred.get("episode_date", "a previous episode")
                callbacks.append(
                    f"Remember when we predicted '{pred.get('prediction', '')[:100]}...'? "
                    f"Well, look at this: {story.get('title', '')}"
                )
                break

    return callbacks[:3]  # Limit to 3 callbacks per episode


def generate_predictions(stories: List[Dict[str, Any]]) -> List[str]:
    """Generate predictions based on current story trends."""
    predictions = []

    # Look for trend indicators
    trend_indicators = {
        "growth": ["growing", "increasing", "surge", "boom", "expansion"],
        "decline": ["falling", "decreasing", "decline", "crash", "downturn"],
        "new_tech": ["announced", "launched", "unveiled", "introduced", "released"],
        "acquisition": ["acquire", "merger", "buyout", "deal", "partnership"],
    }

    for story in stories[:5]:  # Top 5 stories
        text = f"{story.get('title', '')} {story.get('content', '')}".lower()
        title = story.get('title', 'This development')

        for trend, keywords in trend_indicators.items():
            if any(kw in text for kw in keywords):
                if trend == "growth":
                    predictions.append(f"Based on '{title[:50]}...', we predict this trend will continue and possibly accelerate in the coming months.")
                elif trend == "decline":
                    predictions.append(f"Given '{title[:50]}...', we might see a market correction or significant changes ahead.")
                elif trend == "new_tech":
                    predictions.append(f"'{title[:50]}...' could be the start of something big. Watch this space.")
                elif trend == "acquisition":
                    predictions.append(f"The moves described in '{title[:50]}...' suggest we'll see more consolidation in this sector.")
                break

    return predictions[:3]  # Limit to 3 predictions per episode


def format_arc_for_prompt(arc: EpisodeArc) -> str:
    """Format episode arc into a prompt-friendly structure."""
    sections = []

    # Opening hook
    sections.append(f"EPISODE HOOK:\n{arc.opening_hook}\n")

    # Callbacks from past episodes
    if arc.callbacks:
        sections.append("CALLBACKS (Reference these from past episodes):")
        for callback in arc.callbacks:
            sections.append(f"- {callback}")
        sections.append("")

    # Main theme
    sections.append(f"MAIN THEME: {arc.main_theme.name}")
    sections.append(f"Theme description: {arc.main_theme.description}")
    sections.append(f"Number of related stories: {arc.main_theme.story_count}")
    if arc.main_theme.tension_points:
        sections.append("Debate points (hosts should disagree on these):")
        for point in arc.main_theme.tension_points:
            sections.append(f"  - {point}")
    sections.append("\nSTORIES FOR MAIN THEME:")
    for i, story in enumerate(arc.main_theme.stories, 1):
        sections.append(f"\n{i}. {story.get('title', 'Untitled')}")
        sections.append(f"   Source: {story.get('link', 'Unknown')}")
        content = story.get('content', '')[:500]
        sections.append(f"   Summary: {content}...")
    sections.append("")

    # Supporting themes
    if arc.supporting_themes:
        sections.append("SUPPORTING THEMES:")
        for theme in arc.supporting_themes:
            sections.append(f"\n  {theme.name} ({theme.story_count} stories)")
            for story in theme.stories[:2]:  # Limit to 2 stories per supporting theme
                sections.append(f"    - {story.get('title', 'Untitled')}")
    sections.append("")

    # Predictions for this episode
    if arc.predictions:
        sections.append("PREDICTIONS TO MAKE (hosts should discuss and debate these):")
        for pred in arc.predictions:
            sections.append(f"- {pred}")

    return "\n".join(sections)
