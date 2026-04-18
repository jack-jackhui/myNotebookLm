"""Topic curation and story ranking for podcast episodes.

Ranks stories by significance, combines similar stories from multiple sources,
and selects only the top 3-4 stories for in-depth coverage.
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class CuratedStory:
    """A curated story with metadata and combined sources."""
    title: str
    content: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    significance_score: float = 0.0
    key_facts: List[str] = field(default_factory=list)
    key_quotes: List[str] = field(default_factory=list)
    combined_at: datetime = field(default_factory=datetime.now)

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def primary_source(self) -> Optional[Dict[str, Any]]:
        return self.sources[0] if self.sources else None

    def add_source(self, source: Dict[str, Any]) -> None:
        self.sources.append(source)

    def get_all_links(self) -> List[str]:
        return [s.get('link', '') for s in self.sources if s.get('link')]


# Significance scoring weights
SIGNIFICANCE_WEIGHTS = {
    "multiple_sources": 3.0,      # Story covered by multiple sources
    "recency": 2.0,               # More recent = more significant
    "breaking_news": 2.5,         # Contains breaking/exclusive keywords
    "major_company": 2.0,         # Involves major tech companies
    "financial_impact": 1.5,      # Has financial numbers/impact
    "regulatory": 1.5,            # Regulatory/legal significance
    "content_depth": 1.0,         # Longer, more detailed content
}

# Keywords that indicate breaking/significant news
BREAKING_KEYWORDS = [
    "breaking", "exclusive", "just announced", "breaking news",
    "first look", "leaked", "revealed", "confirmed", "official"
]

# Major companies that increase significance
MAJOR_COMPANIES = [
    "apple", "google", "microsoft", "amazon", "meta", "nvidia",
    "openai", "anthropic", "tesla", "samsung", "intel", "amd",
    "coinbase", "binance", "twitter", "x corp", "bytedance", "tiktok"
]


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using SequenceMatcher."""
    # Use first 500 chars for faster comparison
    t1 = text1[:500].lower()
    t2 = text2[:500].lower()
    return SequenceMatcher(None, t1, t2).ratio()


def extract_title_keywords(title: str) -> List[str]:
    """Extract significant keywords from a title."""
    # Remove common words
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                 "being", "have", "has", "had", "do", "does", "did", "will",
                 "would", "could", "should", "may", "might", "must", "shall",
                 "to", "of", "in", "for", "on", "with", "at", "by", "from",
                 "as", "into", "through", "during", "before", "after", "and",
                 "but", "or", "nor", "so", "yet", "both", "either", "neither"}

    words = re.findall(r'\b\w+\b', title.lower())
    return [w for w in words if w not in stopwords and len(w) > 2]


def stories_are_similar(story1: Dict[str, Any], story2: Dict[str, Any],
                       threshold: float = 0.4) -> bool:
    """Determine if two stories are about the same topic."""
    title1 = story1.get('title', '')
    title2 = story2.get('title', '')

    # Check title similarity
    title_sim = calculate_similarity(title1, title2)
    if title_sim > 0.6:
        return True

    # Check keyword overlap
    kw1 = set(extract_title_keywords(title1))
    kw2 = set(extract_title_keywords(title2))
    if kw1 and kw2:
        overlap = len(kw1 & kw2) / max(len(kw1), len(kw2))
        if overlap > 0.5:
            return True

    # Check content similarity (sample)
    content1 = story1.get('content', '')
    content2 = story2.get('content', '')
    if content1 and content2:
        content_sim = calculate_similarity(content1, content2)
        if content_sim > threshold:
            return True

    return False


def extract_key_facts(content: str) -> List[str]:
    """Extract key facts from article content."""
    facts = []

    # Look for sentences with numbers (often factual)
    sentences = re.split(r'[.!?]', content)
    for sentence in sentences:
        sentence = sentence.strip()
        # Contains numbers (financial figures, percentages, etc.)
        if re.search(r'\$[\d,]+|\d+%|\d+\s*(million|billion|trillion)', sentence, re.I):
            if 20 < len(sentence) < 200:
                facts.append(sentence)
        # Contains key fact indicators
        elif any(kw in sentence.lower() for kw in ["announced", "reported", "confirmed", "revealed"]):
            if 20 < len(sentence) < 200:
                facts.append(sentence)

    return facts[:5]  # Return top 5 facts


