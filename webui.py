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
    HOST_1_NAME,
    HOST_2_NAME,
)
from history import history_manager, create_session_entry
from seo import init_seo

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
    page_title="MyNotebookLM - Open Source AI Podcast Generator",
    page_icon="📊",
)

# Initialize SEO components
init_seo()

# Episode length configuration
EPISODE_LENGTH_OPTIONS = {
    "Auto": {"minutes": None, "word_count": None, "description": "Length determined by content"},
    "5 min": {"minutes": 5, "word_count": 750, "description": "~750 words, quick overview"},
    "15 min": {"minutes": 15, "word_count": 2250, "description": "~2,250 words, moderate depth"},
    "30 min": {"minutes": 30, "word_count": 4500, "description": "~4,500 words, detailed discussion"},
}


def estimate_audio_duration(text: str, words_per_minute: int = 150) -> float:
    """Estimate audio duration in minutes based on word count."""
    word_count = len(text.split())
    return word_count / words_per_minute


# Sidebar Configuration
with st.sidebar:
    st.header("Settings")

    st.subheader("Episode Length")
    episode_length = st.selectbox(
        "Target Duration",
        options=list(EPISODE_LENGTH_OPTIONS.keys()),
        index=0,
        help="Select target episode length. Auto lets the content determine length."
    )
    length_config = EPISODE_LENGTH_OPTIONS[episode_length]
    st.caption(length_config["description"])
    st.session_state['episode_length'] = episode_length
    st.session_state['target_word_count'] = length_config["word_count"]

    st.subheader("Podcast Host Names")
    host_1_name = st.text_input(
        "Host 1 Name",
        value=HOST_1_NAME,
        help="Name of the first podcast host (default from environment: HOST_1_NAME)"
    )
    host_2_name = st.text_input(
        "Host 2 Name",
        value=HOST_2_NAME,
        help="Name of the second podcast host (default from environment: HOST_2_NAME)"
    )
    # Store in session state for use throughout the app
    st.session_state['host_1_name'] = host_1_name
    st.session_state['host_2_name'] = host_2_name

    st.subheader("Custom Intro/Outro Audio")
    custom_intro = st.file_uploader(
        "Upload Intro Audio (optional)",
        type=["mp3", "wav"],
        key="custom_intro_upload",
        help="Optional intro music to prepend to the podcast"
    )
    custom_outro = st.file_uploader(
        "Upload Outro Audio (optional)",
        type=["mp3", "wav"],
        key="custom_outro_upload",
        help="Optional outro music to append to the podcast"
    )

    # Save uploaded files and store paths in session state
    if custom_intro:
        intro_save_path = os.path.join("./uploaded_files/", f"custom_intro_{custom_intro.name}")
        os.makedirs("./uploaded_files/", exist_ok=True)
        with open(intro_save_path, "wb") as f:
            f.write(custom_intro.getbuffer())
        st.session_state['custom_intro_path'] = intro_save_path
        st.success(f"Intro uploaded: {custom_intro.name}")
    else:
        st.session_state['custom_intro_path'] = None

    if custom_outro:
        outro_save_path = os.path.join("./uploaded_files/", f"custom_outro_{custom_outro.name}")
        os.makedirs("./uploaded_files/", exist_ok=True)
        with open(outro_save_path, "wb") as f:
            f.write(custom_outro.getbuffer())
        st.session_state['custom_outro_path'] = outro_save_path
        st.success(f"Outro uploaded: {custom_outro.name}")
    else:
        st.session_state['custom_outro_path'] = None

    # Session History
    st.subheader("Session History")
    sessions = history_manager.get_sessions(limit=10)
    if sessions:
        session_options = ["-- Select a session --"] + [s.display_name for s in sessions]
        selected_idx = st.selectbox(
            "Previous Sessions",
            range(len(session_options)),
            format_func=lambda i: session_options[i],
            key="history_select"
        )
        if selected_idx > 0:
            selected_session = sessions[selected_idx - 1]
            st.caption(f"Episode length: {selected_session.episode_length}")
            st.caption(f"Hosts: {selected_session.host_1_name} & {selected_session.host_2_name}")
            if st.button("Load Settings", key="load_session"):
                st.session_state['episode_length'] = selected_session.episode_length
                st.session_state['host_1_name'] = selected_session.host_1_name
                st.session_state['host_2_name'] = selected_session.host_2_name
                st.success("Settings loaded! Refresh to apply.")
    else:
        st.caption("No previous sessions")

