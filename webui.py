import streamlit as st
import os
from content_generation import create_content_generator
from content_extraction import extract_content_from_sources
from text_to_speech_conversion import convert_script_to_audio
from validation import validate_credentials
from datetime import datetime
import asyncio
from config import (
    FRONTENDURL,
    REQUIRE_LOGIN,
    conversation_config_path,
    INTRO_MUSIC_PATH,
    OUTRO_MUSIC_PATH,
    load_llm_config,
)

# Define paths
SCRIPT_FILE_PATH = './data/transcripts/'
AUDIO_FILE_PATH = './data/audio/podcast/'


# Function to save uploaded files to disk
def save_file(uploaded_file):
    """Save an uploaded file to the local filesystem."""
    save_dir = "./uploaded_files/"
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Configure the page
st.set_page_config(
    page_title="MyNoteBookLM - Open Source AI Note Assistant",
    page_icon="📊",
)

# Streamlit App
st.title("MyNoteBookLM")
st.write("Upload documents, generate summaries, ask questions, and create a podcast-style audio version of your notes.")

# Authenticate the user session
if REQUIRE_LOGIN and not validate_credentials():
    st.error("You need to be logged in to view this page.")
    login_url = FRONTENDURL  # Replace with your actual login page URL
    st.markdown(f"[Go to Login Page]({login_url})")
else:
    # Load LLM configuration
    content_generator = create_content_generator()  # Dynamically load the correct LLM provider

    # File Upload Section
    uploaded_files = st.file_uploader("Upload your source files (PDF, Word, Text)", accept_multiple_files=True,
                                      type=["pdf", "docx", "txt"])

    if uploaded_files:
        saved_files = [save_file(file) for file in uploaded_files]
        st.success("Files uploaded successfully!")

        # Extract and Display Content
        combined_text = extract_content_from_sources(saved_files)
        st.write("Content extracted successfully.")

        # Generate Summary
        st.write("### Generating Summary...")
        try:
            summary = content_generator.generate_summary(combined_text)
            st.write("**Summary of the Uploaded Content:**")
            st.write(summary)
        except NotImplementedError:
            st.error("Summary generation is not supported by the current LLM provider.")

        # Q&A Section
        st.write("### Ask Questions about the Content")
        question = st.text_input("Enter your question here:")
        if question:
            try:
                st.write("Generating answer...")
                answer = content_generator.answer_question(question, combined_text)
                st.write("**Answer:**")
                st.write(answer)
            except NotImplementedError:
                st.error("Answering questions is not supported by the current LLM provider.")

        # Toggle Audio Overview Generation Section
        enable_audio_overview = st.checkbox("Enable Audio Overview Generation")

        if enable_audio_overview:
            # Generate Audio Overview Section
            st.write("### Audio Overview Generation")

            if st.button("Generate Audio Overview"):
                try:
                    # Generate conversational script
                    st.write("Generating conversational script...")
                    script = content_generator.generate_conversation_script(combined_text)

                    # Save script to file
                    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    script_filename = os.path.join(SCRIPT_FILE_PATH, f"{timestamp}_conversation_script.txt")
                    os.makedirs(SCRIPT_FILE_PATH, exist_ok=True)
                    with open(script_filename, 'w', encoding='utf-8') as f:
                        f.write(script)

                    # Convert script to audio
                    st.write("Converting script to audio...")
                    os.makedirs(AUDIO_FILE_PATH, exist_ok=True)
                    audio_output_path = os.path.join(AUDIO_FILE_PATH, f"{timestamp}_audio_overview.mp3")
                    asyncio.run(convert_script_to_audio(
                        script_text=script,
                        output_audio_file=audio_output_path,
                        intro_music_path=INTRO_MUSIC_PATH,
                        outro_music_path=OUTRO_MUSIC_PATH
                    ))

                    # Play the audio file
                    with open(audio_output_path, "rb") as audio_file:
                        st.audio(audio_file.read(), format="audio/mp3")
                    st.success("Audio overview created successfully!")
                except NotImplementedError:
                    st.error("Audio generation is not supported by the current LLM provider.")

# Footer
with st.container():
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center;">
            <p>Created by <a href="https://jackhui.com.au" target="_blank">Jack Hui</a></p>
            <p>Follow me on:
                <p>
                <a href="https://twitter.com/realjackhui" target="_blank">
                    <img src="https://img.icons8.com/color/48/000000/twitter--v1.png" alt="Twitter" style="width: 30px; height: 30px;"/>
                </a>
                <a href="https://github.com/jack-jackhui" target="_blank">
                    <img src="https://img.icons8.com/color/48/000000/github.png" alt="Github" style="width: 30px; height: 30px;"/>
                </a>
                <a href="https://linkedin.com/in/jackhui888" target="_blank">
                    <img src="https://img.icons8.com/color/48/000000/linkedin.png" alt="LinkedIn" style="width: 30px; height: 30px;"/>
                </a>
            </p>
            </p>
        </div>
        """, unsafe_allow_html=True
    )
