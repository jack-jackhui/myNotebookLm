import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def generate_article(prompt):
    response = openai.ChatCompletion.create(
        model='gpt-4',  # Or 'gpt-3.5-turbo' if you don't have access to GPT-4
        messages=[
            {'role': 'system', 'content': 'You are a knowledgeable writer specializing in creating insightful articles.'},
            {'role': 'user', 'content': prompt}
        ],
        max_tokens=1500,
        temperature=0.7,
    )
    article = response['choices'][0]['message']['content'].strip()
    return article