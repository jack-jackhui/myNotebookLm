from typing import List
from podcastfy.content_parser.content_extractor import ContentExtractor
#from config import JINA_API_KEY
import os
from pptx import Presentation

def extract_text_from_pptx(pptx_path):
    text = []
    prs = Presentation(pptx_path)
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text.append(shape.text)
    return "\n".join(text)

def extract_content_from_sources(sources: List[str]) -> str:
    content_extractor = ContentExtractor()
    extracted_texts = []
    for source in sources:
        ext = os.path.splitext(source)[1].lower()
        if ext == ".pptx":
            print(f"Extracting content from PowerPoint: {source}")
            extracted_text = extract_text_from_pptx(source)
        else:
            print(f"Extracting content from {source}")
            extracted_text = content_extractor.extract_content(source)
        extracted_texts.append(extracted_text)
    combined_text = "\n\n".join(extracted_texts)
    return combined_text