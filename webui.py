import streamlit as st
import time
import os
from content_generation import create_content_generator
from content_extraction import extract_content_from_sources
from text_to_speech_conversion import convert_script_to_audio
from validation import validate_credentials
from datetime import datetime
import asyncio
from progress import ProgressTracker, ProgressStage
from errors import MyNotebookLMError
from settings import (
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

# Function to wait for the audio file to be fully written
def wait_for_file(file_path, timeout=20, interval=1):
    """
    Wait for a file to be written and accessible.
    :param file_path: Path of the file to wait for.
    :param timeout: Maximum time to wait (in seconds).
    :param interval: Interval between checks (in seconds).
    :return: True if file becomes available, False otherwise.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return True
        time.sleep(interval)
    return False

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
    uploaded_files = st.file_uploader("Upload your source files (PDF, Word, Text, PPT)", accept_multiple_files=True,
                                      type=["pdf", "docx", "txt", "pptx"])

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
                # Progress tracking UI
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(status):
                    status_text.text(f"{status.message}")
                    progress_bar.progress(int(min(status.percent, 100)))
                
                tracker = ProgressTracker(on_progress=update_progress)
                
                try:
                    tracker.start()
                    
                    # Generate conversational script
                    tracker.update(ProgressStage.GENERATING_SCRIPT, "Generating conversational script...")
                    try:
                        script = content_generator.generate_conversational_script(combined_text)
                    except NotImplementedError:
                        tracker.fail("Script generation not supported by current LLM provider")
                        st.error("Conversation script generation is not supported by the current LLM provider.")
                        raise

                    # Save script to file
                    tracker.update(ProgressStage.GENERATING_SCRIPT, "Saving script...")
                    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    script_filename = os.path.join(SCRIPT_FILE_PATH, f"{timestamp}_conversation_script.txt")
                    os.makedirs(SCRIPT_FILE_PATH, exist_ok=True)
                    with open(script_filename, 'w', encoding='utf-8') as f:
                        f.write(script)

                    # Convert script to audio
                    tracker.update(ProgressStage.GENERATING_AUDIO, "Converting script to audio (this may take a few minutes)...")
                    os.makedirs(AUDIO_FILE_PATH, exist_ok=True)
                    audio_output_path = os.path.join(AUDIO_FILE_PATH, f"{timestamp}_audio_overview.mp3")
                    asyncio.run(convert_script_to_audio(
                        script_text=script,
                        output_audio_file=audio_output_path,
                        intro_music_path=INTRO_MUSIC_PATH,
                        outro_music_path=OUTRO_MUSIC_PATH
                    ))

                    # Finalize
                    tracker.update(ProgressStage.FINALIZING, "Preparing audio file...")
                    if wait_for_file(audio_output_path):
                        tracker.complete("Audio overview created successfully!")
                        st.audio(audio_output_path, format="audio/mpeg")
                        st.success("✅ Audio overview created successfully!")
                        
                        # Offer transcript download
                        with open(script_filename, 'r') as f:
                            st.download_button(
                                label="📄 Download Transcript",
                                data=f.read(),
                                file_name=f"{timestamp}_transcript.txt",
                                mime="text/plain"
                            )
                    else:
                        tracker.fail("Audio file generation timed out")
                        st.error("Audio file generation took too long or failed. Please try again.")
                        
                except MyNotebookLMError as e:
                    tracker.fail(e.user_message())
                    st.error(f"❌ {e.user_message()}")
                except NotImplementedError as nie:
                    st.error(str(nie))
                except Exception as e:
                    tracker.fail(str(e))
                    st.error(f"❌ An unexpected error occurred: {str(e)}")

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