# Main App Content

# Authenticate the user session
if REQUIRE_LOGIN and not validate_credentials():
    st.error("You need to be logged in to view this page.")
    login_url = FRONTENDURL  # Replace with your actual login page URL
    st.markdown(f"[Go to Login Page]({login_url})")
else:
    # Load LLM configuration
    content_generator = create_content_generator()  # Dynamically load the correct LLM provider

    # Input Source Selection
    st.write("### 📥 Add Your Content")
    input_tab1, input_tab2, input_tab3 = st.tabs(["📁 Upload Files", "🔗 URL / YouTube", "📝 Paste Text"])
    
    combined_text = None
    
    with input_tab1:
        # File Upload Section
        uploaded_files = st.file_uploader(
            "Upload your source files (PDF, Word, Text, PPT)", 
            accept_multiple_files=True,
            type=["pdf", "docx", "txt", "pptx"]
        )
        if uploaded_files:
            saved_files = [save_file(file) for file in uploaded_files]
            st.success(f"✅ {len(saved_files)} file(s) uploaded successfully!")
            with st.spinner("Extracting content..."):
                combined_text = extract_content_from_sources(saved_files)
            st.session_state['input_type'] = 'file'
            st.session_state['input_source'] = ', '.join([f.name for f in uploaded_files])
            st.success("Content extracted successfully.")
    
    with input_tab2:
        st.write("Enter a URL or YouTube link to extract content from:")
        url_input = st.text_input(
            "URL", 
            placeholder="https://example.com/article or https://youtube.com/watch?v=...",
            help="Supports web pages, YouTube videos (extracts transcript), and more"
        )
        if st.button("🔍 Extract from URL", key="extract_url"):
            if url_input:
                with st.spinner("Extracting content from URL..."):
                    try:
                        combined_text = extract_content_from_sources([url_input])
                        if combined_text:
                            st.success("✅ Content extracted successfully!")
                            st.session_state['combined_text'] = combined_text
                            st.session_state['input_type'] = 'url'
                            st.session_state['input_source'] = url_input
                        else:
                            st.error("Could not extract content from this URL.")
                    except Exception as e:
                        st.error(f"❌ Failed to extract content: {str(e)}")
            else:
                st.warning("Please enter a URL first.")
        
        # Retrieve from session state if available
        if 'combined_text' in st.session_state and not combined_text:
            combined_text = st.session_state.get('combined_text')
    
    with input_tab3:
        st.write("Paste your text content directly:")
        text_input = st.text_area(
            "Text Content",
            height=300,
            placeholder="Paste your article, notes, or any text content here...",
            help="You can paste any text content that you want to convert into a podcast"
        )
        if st.button("📝 Use This Text", key="use_text"):
            if text_input and len(text_input.strip()) > 50:
                combined_text = text_input.strip()
                st.session_state['combined_text'] = combined_text
                st.session_state['input_type'] = 'text'
                st.session_state['input_source'] = f"Pasted text ({len(combined_text)} chars)"
                st.success(f"✅ Text loaded ({len(combined_text)} characters)")
            elif text_input:
                st.warning("Please enter more text (at least 50 characters).")
            else:
                st.warning("Please enter some text first.")
        
        # Retrieve from session state if available
        if 'combined_text' in st.session_state and not combined_text:
            combined_text = st.session_state.get('combined_text')
    
    # Process content if available
    if combined_text:
        st.write("---")
        st.write(f"📄 **Content loaded:** {len(combined_text)} characters")

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

            # Script Generation Options
            col1, col2 = st.columns([3, 1])
            with col1:
                generate_script_btn = st.button("📝 Generate Script", key="gen_script", help="Generate podcast script first, then review before creating audio")
            with col2:
                direct_audio_btn = st.button("🎙️ Direct to Audio", key="direct_audio", help="Skip script preview, generate audio directly")
            
            # Script preview state
            if 'podcast_script' not in st.session_state:
                st.session_state['podcast_script'] = None
            
            # Generate Script Only (for preview)
            if generate_script_btn:
                with st.spinner("Generating conversational script..."):
                    try:
                        target_words = st.session_state.get('target_word_count')
                        script = content_generator.generate_conversational_script(
                            combined_text,
                            target_word_count=target_words
                        )
                        st.session_state['podcast_script'] = script
                        # Show length estimation
                        estimated_duration = estimate_audio_duration(script)
                        st.success(f"✅ Script generated! Estimated duration: ~{estimated_duration:.1f} minutes")
                        st.info("Review and edit below, then click 'Generate Audio from Script'.")
                    except NotImplementedError:
                        st.error("Script generation is not supported by the current LLM provider.")
                    except Exception as e:
                        st.error(f"Failed to generate script: {str(e)}")
            
            # Show script preview/editor if script exists
            if st.session_state.get('podcast_script'):
                st.write("### 📝 Script Preview & Editor")
                st.write("*Review the script below. You can edit it before generating audio.*")

                # Get configured host names
                h1_name = st.session_state.get('host_1_name', HOST_1_NAME)
                h2_name = st.session_state.get('host_2_name', HOST_2_NAME)

                edited_script = st.text_area(
                    "Podcast Script",
                    value=st.session_state['podcast_script'],
                    height=400,
                    help=f"Edit the script if needed. Speaker format: '{h1_name}:' and '{h2_name}:' or '**{h1_name}**:' and '**{h2_name}**:'"
                )

                # Update session state if edited
                if edited_script != st.session_state['podcast_script']:
                    st.session_state['podcast_script'] = edited_script

                # Download transcript before TTS (Task 5)
                st.download_button(
                    label="📄 Download Script as TXT",
                    data=edited_script,
                    file_name=f"podcast_script_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt",
                    mime="text/plain",
                    key="download_script_txt"
                )
                st.download_button(
                    label="📄 Download Script as Markdown",
                    data=edited_script,
                    file_name=f"podcast_script_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md",
                    mime="text/markdown",
                    key="download_script_md"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🎙️ Generate Audio from Script", key="gen_audio_from_script"):
                        script = st.session_state['podcast_script']
                        # Get configured host names for TTS
                        tts_host_1 = st.session_state.get('host_1_name', HOST_1_NAME)
                        tts_host_2 = st.session_state.get('host_2_name', HOST_2_NAME)
                        # Progress tracking UI
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        def update_progress(status):
                            status_text.text(f"{status.message}")
                            progress_bar.progress(int(min(status.percent, 100)))

                        tracker = ProgressTracker(on_progress=update_progress)

                        try:
                            tracker.start()
                            tracker.update(ProgressStage.GENERATING_AUDIO, "Converting script to audio (this may take a few minutes)...")

                            # Save script to file
                            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                            script_filename = os.path.join(SCRIPT_FILE_PATH, f"{timestamp}_conversation_script.txt")
                            os.makedirs(SCRIPT_FILE_PATH, exist_ok=True)
                            with open(script_filename, 'w', encoding='utf-8') as f:
                                f.write(script)

                            # Convert to audio
                            os.makedirs(AUDIO_FILE_PATH, exist_ok=True)
                            audio_output_path = os.path.join(AUDIO_FILE_PATH, f"{timestamp}_audio_overview.mp3")
                            # Use custom intro/outro if uploaded, else fall back to defaults
                            intro_path = st.session_state.get('custom_intro_path') or INTRO_MUSIC_PATH
                            outro_path = st.session_state.get('custom_outro_path') or OUTRO_MUSIC_PATH
                            tts_result = asyncio.run(convert_script_to_audio(
                                script_text=script,
                                output_audio_file=audio_output_path,
                                intro_music_path=intro_path,
                                outro_music_path=outro_path,
                                host_1_name=tts_host_1,
                                host_2_name=tts_host_2
                            ))

                            # Show TTS result summary if there were failures
                            if tts_result and tts_result.failed_segments:
                                st.warning(f"Audio generated with {tts_result.success_count} of {tts_result.total_segments} segments. "
                                          f"{tts_result.failure_count} segment(s) failed and were skipped.")
                                with st.expander("View failed segments"):
                                    st.text(tts_result.get_failure_summary())

                            tracker.update(ProgressStage.FINALIZING, "Preparing audio file...")
                            if wait_for_file(audio_output_path):
                                tracker.complete("Audio generated successfully!")
                                st.audio(audio_output_path, format="audio/mpeg")
                                st.success("✅ Audio overview created successfully!")

                                # Save session to history
                                session_entry = create_session_entry(
                                    input_source=st.session_state.get('input_source', 'Unknown'),
                                    input_type=st.session_state.get('input_type', 'unknown'),
                                    episode_length=st.session_state.get('episode_length', 'Auto'),
                                    host_1_name=tts_host_1,
                                    host_2_name=tts_host_2,
                                    script=script,
                                    audio_path=audio_output_path,
                                    script_path=script_filename,
                                    custom_intro=intro_path if intro_path != INTRO_MUSIC_PATH else None,
                                    custom_outro=outro_path if outro_path != OUTRO_MUSIC_PATH else None,
                                )
                                history_manager.save_session(session_entry)

                                with open(script_filename, 'r') as f:
                                    st.download_button(
                                        label="📄 Download Transcript",
                                        data=f.read(),
                                        file_name=f"{timestamp}_transcript.txt",
                                        mime="text/plain"
                                    )
                            else:
                                tracker.fail("Audio file generation timed out")
                                st.error("Audio generation failed. Please try again.")
                        except Exception as e:
                            tracker.fail(str(e))
                            st.error(f"❌ Error: {str(e)}")
                with col2:
                    if st.button("🗑️ Clear Script", key="clear_script"):
                        st.session_state['podcast_script'] = None
                        st.rerun()
            
            # Direct to Audio (skip preview)
            if direct_audio_btn:
                # Get configured host names for TTS
                tts_host_1 = st.session_state.get('host_1_name', HOST_1_NAME)
                tts_host_2 = st.session_state.get('host_2_name', HOST_2_NAME)
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
                        target_words = st.session_state.get('target_word_count')
                        script = content_generator.generate_conversational_script(
                            combined_text,
                            target_word_count=target_words
                        )
                        # Show length estimation
                        estimated_duration = estimate_audio_duration(script)
                        st.info(f"Script generated. Estimated duration: ~{estimated_duration:.1f} minutes")
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
                    # Use custom intro/outro if uploaded, else fall back to defaults
                    intro_path = st.session_state.get('custom_intro_path') or INTRO_MUSIC_PATH
                    outro_path = st.session_state.get('custom_outro_path') or OUTRO_MUSIC_PATH
                    tts_result = asyncio.run(convert_script_to_audio(
                        script_text=script,
                        output_audio_file=audio_output_path,
                        intro_music_path=intro_path,
                        outro_music_path=outro_path,
                        host_1_name=tts_host_1,
                        host_2_name=tts_host_2
                    ))

                    # Show TTS result summary if there were failures
                    if tts_result and tts_result.failed_segments:
                        st.warning(f"Audio generated with {tts_result.success_count} of {tts_result.total_segments} segments. "
                                  f"{tts_result.failure_count} segment(s) failed and were skipped.")
                        with st.expander("View failed segments"):
                            st.text(tts_result.get_failure_summary())

                    # Finalize
                    tracker.update(ProgressStage.FINALIZING, "Preparing audio file...")
                    if wait_for_file(audio_output_path):
                        tracker.complete("Audio overview created successfully!")
                        st.audio(audio_output_path, format="audio/mpeg")
                        st.success("✅ Audio overview created successfully!")

                        # Save session to history
                        session_entry = create_session_entry(
                            input_source=st.session_state.get('input_source', 'Unknown'),
                            input_type=st.session_state.get('input_type', 'unknown'),
                            episode_length=st.session_state.get('episode_length', 'Auto'),
                            host_1_name=tts_host_1,
                            host_2_name=tts_host_2,
                            script=script,
                            audio_path=audio_output_path,
                            script_path=script_filename,
                            custom_intro=intro_path if intro_path != INTRO_MUSIC_PATH else None,
                            custom_outro=outro_path if outro_path != OUTRO_MUSIC_PATH else None,
                        )
                        history_manager.save_session(session_entry)

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
