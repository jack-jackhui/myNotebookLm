from content_generation import create_content_generator

def generate_episode_details(transcript_text):
    """
    Generate the episode title and description from the given transcript text dynamically
    using the appropriate LLM provider.
    """
    # Dynamically initialize the appropriate ContentGenerator based on configuration
    content_generator = create_content_generator()

    # Generate title and description using specific methods
    title = content_generator.generate_title(transcript_text)
    description = content_generator.generate_description(transcript_text)

    # Remove extra whitespace and handle missing data
    title = title.strip() if title else "Untitled Episode"
    description = description.strip() if description else "No description available."

    return title, description

# Example usage (for testing purposes)
if __name__ == "__main__":
    # Example transcript content for testing
    sample_transcript = "Today, we discuss the impact of AI on the job market, including opportunities and challenges."

    title, description = generate_episode_details(sample_transcript)
    print("Generated Title:", title)
    print("Generated Description:", description)