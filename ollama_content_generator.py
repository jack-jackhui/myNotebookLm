# ollama_content_generator.py

import requests
from generic_content_generator import ContentGenerator
from datetime import datetime
import os

class OllamaContentGenerator(ContentGenerator):
    def __init__(self, conversation_config, api_config):
        super().__init__(config=conversation_config)
        self.host = api_config['host']
        self.port = api_config['port']
        self.model_name = api_config['model_name']

    def _generate_content(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> str:
        """
        Internal helper to call the Ollama API with a specific prompt and return the response content.
        """
        url = f"http://{self.host}:{self.port}/api/generate"
        response = requests.post(url, json={
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        })
        if response.status_code == 200:
            return response.json().get("text", "").strip()
        else:
            print(f"Failed to generate content from Ollama: {response.text}")
            return ""

    def answer_question(self, question: str, document_content: str) -> str:
        """
        Generate an answer to a question based on document content using Ollama.
        """
        prompt = f"Answer the following question based on the content provided:\n\nContent:\n{document_content}\n\nQuestion: {question}\nAnswer concisely."
        return self._generate_content(prompt, max_tokens=150)

    def generate_summary(self, document_content: str) -> str:
        """
        Generate a summary of the document content using Ollama.
        """
        prompt = f"Summarize the following content:\n\n{document_content}\n\nThe summary should be concise and cover the main points."
        return self._generate_content(prompt, max_tokens=200)

    def generate_conversational_script(self, content: str) -> str:
        """
        Generate a conversation script based on provided content.
        """
        prompt = (
            f"Create a conversation between two hosts, Jack and Corr, about the following content:\n\n{content}\n\n"
            f"Each response should be conversational and reflect a back-and-forth dialogue style. Use explicit speaker tags like 'Jack:' and 'Corr:'."
        )
        return self._generate_content(prompt, max_tokens=2000)

    def generate_qa_content(
        self,
        input_texts: str = "",
        image_file_paths: list = [],
        output_filepath: str = None,
        is_first_episode: bool = False,
        is_segment: bool = False,
        is_opening: bool = False,
        is_ending: bool = False
    ) -> str:
        """
        Generate the conversation script using Ollama.
        """
        conversation_config = self.config or {}
        podcast_name = conversation_config.get('podcast_name', 'AI Unchained')
        podcast_tagline = conversation_config.get('podcast_tagline', 'Your Guide to AI, Web 3.0, and the Cutting Edge of Tech')
        user_instructions = conversation_config.get('user_instructions', '')
        creativity = conversation_config.get('creativity', 0.7)
        max_tokens = conversation_config.get('word_count', 3000)

        # Adjust the prompt based on whether it’s the first episode
        if is_opening:
            if is_first_episode:
                system_prompt = (
                    f"You are generating the first-episode opening script for '{podcast_name}'. "
                    f"Include the speaker's name (Jack or Corr) followed by a colon and dialogue. "
                    f"Introduce the show and set up expectations."
                )
                user_prompt = (
                    f"{user_instructions}\n\nThis is the first episode of '{podcast_name}'. "
                    f"Provide an engaging introduction to the show. Hosts: Jack(male) and Corr(female)\n"
                    f"Content to discuss:\n{input_texts}\n"
                )
            else:
                system_prompt = (
                    f"Generate an opening script for '{podcast_name}'. Include speaker names and set context for today’s topics."
                )
                user_prompt = (
                    f"{user_instructions}\n\nHosts: Jack and Corr\nOpening content: {input_texts}\n\n"
                )
        elif is_ending:
            system_prompt = (
                f"Generate the closing script for '{podcast_name}'. Summarize main points, thank the audience, and offer any final thoughts."
            )
            user_prompt = (
                f"{user_instructions}\n\nHosts: Jack and Corr\nEnding content: {input_texts}\n\n"
            )
        elif is_segment:
            system_prompt = (
                f"Generate a podcast segment script for '{podcast_name}'. "
                f"Include speaker names and ensure continuity without introductory or concluding remarks."
            )
            user_prompt = (
                f"{user_instructions}\n\nHosts: Jack and Corr\n"
                f"This is part of a single episode. Do not add opening or closing content.\n"
                f"Topic for this segment: {input_texts}\n\n"
            )
        else:
            system_prompt = (
                f"Generate a dynamic, engaging podcast script for '{podcast_name}' in the style of All-in Podcasts. "
                f"Include speaker names and maintain engaging, insightful content."
            )
            user_prompt = (
                f"{user_instructions}\n\nHosts: Jack(male) and Corr(female)\n{input_texts}\n\n"
            )

        prompt = f"{system_prompt}\n\n{user_prompt}"
        script = self._generate_content(prompt, max_tokens=max_tokens, temperature=creativity)

        # Save the script if an output filepath is provided
        if output_filepath:
            os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(script)

        return script

    def iterative_script_generation(self, input_segments: list, is_first_episode: bool = False) -> str:
        """
        Generate the full script by processing each segment iteratively.
        """
        full_script = ""
        for i, segment in enumerate(input_segments):
            segment_prompt = (
                f"Continue the ongoing discussion for the current episode, focusing on the topic: {segment}. "
                "Ensure this is a continuation without introductory or concluding remarks."
            )
            segment_script = self.generate_qa_content(
                input_texts=segment_prompt,
                is_first_episode=False,
                is_segment=True
            )
            full_script += segment_script + "\n\n"
        return full_script.strip()