def extract_key_quotes(content: str) -> List[str]:
    """Extract notable quotes from article content."""
    quotes = []

    # Look for quoted text
    quote_patterns = [
        r'"([^"]{30,200})"',  # Double quotes
        r"'([^']{30,200})'",  # Single quotes (be careful with contractions)
        r'"([^"]{30,200})"',  # Smart quotes
    ]

    for pattern in quote_patterns:
        matches = re.findall(pattern, content)
        quotes.extend(matches)

    # Deduplicate and limit
    seen = set()
    unique_quotes = []
    for q in quotes:
        q_lower = q.lower()
        if q_lower not in seen:
            seen.add(q_lower)
            unique_quotes.append(q)

    return unique_quotes[:3]  # Return top 3 quotes


def calculate_significance_score(story: Dict[str, Any], source_count: int = 1) -> float:
    """Calculate significance score for a story."""
    score = 0.0
    title = story.get('title', '').lower()
    content = story.get('content', '').lower()
    text = f"{title} {content}"

    # Multiple sources covering the same story
    if source_count > 1:
        score += SIGNIFICANCE_WEIGHTS["multiple_sources"] * min(source_count, 5)

    # Recency (if published date available)
    published = story.get('published')
    if published:
        if isinstance(published, datetime):
            hours_old = (datetime.now() - published).total_seconds() / 3600
            if hours_old < 6:
                score += SIGNIFICANCE_WEIGHTS["recency"] * 2
            elif hours_old < 24:
                score += SIGNIFICANCE_WEIGHTS["recency"]

    # Breaking news keywords
    if any(kw in text for kw in BREAKING_KEYWORDS):
        score += SIGNIFICANCE_WEIGHTS["breaking_news"]

    # Major company involvement
    company_count = sum(1 for company in MAJOR_COMPANIES if company in text)
    score += SIGNIFICANCE_WEIGHTS["major_company"] * min(company_count, 3)

    # Financial impact (contains dollar amounts, percentages)
    if re.search(r'\$[\d,]+\s*(million|billion|trillion)?', text):
        score += SIGNIFICANCE_WEIGHTS["financial_impact"]
    if re.search(r'\d+%', text):
        score += SIGNIFICANCE_WEIGHTS["financial_impact"] * 0.5

    # Regulatory significance
    if any(kw in text for kw in ["sec", "regulation", "lawsuit", "ban", "antitrust", "investigation"]):
        score += SIGNIFICANCE_WEIGHTS["regulatory"]

    # Content depth
    content_length = len(content)
    if content_length > 2000:
        score += SIGNIFICANCE_WEIGHTS["content_depth"] * 2
    elif content_length > 1000:
        score += SIGNIFICANCE_WEIGHTS["content_depth"]

    return score


def combine_similar_stories(stories: List[Dict[str, Any]]) -> List[CuratedStory]:
    """Combine similar stories from multiple sources into single curated stories."""
    if not stories:
        return []

    curated: List[CuratedStory] = []
    used_indices = set()

    for i, story in enumerate(stories):
        if i in used_indices:
            continue

        # Find all similar stories
        similar_stories = [story]
        used_indices.add(i)

        for j, other_story in enumerate(stories):
            if j in used_indices:
                continue
            if stories_are_similar(story, other_story):
                similar_stories.append(other_story)
                used_indices.add(j)

        # Create curated story from similar stories
        # Use the longest content as primary
        similar_stories.sort(key=lambda s: len(s.get('content', '')), reverse=True)
        primary = similar_stories[0]

        curated_story = CuratedStory(
            title=primary.get('title', 'Untitled'),
            content=primary.get('content', ''),
            sources=similar_stories
        )

        # Extract key facts and quotes from all sources
        all_content = " ".join(s.get('content', '') for s in similar_stories)
        curated_story.key_facts = extract_key_facts(all_content)
        curated_story.key_quotes = extract_key_quotes(all_content)

        # Calculate significance score
        curated_story.significance_score = calculate_significance_score(
            primary, source_count=len(similar_stories)
        )

        curated.append(curated_story)

    return curated


