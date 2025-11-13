import streamlit as st
import tempfile
import os
import sys
from pathlib import Path
import re

# Add the project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.transcripter.audio import convert_to_wav_mono_16k
from src.transcripter.stt import transcribe_wav_streaming, transcribe_wav
from src.transcripter.summarize import summarize_text, process_transcript
from src.transcripter.pdf_export import export_to_pdf

# Page config
st.set_page_config(
    page_title="Smart Meeting Minutes",
    page_icon="🎙️",
    layout="wide"
)

# Custom CSS for modern UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    st.markdown('<h1 class="main-header">🎙️ Smart Meeting Minutes</h1>', unsafe_allow_html=True)
    st.markdown("### Transform your meeting recordings into structured summaries and actionable insights")
    
    # Sidebar for video upload and settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        language = st.selectbox(
            "Language",
            ["en", "hi"],
            index=0,
            help="Select the language of your audio file"
        )
        
        translate = st.checkbox(
            "Translate to English",
            value=False,
            help="Translate Hindi transcript to English (only for Hindi audio)"
        )
        
        skip_summary = st.checkbox(
            "Skip Summary",
            value=False,
            help="Only generate highlights, skip summarization"
        )
        
        st.markdown("---")
        st.markdown("### 📋 Supported Formats")
        st.markdown("- Audio: MP3, WAV, M4A")
        st.markdown("- Video: MP4, AVI, MOV")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("All processing happens offline. No data is sent to external services.")
        st.markdown("**Optimized for 8GB RAM systems**")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload your meeting recording",
        type=["mp3", "wav", "mp4", "m4a", "avi", "mov"],
        help="Upload an audio or video file of your meeting"
    )
    
    if uploaded_file is not None:
        # Show file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.metric("File Size", f"{file_size_mb:.2f} MB")
        with col3:
            st.metric("Language", "Hindi" if language == "hi" else "English")
        
        # Process button
        if st.button("🚀 Process Meeting", type="primary", use_container_width=True):
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Save uploaded file
                input_path = temp_path / uploaded_file.name
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Step 1: Convert audio
                    status_text.text("🔄 Step 1/6: Converting audio to required format...")
                    progress_bar.progress(5)
                    
                    wav_path = convert_to_wav_mono_16k(str(input_path), temp_path)
                    
                    # Step 2: Transcribe
                    status_text.text(f"🎤 Step 2/6: Transcribing audio ({'Hindi' if language == 'hi' else 'English'})...")
                    progress_bar.progress(20)
                    
                    transcript = transcribe_wav_streaming(
                        wav_path,
                        output_file=None,
                        show_progress=False,
                        include_timestamps=False,
                        language=language,
                    )
                    
                    progress_bar.progress(40)
                    status_text.text("✅ Transcription complete!")
                    
                    # Step 3: Translate if needed
                    if translate and language == "hi":
                        status_text.text("🌐 Step 3/6: Translating Hindi to English...")
                        from src.transcripter.translate import translate_hindi_to_english
                        transcript = translate_hindi_to_english(transcript)
                        progress_bar.progress(50)
                    elif translate and language != "hi":
                        st.warning("Translation only works with Hindi audio. Skipping translation.")
                        progress_bar.progress(50)
                    else:
                        progress_bar.progress(50)
                    
                    # Step 4: Generate summary and extract features
                    if not skip_summary:
                        status_text.text("📝 Step 4/6: Generating summary...")
                        progress_bar.progress(55)
                        
                        # Use the new process_transcript function for all features
                        results = process_transcript(transcript)
                        
                        summary_text = results["summary"]
                        action_items = results["action_items"]
                        highlights = results["highlights"]
                        topics = results["topics"]
                    else:
                        # If skipping summary, still extract other features
                        status_text.text("📝 Step 4/6: Extracting features (skipping summary)...")
                        progress_bar.progress(55)
                        
                        from src.transcripter.action_items import extract_action_items
                        from src.transcripter.highlights import extract_highlights as extract_highlights_func
                        from src.transcripter.topics import extract_topics
                        
                        summary_text = ""
                        action_items = extract_action_items(transcript)
                        highlights = extract_highlights_func(transcript)
                        topics = extract_topics(transcript)
                    
                    # Step 5: Extract Action Items
                    status_text.text("✅ Step 5/6: Extracting action items...")
                    progress_bar.progress(80)
                    
                    # Step 6: Creating Highlights
                    status_text.text("✨ Step 6/6: Creating highlights...")
                    progress_bar.progress(90)
                    
                    # Step 7: Extracting Topics
                    status_text.text("🔑 Extracting topics...")
                    progress_bar.progress(95)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Processing complete!")
                    
                    # Clean up temporary audio file
                    if wav_path.exists():
                        wav_path.unlink()
                    
                    # Store results in session state
                    st.session_state['transcript'] = transcript
                    st.session_state['summary'] = summary_text
                    st.session_state['action_items'] = action_items
                    st.session_state['highlights'] = highlights
                    st.session_state['topics'] = topics
                    st.session_state['filename'] = Path(uploaded_file.name).stem
                    
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
                    st.exception(e)
                    return
        
        # Display results if available
        if 'summary' in st.session_state or 'action_items' in st.session_state:
            st.markdown("---")
            st.header("📊 Results")
            
            # Create tabs for different views
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📝 Summary", 
                "✅ Action Items", 
                "✨ Highlights", 
                "🔑 Topics",
                "📄 Full Report"
            ])
            
            with tab1:
                if st.session_state.get('summary'):
                    st.markdown("### Summary")
                    st.text_area(
                        "Meeting Summary",
                        value=st.session_state['summary'],
                        height=300,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                else:
                    st.info("Summary was skipped. Enable it in settings to generate summaries.")
            
            with tab2:
                if st.session_state.get('action_items'):
                    st.markdown("### Action Items")
                    action_items_text = "\n".join(st.session_state['action_items'])
                    st.text_area(
                        "Action Items",
                        value=action_items_text,
                        height=300,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                else:
                    st.info("No action items found in the transcript.")
            
            with tab3:
                if st.session_state.get('highlights'):
                    st.markdown("### Highlights")
                    highlights_text = "\n".join(st.session_state['highlights'])
                    st.text_area(
                        "Highlights",
                        value=highlights_text,
                        height=300,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                else:
                    st.info("No highlights found in the transcript.")
            
            with tab4:
                if st.session_state.get('topics'):
                    st.markdown("### Topics / Keywords")
                    topics_text = ", ".join(st.session_state['topics'])
                    st.markdown(f"**{topics_text}**")
                else:
                    st.info("No topics found in the transcript.")
            
            with tab5:
                st.markdown("### Full Meeting Report")
                
                # Display all sections
                if st.session_state.get('summary'):
                    st.markdown("#### 📝 Summary")
                    st.write(st.session_state['summary'])
                    st.markdown("---")
                
                if st.session_state.get('action_items'):
                    st.markdown("#### ✅ Action Items")
                    for item in st.session_state['action_items']:
                        st.write(item)
                    st.markdown("---")
                
                if st.session_state.get('highlights'):
                    st.markdown("#### ✨ Highlights")
                    for highlight in st.session_state['highlights']:
                        st.write(highlight)
                    st.markdown("---")
                
                if st.session_state.get('topics'):
                    st.markdown("#### 🔑 Topics")
                    st.write(", ".join(st.session_state['topics']))
            
            # Download buttons
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Download Summary
                if st.session_state.get('summary'):
                    st.download_button(
                        label="📥 Download Summary",
                        data=st.session_state['summary'],
                        file_name=f"{st.session_state['filename']}_summary.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            with col2:
                # Download Action Items
                if st.session_state.get('action_items'):
                    action_items_text = "\n".join(st.session_state['action_items'])
                    st.download_button(
                        label="📥 Download Action Items",
                        data=action_items_text,
                        file_name=f"{st.session_state['filename']}_action_items.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            with col3:
                # Download PDF
                try:
                    pdf_bytes = export_to_pdf(
                        summary=st.session_state.get('summary', ''),
                        action_items=st.session_state.get('action_items', []),
                        highlights=st.session_state.get('highlights', []),
                        topics=st.session_state.get('topics', [])
                    )
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"{st.session_state['filename']}_meeting_summary.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"PDF generation failed: {str(e)}")
                    st.info("Please install reportlab or fpdf2: pip install reportlab")
            
            # Clear results button
            if st.button("🗑️ Clear Results", use_container_width=True):
                for key in ['transcript', 'summary', 'action_items', 'highlights', 'topics', 'filename']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    else:
        # Show welcome message
        st.info("👆 Please upload a meeting recording to get started")
        
        # Show example usage
        with st.expander("ℹ️ How to use"):
            st.markdown("""
            1. **Upload** your meeting audio or video file
            2. **Select** the language (English or Hindi)
            3. **Choose** options (translation, skip summary)
            4. **Click** "Process Meeting" to start
            5. **View** and download your results
            
            **Supported formats:** MP3, WAV, MP4, M4A, AVI, MOV
            """)
        
        # Show features
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("### 🎯 Features")
            st.markdown("- Offline processing")
            st.markdown("- Multi-language support")
            st.markdown("- Smart highlights")
            st.markdown("- Action item extraction")
        
        with col2:
            st.markdown("### 📋 Outputs")
            st.markdown("- Meeting summary")
            st.markdown("- Action items")
            st.markdown("- Highlights")
            st.markdown("- Topics/Keywords")
        
        with col3:
            st.markdown("### 📄 Export")
            st.markdown("- Text downloads")
            st.markdown("- PDF reports")
            st.markdown("- Structured format")
        
        with col4:
            st.markdown("### 🔒 Privacy")
            st.markdown("- No API calls")
            st.markdown("- Local processing")
            st.markdown("- Your data stays private")
            st.markdown("- 8GB RAM optimized")


if __name__ == "__main__":
    main()
