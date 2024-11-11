import feedparser
from datetime import datetime, timedelta
import re
from newspaper import Article

# Define your news sources here (these should have RSS feeds)
rss_feeds = [
    "https://news.ycombinator.com/rss",  # Example: Tech news
    "https://rss.cnn.com/rss/edition_business.rss",
    "https://cointelegraph.com/editors_pick_rss",
    "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
    "https://decrypt.co/feed?_gl=1*15n6zx3*_up*MQ..*_ga*MzA2NjYyMjguMTczMDQ0NDYzMQ..*_ga_S6XJW9326S*MTczMDQ0NDYzMC4xLjEuMTczMDQ0NDYzMy4wLjAuMA..",
    # Add more sources related to your focus topics
]

def clean_text(text):
    """Remove HTML tags from the summary and return cleaned text."""
    return re.sub(r'<.*?>', '', text)  # Remove HTML tags

def get_full_text(url):
    """Retrieve the full text of an article from its URL using newspaper3k."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Could not retrieve full text for {url}: {e}")
        return ""

def get_recent_articles():
    recent_articles = []
    now = datetime.now()
    cutoff_date = now - timedelta(days=1)  # Get articles from the last day

    for feed_url in rss_feeds:
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
    print(f"\nTotal articles fetched: {len(recent_articles)}")
    return recent_articles
