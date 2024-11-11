from openai import AzureOpenAI
from podcastfy.content_generator import ContentGenerator
from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_MODEL_NAME,
)
from datetime import datetime
import os

class AzureContentGenerator(ContentGenerator):
    def __init__(self, conversation_config=None):
        super().__init__(api_key=AZURE_OPENAI_API_KEY, conversation_config=conversation_config)

        # Initialize AzureOpenAI client
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )

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
        Generate the conversation script using Azure OpenAI.
        """
        # Prepare the prompt based on conversation_config
        conversation_config = self.config_conversation or {}
        podcast_name = conversation_config.get('podcast_name', 'AI Unchained')
        podcast_tagline = conversation_config.get('podcast_tagline', 'Your Guide to AI, Web 3.0, and the Cutting Edge of Tech')
        user_instructions = conversation_config.get('user_instructions', '')
        creativity = conversation_config.get('creativity', 0.7)
        max_tokens = conversation_config.get('word_count', 3000)

        # Adjust the prompt based on whether it’s the first episode
        if is_opening:
            # Opening prompt with consideration for the first episode
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
                # Regular opening prompt for non-first episodes
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
            # Closing prompt
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
            # Prompt for segments within the same episode to ensure continuity
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
                f"a dynamic interaction that connects smoothly with the rest of the episode."
                f"Use layman's language to explain any technology concept and make it simple to understand by normal person.\n"
                f"Use explicit speaker tags, e.g., 'Jack: [Dialogue]', 'Corr: [Dialogue]'."
            )
        else:
            # Standard prompt for introductory or concluding content
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

        try:
            # Call the Azure OpenAI API using the AzureOpenAI client
            response = self.client.chat.completions.create(
                messages=messages,
                model=AZURE_OPENAI_MODEL_NAME,  # Your deployment name
                temperature=creativity,
                max_tokens=max_tokens
            )

            # Extract the generated script
            script = response.choices[0].message.content
            # print(f"DEBUG: LLM Response:\n{script}\n")

            # Define the output directory and filename with date and time
            output_directory = 'data/transcripts'
            os.makedirs(output_directory, exist_ok=True)
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            output_filepath = os.path.join(output_directory, f"{timestamp}_conversation_script.txt")

            # Save the script if an output filepath is provided
            if output_filepath:
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    f.write(script)

            return script.strip()

        except Exception as e:
            print(f"Failed to generate conversation script: {str(e)}")
            return ""

    def iterative_script_generation(self, input_segments: list, is_first_episode: bool = False) -> str:
        """
        Generate the full script by processing each segment iteratively.
        """
        full_script = ""

        """
        # Generate the opening segment
        print("Debug: Generating episode opening...")
        opening_prompt = (
            "This is the opening of the episode, introducing the show and setting up the topics to be discussed. "
            "This will be a single, continuous episode with multiple topics."
        )
        opening_script = self.generate_qa_content(
            input_texts=opening_prompt,
            is_first_episode=is_first_episode,
            is_segment=False
        )
        print(f"DEBUG: Opening prompt sent to LLM:\n{opening_prompt}\n")
        full_script += opening_script + "\n\n"
        """

        # Generate each segment as a continuation of the previous discussion
        for i, segment in enumerate(input_segments):
            print(f"Generating script for segment {i + 1}: {segment[:30]}...")  # Log progress for each segment
            segment_prompt = (
                f"Continue the ongoing discussion for the current episode, focusing on the topic: {segment}. "
                "Ensure this is a continuation without repeating the opening or closing."
            )
            segment_script = self.generate_qa_content(
                input_texts=segment_prompt,
                is_first_episode=False,
                is_segment=True  # Mark this as part of the main content
            )
            # print(f"DEBUG: Segment prompt sent to LLM:\n{segment_prompt}\n")
            full_script += segment_script + "\n\n"  # Add each generated segment to the full script

        """
        # Generate the closing segment
        print("Debug: Generating episode closing...")
        closing_prompt = (
            "This is the closing of the episode, summarizing the topics covered and thanking the audience."
        )

        closing_script = self.generate_qa_content(
            input_texts=closing_prompt,
            is_first_episode=False,
            is_segment=False
        )
        print(f"DEBUG: Closing prompt sent to LLM:\n{closing_prompt}\n")
        full_script += closing_script
        """

        return full_script.strip()

    def generate_title(self, transcript_text: str) -> str:
        """
        Generate an engaging title for the podcast episode based on transcript content.
        """
        prompt = (
            f"Generate an engaging title for a podcast episode based on the following content:\n\n{transcript_text}\n\n"
            "Title should be short, catchy, and summarize the main topic."
        )
        return self._generate_content(prompt, max_tokens=50)  # Limiting tokens for a concise title

    def generate_description(self, transcript_text: str) -> str:
        """
        Generate a concise and engaging description for the podcast episode based on transcript content.
        """
        prompt = (
            f"Generate a concise and engaging description for a podcast episode based on the following content:\n\n{transcript_text}\n\n"
            "The description should be informative, enticing, and give an overview of the main points discussed."
        )
        return self._generate_content(prompt, max_tokens=150)  # Allowing more tokens for a richer description

    def _generate_content(self, prompt: str, max_tokens: int) -> str:
        """
        Internal helper to call the OpenAI API with a specific prompt and return the response content.
        """
        messages = [{"role": "user", "content": prompt}]
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model=AZURE_OPENAI_MODEL_NAME,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Failed to generate content: {str(e)}")
            return ""