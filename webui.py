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
                        script = content_generator.generate_conversational_script(combined_text)
                        st.session_state['podcast_script'] = script
                        st.success("✅ Script generated! Review and edit below, then click 'Generate Audio from Script'.")
                    except NotImplementedError:
                        st.error("Script generation is not supported by the current LLM provider.")
                    except Exception as e:
                        st.error(f"Failed to generate script: {str(e)}")
            
            # Show script preview/editor if script exists
            if st.session_state.get('podcast_script'):
                st.write("### 📝 Script Preview & Editor")
                st.write("*Review the script below. You can edit it before generating audio.*")
                
                edited_script = st.text_area(
                    "Podcast Script",
                    value=st.session_state['podcast_script'],
                    height=400,
                    help="Edit the script if needed. Speaker format: 'Jack:' and 'Corr:' or '**Jack**:' and '**Corr**:'"
                )
                
                # Update session state if edited
                if edited_script != st.session_state['podcast_script']:
                    st.session_state['podcast_script'] = edited_script
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🎙️ Generate Audio from Script", key="gen_audio_from_script"):
                        script = st.session_state['podcast_script']
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
                            asyncio.run(convert_script_to_audio(
                                script_text=script,
                                output_audio_file=audio_output_path,
                                intro_music_path=INTRO_MUSIC_PATH,
                                outro_music_path=OUTRO_MUSIC_PATH
                            ))
                            
                            tracker.update(ProgressStage.FINALIZING, "Preparing audio file...")
                            if wait_for_file(audio_output_path):
                                tracker.complete("Audio generated successfully!")
                                st.audio(audio_output_path, format="audio/mpeg")
                                st.success("✅ Audio overview created successfully!")
                                
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
