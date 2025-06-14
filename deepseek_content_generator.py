# deepseek_content_generator.py

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from generic_content_generator import ContentGenerator
from datetime import datetime
import os
from azure.core.exceptions import AzureError
import time
import re

class DeepSeekContentGenerator(ContentGenerator):
    def __init__(self, conversation_config=None, api_config=None):
        super().__init__(config=conversation_config)

        # Extract DeepSeek-specific configuration
        self.endpoint = api_config.get('endpoint')
        self.model_name = api_config.get('model_name')
        self.api_key = api_config.get('api_key')

        # Initialize DeepSeek client
        self.client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )

    def clean_script(text: str) -> str:
        # Remove <think>...</think> blocks (including multiline)
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # Remove stray <think> or </think> tags
        text = re.sub(r"</?think>", "", text, flags=re.IGNORECASE)
        # Remove all stage directions in the format **[ ... ]**
        text = re.sub(r"\*\*\[.*?\]\*\*", "", text, flags=re.DOTALL)
        # Remove empty lines caused by removals
        text = re.sub(r"\n\s*\n", "\n", text)
        # Optionally strip leading/trailing whitespace
        return text.strip()

    def answer_question(self, question: str, document_content: str) -> str:
        """
        Generate an answer to a question based on document content using DeepSeek-R1.
        """
        prompt = f"Answer the following question based on the content provided:\n\nContent:\n{document_content}\n\nQuestion: {question}\nAnswer concisely."
        return self._generate_content(prompt, max_tokens=150)

    def generate_summary(self, document_content: str) -> str:
        """
        Generate a summary of the document content using DeepSeek-R1.
        """
        prompt = f"Summarize the following content:\n\n{document_content}\n\nThe summary should be concise and cover the main points."
        return self._generate_content(prompt, max_tokens=200)

    def generate_conversational_script(self, content: str) -> str:
        """
        Generate a conversation script based on provided content.
        """
        if not content:
            raise ValueError("Content cannot be empty for script generation.")

        system_prompt = "You are a podcast script writer creating engaging dialogues between two hosts."
        user_prompt = (
            f"Create a conversation between two hosts, Jack and Corr, about the following content:\n\n{content}\n\n"
            f"Each response should be conversational and reflect a back-and-forth dialogue style. Use explicit speaker tags like 'Jack:' and 'Corr:'."
        )

        messages = [
            SystemMessage(content=system_prompt),
            UserMessage(content=user_prompt)
        ]

        try:
            response = self.client.complete(
                messages=messages,
                model=self.model_name,
                temperature=0.7,
                max_tokens=1500
            )

            script = response.choices[0].message.content
            if script:
                script = self.clean_script(script)
            return script.strip() if script else ""

        except Exception as e:
            print(f"Failed to generate conversational script: {str(e)}")
            return ""

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
        Generate the conversation script using DeepSeek-R1.
        """
        conversation_config = self.config or {}
        podcast_name = conversation_config.get('podcast_name', 'AI Unchained')
        podcast_tagline = conversation_config.get('podcast_tagline', 'Your Guide to AI, Web 3.0, and the Cutting Edge of Tech')
        user_instructions = conversation_config.get('user_instructions', '')
        creativity = conversation_config.get('creativity', 0.7)
        max_tokens = conversation_config.get('word_count', 3000)

        # Configure system and user prompts based on segment type
        if is_opening:
            system_prompt = f"You are an AI assistant generating podcast scripts for {podcast_name}"
            user_prompt = self._create_opening_prompt(is_first_episode, input_texts, podcast_name, user_instructions)
        elif is_ending:
            system_prompt = f"You are an AI assistant generating podcast conclusions for {podcast_name}"
            user_prompt = self._create_closing_prompt(input_texts, user_instructions)
        elif is_segment:
            system_prompt = f"You are an AI assistant generating podcast segments for {podcast_name}"
            user_prompt = self._create_segment_prompt(input_texts, user_instructions)
        else:
            system_prompt = f"You are an AI assistant generating podcast content in the style of {podcast_name}"
            user_prompt = self._create_general_prompt(input_texts, user_instructions, podcast_tagline)

        messages = [
            SystemMessage(content=system_prompt),
            UserMessage(content=user_prompt)
        ]

        try:
            response = self.client.complete(
                messages=messages,
                model=self.model_name,
                temperature=creativity,
                max_tokens=max_tokens
            )

            script = response.choices[0].message.content
            if script:
                script = self.clean_script(script)
            self._save_script(script, output_filepath)
            return script.strip()

        except Exception as e:
            print(f"Failed to generate content: {str(e)}")
            return ""

    def _create_opening_prompt(self, is_first_episode, input_texts, podcast_name, instructions):
        if is_first_episode:
            return (
                f"{instructions}\nCreate the first episode opening for {podcast_name}. "
                f"Introduce the show, explain its concept, and outline future expectations. "
                f"Content: {input_texts}\nUse explicit 'Jack:' and 'Corr:' tags."
            )
        return (
            f"{instructions}\nCreate a regular episode opening for {podcast_name}. "
            f"Introduce today's topics without repeating first episode content. "
            f"Content: {input_texts}\nUse explicit speaker tags."
        )

    def _create_closing_prompt(self, input_texts, instructions):
        return (
            f"{instructions}\nCreate an episode conclusion. Summarize key points "
            f"and thank the audience. Content: {input_texts}\nUse speaker tags."
        )

    def _create_segment_prompt(self, input_texts, instructions):
        return (
            f"{instructions}\nCreate a mid-episode segment. Focus on: {input_texts}\n"
            "Maintain ongoing discussion without opening/closing phrases. Use speaker tags."
        )

    def _create_general_prompt(self, input_texts, instructions, tagline):
        return (
            f"{instructions}\nCreate podcast content about: {input_texts}\n"
            f"Style: {tagline}\nUse natural dialogue with 'Jack:' and 'Corr:' tags."
        )

    def _save_script(self, script, output_filepath):
        if output_filepath:
            os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(script)
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            default_path = f"data/transcripts/{timestamp}_deepseek_script.txt"
            os.makedirs(os.path.dirname(default_path), exist_ok=True)
            with open(default_path, 'w', encoding='utf-8') as f:
                f.write(script)

    def iterative_script_generation(self, input_segments: list, is_first_episode: bool = False) -> str:
        full_script = ""
        for segment in input_segments:
            segment_script = self.generate_qa_content(
                input_texts=segment,
                is_segment=True
            )
            full_script += segment_script + "\n\n"
        return full_script.strip()

    def generate_title(self, transcript_text: str) -> str:
        prompt = f"Generate a catchy podcast title based on:\n{transcript_text}\nKeep it short and descriptive."
        return self._generate_content(prompt, max_tokens=50)

    def generate_description(self, transcript_text: str) -> str:
        prompt = f"Create an engaging podcast description based on:\n{transcript_text}\nKeep it under 150 words."
        return self._generate_content(prompt, max_tokens=150)

    def _generate_content(self, prompt: str, max_tokens: int, system_message: str = None) -> str:
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(UserMessage(content=prompt))

        retries = 3
        for attempt in range(retries):
            try:
                response = self.client.complete(
                    messages=messages,
                    model=self.model_name,
                    max_tokens=max_tokens,
                    temperature=0.7,
                    timeout=30  # Increase timeout to 30 seconds
                )
                return response.choices[0].message.content.strip()
            except AzureError as e:
                if attempt < retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{retries})")
                    time.sleep(wait_time)
                    continue
                print(f"Final attempt failed: {str(e)}")
                return ""
