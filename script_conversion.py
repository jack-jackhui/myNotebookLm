import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def convert_to_conversational_script(article_text):
    prompt = (
        "Transform the following article into a conversational script between two podcast hosts discussing the content. "
        "Ensure the conversation is engaging and informative.\n\n"
        f"Article:\n{article_text}"
    )
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[
            {'role': 'system', 'content': 'You are a scriptwriter for a podcast.'},
            {'role': 'user', 'content': prompt}
        ],
        max_tokens=2000,
        temperature=0.7,
    )
    script = response['choices'][0]['message']['content'].strip()
    return script