# custom_content_extractor.py

from podcastfy.content_parser.content_extractor import ContentExtractor
from youtube_transcriber import YouTubeTranscriber  # Your modified version
from website_extractor import WebsiteExtractor      # Your modified version
from pdf_extractor import PDFExtractor              # Your modified version
import logging

logger = logging.getLogger(__name__)