# openai_content_generator.py

from openai import OpenAI
from generic_content_generator import ContentGenerator
from datetime import datetime
import os


class OpenAIContentGenerator(ContentGenerator):
    def __init__(self, conversation_config=None, api_config=None):
        super().__init__(config=conversation_config)

        # Initialize OpenAI client with the provided API key
        self.client = OpenAI(
            api_key=api_config.get('api_key')  # Set the API key
        )
        self.model_name = api_config.get('model_name')  # Model to use for content generation

    def answer_question(self, question: str, document_content: str) -> str:
        """
        Generate an answer to a question based on document content using OpenAI.
        """
        prompt = f"Answer the following question based on the content provided:\n\nContent:\n{document_content}\n\nQuestion: {question}\nAnswer concisely."
        return self._generate_content(prompt, max_tokens=150)

    def generate_summary(self, document_content: str) -> str:
        """
        Generate a summary of the document content using OpenAI.
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
        is_first_episode: bool = False,
        is_segment: bool = False,
        is_opening: bool = False,
        is_ending: bool = False
    ) -> str:
        """
        Generate the conversation script using OpenAI.
        """
        conversation_config = self.config or {}
        podcast_name = conversation_config.get('podcast_name', 'AI Unchained')
        podcast_tagline = conversation_config.get('podcast_tagline', 'Your Guide to AI, Web 3.0, and the Cutting Edge of Tech')
        user_instructions = conversation_config.get('user_instructions', '')
        creativity = conversation_config.get('creativity', 0.7)
        max_tokens = conversation_config.get('word_count', 3000)

        if is_opening:
            if is_first_episode:
                system_prompt = (
                    f"You are an AI assistant generating the first-episode opening script for '{podcast_name}'. "
                    f"Each section should explicitly include the speaker's name (Jack or Corr) followed by a colon and dialogue. \n"
                    f"Your script should introduce the show, delve into its concept, and give insights on what the audience can expect in future episodes."
                )
                user_prompt = (
                    f"{user_instructions}\n\n"
                    f"This is the first episode of '{podcast_name}'. Provide a welcoming introduction to the show, explaining its concept and the value it offers. "
                    f"Hosts: Jack(male) and Corr(female)\n"
                    f"Use explicit speaker tags, e.g., 'Jack: [Dialogue]', 'Corr: [Dialogue]'.\n"
                    f"Content to discuss:\n{input_texts}\n"
                    f"This is just the opening segment of a long single episode so do not include any ending or conclusion of the episode."
                )
            else:
                system_prompt = (
                    f"You are an AI assistant generating an opening script for the ongoing episode of '{podcast_name}'. \n"
                    f"Each section should explicitly include the speaker's name (Jack or Corr) followed by a colon and dialogue. \n"
                    f"Set the context for today’s topics and welcome the audience."
                )
                user_prompt = (
                    f"{user_instructions}\n\n"
                    f"Hosts: Jack and Corr\n"
                    f"Opening content: {input_texts}\n\n"
                    f"Provide a welcoming introduction without repeating introductory information from the first episode.\n"
                    f"Use explicit speaker tags, e.g., 'Jack: [Dialogue]', 'Corr: [Dialogue]'."
                )
        elif is_ending:
            system_prompt = (
                f"You are an AI assistant generating the closing script for an episode of '{podcast_name}'. "
                f"Summarize the main points, thank the audience, and offer any final thoughts.\n"
                f"Each section should explicitly include the speaker's name (Jack or Corr) followed by a colon and dialogue."
            )
            user_prompt = (
                f"{user_instructions}\n\n"
                f"Hosts: Jack and Corr\n"
                f"Ending content: {input_texts}\n\n"
                f"Ensure this is a concluding segment, wrapping up the discussion and leaving the audience with a closing message.\n"
                f"Use explicit speaker tags, e.g., 'Jack: [Dialogue]', 'Corr: [Dialogue]'."
            )
        elif is_segment:
            system_prompt = (
                f"You are an AI assistant generating a podcast segment script for the ongoing episode of '{podcast_name}'.\n"
                f"Each section should explicitly include the speaker's name (Jack or Corr) followed by a colon and dialogue. \n"
                f"This segment is part of a larger conversation within a single episode. Avoid starting or ending the segment with "
                f"phrases like 'Welcome back' or 'Thanks for listening.' Ensure smooth continuity as part of an ongoing discussion."
            )
            user_prompt = (
                f"{user_instructions}\n\n"
                f"Hosts: Jack and Corr\n"
                f"This is a part of a larger conversation within a single episode. Do not add any episode opening content or episode ending content.\n"
                f"Topic for this segment: {input_texts}\n\n"
                f"Encourage the hosts to engage in a deep dialogue on this topic, sharing personal insights and experiences, and ensuring "
                f"a dynamic interaction that connects smoothly with the rest of the episode.\n"
                f"Use explicit speaker tags, e.g., 'Jack: [Dialogue]', 'Corr: [Dialogue]'."
            )
        else:
            system_prompt = (
                f"You are an AI assistant that generates insightful and engaging podcast scripts in the style of All-in Podcasts.\n"
                f"The podcast name is '{podcast_name}' and tagline is '{podcast_tagline}'. The conversation should be insightful, dynamic, and engaging.\n"
                f"Each section should explicitly include the speaker's name (Jack or Corr) followed by a colon and dialogue."
            )
            user_prompt = (
                f"{user_instructions}\n\n"
                f"Hosts: Jack(male) and Corr(female)\n"
                f"{input_texts}\n\n"
                f"Encourage the hosts to engage in a rich dialogue, exploring topics deeply, sharing personal insights and experiences. "
                f"Use layman's language to explain any technology concept and make it simple to understand by a normal person.\n"
                f"Use explicit speaker tags, e.g., 'Jack: [Dialogue]', 'Corr: [Dialogue]'."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self._generate_content(messages, max_tokens)

    def iterative_script_generation(self, input_segments: list, is_first_episode: bool = False) -> str:
        full_script = ""
        for i, segment in enumerate(input_segments):
            segment_script = self.generate_qa_content(
                input_texts=segment,
                is_first_episode=is_first_episode,
                is_segment=True
            )
            full_script += segment_script + "\n\n"
        return full_script.strip()

    def _generate_content(self, messages, max_tokens):
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Failed to generate content: {str(e)}")
            return ""