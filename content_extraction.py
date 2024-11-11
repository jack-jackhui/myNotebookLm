from typing import List
from podcastfy.content_parser.content_extractor import ContentExtractor
#from config import JINA_API_KEY

def extract_content_from_sources(sources: List[str]) -> str:
    content_extractor = ContentExtractor()
    extracted_texts = []
    for source in sources:
        print(f"Extracting content from {source}")
        extracted_text = content_extractor.extract_content(source)
        extracted_texts.append(extracted_text)

    combined_text = "\n\n".join(extracted_texts)
    return combined_text