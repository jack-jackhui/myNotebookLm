# generic_content_generator.py

class ContentGenerator:
    def __init__(self, config):
        self.config = config

    def generate_conversational_script(self, content):
        """
        Generate a conversational script based on the provided content.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def generate_summary(self, content):
        """
        Generate a summary of the provided content.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def answer_question(self, question, document_content):
        """
        Answer a question based on the provided document content.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def generate_qa_content(
        self, input_texts, image_file_paths=None, output_filepath=None,
        is_first_episode=False, is_segment=False, is_opening=False, is_ending=False
    ):
        """
        Generate QA-style content based on input parameters.
        Optional parameters provide context on where this content fits in an episode.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def iterative_script_generation(self, input_segments, is_first_episode=False):
        """
        Generate a full script by processing each segment iteratively.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def generate_title(self, transcript_text):
        """
        Generate an engaging title based on transcript content.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def generate_description(self, transcript_text):
        """
        Generate a concise and engaging description for content based on transcript.
        """
        raise NotImplementedError("Subclasses must implement this method")