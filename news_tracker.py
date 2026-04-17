import feedparser
import logging
import random
import time
from datetime import datetime, timedelta
import re
import requests
from newspaper import Article
from settings import load_rss_feeds

logger = logging.getLogger(__name__)

# Rotating user agents to avoid 403 blocks
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Sites that commonly block scrapers - use summary only
BLOCKED_DOMAINS = [
    "bloomberg.com", "wsj.com", "ft.com", "nytimes.com",
    "washingtonpost.com", "economist.com", "businessinsider.com"
]


def clean_text(text):
    """Remove HTML tags from the summary and return cleaned text."""
    return re.sub(r'<.*?>', '', text)  # Remove HTML tags


def is_blocked_domain(url: str) -> bool:
    """Check if URL is from a domain known to block scrapers."""
    return any(domain in url.lower() for domain in BLOCKED_DOMAINS)


def get_full_text(url: str, max_retries: int = 2) -> str:
    """Retrieve the full text of an article from its URL using newspaper3k.

    Handles 403 errors with retry logic and user agent rotation.
    """
    # Skip known blocked domains
    if is_blocked_domain(url):
        logger.debug(f"Skipping blocked domain: {url}")
        return ""

    for attempt in range(max_retries):
        try:
            # Use random user agent
            user_agent = random.choice(USER_AGENTS)

            # Configure article with custom user agent
            config = Article(url)
            config.config.browser_user_agent = user_agent
            config.config.request_timeout = 10

            article = Article(url, config=config.config)
            article.download()
            article.parse()

            if article.text and len(article.text) > 100:
                return article.text
            return ""

        except Exception as e:
            error_str = str(e).lower()

            # Check for 403/blocked errors
            if "403" in error_str or "forbidden" in error_str or "blocked" in error_str:
                logger.warning(f"Blocked (attempt {attempt + 1}/{max_retries}): {url}")
                if attempt < max_retries - 1:
                    time.sleep(1 + random.random())  # Random delay before retry
                    continue
                else:
                    logger.info(f"Giving up on blocked URL: {url}")
                    return ""

            # Check for timeout/connection errors
            if "timeout" in error_str or "connection" in error_str:
                logger.warning(f"Connection issue (attempt {attempt + 1}/{max_retries}): {url}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue

            logger.debug(f"Could not retrieve full text for {url}: {e}")
            return ""

    return ""

def get_recent_articles():
    recent_articles = []
    now = datetime.now()
    cutoff_date = now - timedelta(days=1)  # Get articles from the last day

    # Load RSS feeds from the configuration
    rss_feeds = load_rss_feeds()

    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                # Parse the publish date
                published_date = datetime(*entry.published_parsed[:6])

                # Only add articles published after the cutoff date
                if published_date > cutoff_date:
                    # Try to fetch the full text, falling back to summary if needed
                    full_text = get_full_text(entry.link)
                    if not full_text:  # If full text is unavailable, use summary
                        full_text = clean_text(entry.get('summary', 'Summary not available.'))

                    # Format the article for clear context
                    article_content = f"Title: {entry.title}\nContent: {full_text}"

                    article = {
                        "title": entry.title,
                        "content": full_text,
                        "link": entry.link,
                        "published": published_date
                    }
                    recent_articles.append(article)
        except Exception as e:
            print(f"Failed to parse feed {feed_url}: {e}")

    print(f"\nTotal articles fetched: {len(recent_articles)}")
    return recent_articles