def rank_stories(curated_stories: List[CuratedStory]) -> List[CuratedStory]:
    """Rank curated stories by significance score."""
    return sorted(curated_stories, key=lambda s: s.significance_score, reverse=True)


def select_top_stories(
    stories: List[Dict[str, Any]],
    max_stories: int = 4,
    min_significance: float = 2.0
) -> List[CuratedStory]:
    """Select the top stories for an episode.

    Args:
        stories: Raw list of stories from news tracker
        max_stories: Maximum number of stories to select (default: 4)
        min_significance: Minimum significance score to include

    Returns:
        List of top curated stories, ranked by significance
    """
    if not stories:
        return []

    # Combine similar stories
    curated = combine_similar_stories(stories)
    logger.info(f"Combined {len(stories)} stories into {len(curated)} unique topics")

    # Rank by significance
    ranked = rank_stories(curated)

    # Filter by minimum significance (but always keep at least 1)
    filtered = [s for s in ranked if s.significance_score >= min_significance]
    if not filtered and ranked:
        filtered = [ranked[0]]

    # Select top stories
    selected = filtered[:max_stories]

    logger.info(f"Selected {len(selected)} top stories for episode")
    for i, story in enumerate(selected, 1):
        logger.info(f"  {i}. [{story.significance_score:.1f}] {story.title[:60]}...")

    return selected


def format_curated_stories_for_prompt(stories: List[CuratedStory]) -> str:
    """Format curated stories into a prompt-friendly structure."""
    sections = []

    sections.append(f"TODAY'S TOP {len(stories)} STORIES (In order of significance):\n")

    for i, story in enumerate(stories, 1):
        sections.append(f"{'='*60}")
        sections.append(f"STORY {i}: {story.title}")
        sections.append(f"Significance Score: {story.significance_score:.1f}")
        sections.append(f"Sources: {story.source_count} ({', '.join(story.get_all_links()[:3])})")

        sections.append(f"\nCONTENT:")
        sections.append(story.content[:1500] + "..." if len(story.content) > 1500 else story.content)

        if story.key_facts:
            sections.append(f"\nKEY FACTS (mention these):")
            for fact in story.key_facts:
                sections.append(f"  - {fact}")

        if story.key_quotes:
            sections.append(f"\nNOTABLE QUOTES (consider using):")
            for quote in story.key_quotes:
                sections.append(f'  "{quote}"')

        sections.append("")

    return "\n".join(sections)


def curated_to_dict(story: CuratedStory) -> Dict[str, Any]:
    """Convert CuratedStory to dictionary for compatibility with existing code."""
    return {
        'title': story.title,
        'content': story.content,
        'link': story.primary_source.get('link', '') if story.primary_source else '',
        'published': story.primary_source.get('published') if story.primary_source else None,
        'source_count': story.source_count,
        'significance_score': story.significance_score,
        'key_facts': story.key_facts,
        'key_quotes': story.key_quotes,
        'all_links': story.get_all_links(),
    }


def format_single_story_for_prompt(story: CuratedStory) -> str:
    """Format a single curated story for prompt inclusion."""
    # sources is a list of dicts with keys: source, title, link, etc.
    sources_lines = []
    for s in story.sources[:3]:
        src_name = s.get("source", "Unknown")
        src_title = s.get("title", "No title")
        sources_lines.append(f"  - {src_name}: {src_title}")
    sources_text = "\n".join(sources_lines) if sources_lines else "  (no sources)"
    
    key_facts = story.key_facts[:5] if story.key_facts else []
    facts_text = "\n".join([f"  - {fact}" for fact in key_facts]) if key_facts else "  (no key facts extracted)"
    
    content_preview = story.content[:2000] if story.content else "(no content)"
    
    return f"""
STORY: {story.title}
Significance Score: {story.significance_score:.1f}

Sources ({len(story.sources)} total):
{sources_text}

Key Facts:
{facts_text}

Full Content:
{content_preview}
"""
