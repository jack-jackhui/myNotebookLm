"""Base content generator with shared logic."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from constants import EpisodeLength, TokenLimits, Defaults
from errors import LLMProviderError

logger = logging.getLogger(__name__)


class ContentGenerator(ABC):
    """Abstract base class for LLM content generators."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._podcast_name = self.config.get('podcast_name', Defaults.PODCAST_NAME)
        self._podcast_tagline = self.config.get('podcast_tagline', Defaults.PODCAST_TAGLINE)
        self._user_instructions = self.config.get('user_instructions', '')
        self._creativity = self.config.get('creativity', Defaults.CREATIVITY)
        self._max_tokens = self.config.get('word_count', Defaults.WORD_COUNT)
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name for error messages."""
        pass
    
    @abstractmethod
    def _call_llm(
        self, 
        messages: list, 
        max_tokens: int, 
        temperature: float = 0.7
    ) -> str:
        """Make the actual LLM API call. Implement in subclass."""
        pass
    
    def _get_length_config(self, target_word_count: Optional[int]) -> Tuple[str, int]:
        """Get length instruction and max tokens based on target word count."""
        if not target_word_count:
            return "", TokenLimits.DEFAULT
        
        if target_word_count <= EpisodeLength.SHORT:
            return (
                f"Keep the conversation brief and focused, around {EpisodeLength.SHORT} words total (~5 minutes when spoken). ",
                TokenLimits.SHORT_EPISODE
            )
        elif target_word_count <= EpisodeLength.MEDIUM:
            return (
                f"Create a moderately detailed conversation, around 2,000-2,500 words (~15 minutes when spoken). ",
                TokenLimits.MEDIUM_EPISODE
            )
        else:
            return (
                f"Create an in-depth, detailed conversation, around 4,000-4,500 words (~30 minutes when spoken). ",
                TokenLimits.LONG_EPISODE
            )
    
    def _build_prompts(
        self,
        input_texts: str,
        host_1_name: str,
        host_2_name: str,
        is_first_episode: bool = False,
        is_segment: bool = False,
        is_opening: bool = False,
        is_ending: bool = False
    ) -> Tuple[str, str]:
        """Build system and user prompts based on segment type."""
        
        if is_opening:
            if is_first_episode:
                system_prompt = (
                    f"You are an AI assistant generating the first-episode opening script for '{self._podcast_name}'. "
                    f"Each section should explicitly include the speaker's name ({host_1_name} or {host_2_name}) followed by a colon and dialogue.\n"
                    f"Your script should introduce the show, delve into its concept, and give insights on what the audience can expect in future episodes."
                )
                user_prompt = (
                    f"{self._user_instructions}\n\n"
                    f"This is the first episode of '{self._podcast_name}'. Provide a welcoming introduction to the show, explaining its concept and the value it offers. "
                    f"Hosts: {host_1_name}(male) and {host_2_name}(female)\n"
                    f"Use explicit speaker tags, e.g., '{host_1_name}: [Dialogue]', '{host_2_name}: [Dialogue]'.\n"
                    f"Content to discuss:\n{input_texts}\n"
                    f"This is just the opening segment of a long single episode so do not include any ending or conclusion of the episode."
                )
            else:
                system_prompt = (
                    f"You are an AI assistant generating an opening script for the ongoing episode of '{self._podcast_name}'.\n"
                    f"Each section should explicitly include the speaker's name ({host_1_name} or {host_2_name}) followed by a colon and dialogue.\n"
                    f"Set the context for today's topics and welcome the audience."
                )
                user_prompt = (
                    f"{self._user_instructions}\n\n"
                    f"Hosts: {host_1_name} and {host_2_name}\n"
                    f"Opening content: {input_texts}\n\n"
                    f"Provide a welcoming introduction without repeating introductory information from the first episode.\n"
                    f"Use explicit speaker tags, e.g., '{host_1_name}: [Dialogue]', '{host_2_name}: [Dialogue]'."
                )
        elif is_ending:
            system_prompt = (
                f"You are an AI assistant generating the closing script for an episode of '{self._podcast_name}'. "
                f"Summarize the main points, thank the audience, and offer any final thoughts.\n"
                f"Each section should explicitly include the speaker's name ({host_1_name} or {host_2_name}) followed by a colon and dialogue."
            )
            user_prompt = (
                f"{self._user_instructions}\n\n"
                f"Hosts: {host_1_name} and {host_2_name}\n"
                f"Ending content: {input_texts}\n\n"
                f"Ensure this is a concluding segment, wrapping up the discussion and leaving the audience with a closing message.\n"
                f"Use explicit speaker tags, e.g., '{host_1_name}: [Dialogue]', '{host_2_name}: [Dialogue]'."
            )
        elif is_segment:
            system_prompt = (
                f"You are an AI assistant generating a podcast segment script for the ongoing episode of '{self._podcast_name}'.\n"
                f"Each section should explicitly include the speaker's name ({host_1_name} or {host_2_name}) followed by a colon and dialogue.\n"
                f"This segment is part of a larger conversation within a single episode. Avoid starting or ending the segment with "
                f"phrases like 'Welcome back' or 'Thanks for listening.' Ensure smooth continuity as part of an ongoing discussion."
            )
            user_prompt = (
                f"{self._user_instructions}\n\n"
                f"Hosts: {host_1_name} and {host_2_name}\n"
                f"This is a part of a larger conversation within a single episode. Do not add any episode opening content or episode ending content.\n"
                f"Topic for this segment: {input_texts}\n\n"
                f"Encourage the hosts to engage in a deep dialogue on this topic, sharing personal insights and experiences, and ensuring "
                f"a dynamic interaction that connects smoothly with the rest of the episode.\n"
                f"Use layman's language to explain any technology concept and make it simple to understand by normal person.\n"
                f"Use explicit speaker tags, e.g., '{host_1_name}: [Dialogue]', '{host_2_name}: [Dialogue]'."
            )
        else:
            system_prompt = (
                f"You are an AI assistant that generates insightful and engaging podcast scripts in the style of All-in Podcasts.\n"
                f"The podcast name is '{self._podcast_name}' and tagline is '{self._podcast_tagline}'. The conversation should be insightful, dynamic, and engaging.\n"
                f"Each section should explicitly include the speaker's name ({host_1_name} or {host_2_name}) followed by a colon and dialogue."
            )
            user_prompt = (
                f"{self._user_instructions}\n\n"
                f"Hosts: {host_1_name}(male) and {host_2_name}(female)\n"
                f"{input_texts}\n\n"
                f"Encourage the hosts to engage in a rich dialogue, exploring topics deeply, sharing personal insights and experiences. "
                f"Use layman's language to explain any technology concept and make it simple to understand by a normal person.\n"
                f"Use explicit speaker tags, e.g., '{host_1_name}: [Dialogue]', '{host_2_name}: [Dialogue]'."
            )
        
        return system_prompt, user_prompt
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _call_llm_with_retry(
        self, 
        messages: list, 
        max_tokens: int, 
        temperature: float = 0.7
    ) -> str:
        """Call LLM with retry logic."""
        try:
            return self._call_llm(messages, max_tokens, temperature)
        except Exception as e:
            logger.warning(f"LLM call failed, retrying: {e}")
            raise
    
    def generate_conversational_script(
        self, 
        content: str, 
        target_word_count: Optional[int] = None,
        host_1_name: str = Defaults.HOST_1_NAME,
        host_2_name: str = Defaults.HOST_2_NAME
    ) -> str:
        """Generate a conversation script based on provided content."""
        if not content:
            raise ValueError("Content cannot be empty for script generation.")
        
        length_instruction, max_tokens = self._get_length_config(target_word_count)
        
        prompt = (
            f"Create a conversation between two hosts, {host_1_name} and {host_2_name}, about the following content:\n\n{content}\n\n"
            f"{length_instruction}"
            f"Each response should be conversational and reflect a back-and-forth dialogue style. "
            f"Use explicit speaker tags like '{host_1_name}:' and '{host_2_name}:'."
        )
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            script = self._call_llm_with_retry(messages, max_tokens)
            return script.strip() if script else ""
        except Exception as e:
            raise LLMProviderError(self.provider_name, f"Failed to generate script: {e}")
    
    def generate_qa_content(
        self,
        input_texts: str = "",
        is_first_episode: bool = False,
        is_segment: bool = False,
        is_opening: bool = False,
        is_ending: bool = False,
        host_1_name: str = Defaults.HOST_1_NAME,
        host_2_name: str = Defaults.HOST_2_NAME
    ) -> str:
        """Generate conversation script using configured LLM."""
        system_prompt, user_prompt = self._build_prompts(
            input_texts=input_texts,
            host_1_name=host_1_name,
            host_2_name=host_2_name,
            is_first_episode=is_first_episode,
            is_segment=is_segment,
            is_opening=is_opening,
            is_ending=is_ending
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            script = self._call_llm_with_retry(messages, self._max_tokens, self._creativity)
            return script.strip() if script else ""
        except Exception as e:
            raise LLMProviderError(self.provider_name, f"Failed to generate QA content: {e}")
    
    def iterative_script_generation(
        self, 
        input_segments: list, 
        is_first_episode: bool = False,
        host_1_name: str = Defaults.HOST_1_NAME,
        host_2_name: str = Defaults.HOST_2_NAME
    ) -> str:
        """Generate full script by processing each segment iteratively."""
        full_script = ""
        for i, segment in enumerate(input_segments):
            logger.info(f"Generating script for segment {i + 1}: {segment[:30]}...")
            segment_script = self.generate_qa_content(
                input_texts=segment,
                is_first_episode=False,
                is_segment=True,
                host_1_name=host_1_name,
                host_2_name=host_2_name
            )
            full_script += segment_script + "\n\n"
        return full_script.strip()
    
    def generate_summary(self, document_content: str) -> str:
        """Generate a summary of the document content."""
        prompt = (
            f"Summarize the following content:\n\n{document_content}\n\n"
            "The summary should be concise and cover the main points."
        )
        messages = [{"role": "user", "content": prompt}]
        
        try:
            return self._call_llm_with_retry(messages, TokenLimits.SUMMARY)
        except Exception as e:
            raise LLMProviderError(self.provider_name, f"Failed to generate summary: {e}")
    
    def answer_question(self, question: str, document_content: str) -> str:
        """Generate an answer to a question based on document content."""
        prompt = (
            f"Answer the following question based on the content provided:\n\n"
            f"Content:\n{document_content}\n\n"
            f"Question: {question}\nAnswer concisely."
        )
        messages = [{"role": "user", "content": prompt}]
        
        try:
            return self._call_llm_with_retry(messages, TokenLimits.ANSWER)
        except Exception as e:
            raise LLMProviderError(self.provider_name, f"Failed to answer question: {e}")
    
    def generate_title(self, transcript_text: str) -> str:
        """Generate an engaging title for the podcast episode."""
        prompt = (
            f"Generate an engaging title for a podcast episode based on the following content:\n\n{transcript_text}\n\n"
            "Title should be short, catchy, and summarize the main topic."
        )
        messages = [{"role": "user", "content": prompt}]
        
        try:
            return self._call_llm_with_retry(messages, TokenLimits.TITLE)
        except Exception as e:
            raise LLMProviderError(self.provider_name, f"Failed to generate title: {e}")
    
    def generate_description(self, transcript_text: str) -> str:
        """Generate a concise description for the podcast episode."""
        prompt = (
            f"Generate a concise and engaging description for a podcast episode based on the following content:\n\n{transcript_text}\n\n"
            "The description should be informative, enticing, and give an overview of the main points discussed."
        )
        messages = [{"role": "user", "content": prompt}]
        
        try:
            return self._call_llm_with_retry(messages, TokenLimits.DESCRIPTION)
        except Exception as e:
            raise LLMProviderError(self.provider_name, f"Failed to generate description: {e}")
