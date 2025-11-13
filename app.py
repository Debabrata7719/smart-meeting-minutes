import streamlit as st
import tempfile
import os
from pathlib import Path
import re

from src.transcripter.audio import convert_to_wav_mono_16k
from src.transcripter.stt import transcribe_wav_streaming, transcribe_wav
from src.transcripter.summarize import summarize_text
from src.transcripter.translate import translate_hindi_to_english

# Page config
st.set_page_config(
    page_title="Smart Meeting Minutes",
    page_icon="🎙️",
    layout="wide"
)

# Import highlight extraction function from cli
HIGHLIGHT_CATEGORIES = {
	"Financial Metrics": [
		"revenue", "profit", "cost", "margin", "roi", "budget", "pricing", "price",
		"invoice", "mrr", "arr", "funding"
	],
	"Growth & Business": [
		"growth", "market", "sales", "expansion", "deal", "contract", "pipeline"
	],
	"Customer & Users": [
		"customers", "users", "churn", "retention"
	],
	"Planning & Forecasting": [
		"forecast"
	],
	"Operations & Team": [
		"hiring", "headcount"
	]
}

HIGHLIGHT_KEYWORDS = [kw for keywords in HIGHLIGHT_CATEGORIES.values() for kw in keywords]
_HIGHLIGHT_PATTERN = re.compile(
	rf"(?i)\b(?:{'|'.join(re.escape(kw) for kw in HIGHLIGHT_KEYWORDS)})\b"
)


def extract_highlights(transcript: str) -> str:
	"""Extract and structure highlights from transcript with full context."""
	if not transcript:
		return ""

	# Clean transcript
	transcript = re.sub(r'\s+', ' ', transcript).strip()
	
	# Split into sentences for better extraction
	sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", transcript) if s.strip()]
	
	# Patterns that indicate important statements
	importance_indicators = [
		r'\b(?:decided|decision|agreed|agreement|approved|approval|announced|announcement)\b',
		r'\b(?:will|going to|plan to|need to|must|should)\b',
		r'\b(?:important|critical|key|major|significant|priority)\b',
		r'\b(?:deadline|due date|target|goal|objective)\b',
		r'\b\d+%|\$\d+|\d+\s*(?:million|billion|thousand|k|m|b)\b',
		r'\b(?:next week|next month|next quarter|by|before|after)\b',
	]
	
	importance_pattern = re.compile('|'.join(importance_indicators), re.IGNORECASE)
	
	# Extract important topics with context
	categorized: dict[str, list[str]] = {cat: [] for cat in HIGHLIGHT_CATEGORIES.keys()}
	seen_highlights = set()
	
	# Process sentences with context window
	for i, sentence in enumerate(sentences):
		if not sentence or len(sentence) < 10:
			continue
		
		sentence_lower = sentence.lower()
		has_keyword = _HIGHLIGHT_PATTERN.search(sentence)
		has_importance = importance_pattern.search(sentence)
		
		if has_keyword or has_importance:
			# Build context: include previous and next sentence if available
			context_parts = []
			
			if i > 0 and len(sentences[i-1]) > 15:
				prev_sentence = sentences[i-1].strip()
				if (len(prev_sentence) < 100 or 
				    _HIGHLIGHT_PATTERN.search(prev_sentence) or
				    importance_pattern.search(prev_sentence)):
					context_parts.append(prev_sentence)
			
			context_parts.append(sentence)
			
			if i < len(sentences) - 1 and len(sentences[i+1]) > 15:
				next_sentence = sentences[i+1].strip()
				if (len(next_sentence) < 100 or 
				    _HIGHLIGHT_PATTERN.search(next_sentence) or
				    importance_pattern.search(next_sentence)):
					context_parts.append(next_sentence)
			
			highlight_text = ' '.join(context_parts)
			highlight_text = re.sub(r'\s+', ' ', highlight_text).strip()
			
			if len(highlight_text) > 500:
				highlight_text = sentence
			
			highlight_key = highlight_text.lower()[:100]
			if highlight_key in seen_highlights:
				continue
			seen_highlights.add(highlight_key)
			
			category_found = False
			for category, keywords in HIGHLIGHT_CATEGORIES.items():
				if any(kw.lower() in sentence_lower for kw in keywords):
					if not highlight_text[-1] in '.!?':
						highlight_text += '.'
					categorized[category].append(highlight_text)
					category_found = True
					break
			
			if not category_found and has_importance:
				if "Key Decisions & Actions" not in categorized:
					categorized["Key Decisions & Actions"] = []
				if not highlight_text[-1] in '.!?':
					highlight_text += '.'
				categorized["Key Decisions & Actions"].append(highlight_text)
	
	# Build structured output
	output_lines = []
	output_lines.append("=" * 70)
	output_lines.append("MEETING HIGHLIGHTS")
	output_lines.append("=" * 70)
	output_lines.append("")
	
	key_decisions_count = 0
	if "Key Decisions & Actions" in categorized:
		key_decisions_count = len(categorized["Key Decisions & Actions"])
	
	if key_decisions_count > 0:
		output_lines.append("KEY DECISIONS & ACTIONS")
		output_lines.append("-" * 70)
		for i, item in enumerate(categorized["Key Decisions & Actions"], 1):
			output_lines.append(f"  {i}. {item}")
		output_lines.append("")
		del categorized["Key Decisions & Actions"]
	
	for category, items in categorized.items():
		if items:
			output_lines.append(f"{category.upper()}")
			output_lines.append("-" * 70)
			for i, item in enumerate(items, 1):
				output_lines.append(f"  {i}. {item}")
			output_lines.append("")
	
	total_highlights = sum(len(items) for items in categorized.values()) + key_decisions_count
	
	if total_highlights == 0:
		output_lines.append("No highlights found matching key business metrics.")
		return "\n".join(output_lines)
	
	output_lines.append("=" * 70)
	output_lines.append(f"Total Highlights: {total_highlights}")
	output_lines.append("=" * 70)
	
	return "\n".join(output_lines)


def main():
	st.title("🎙️ Smart Meeting Minutes")
	st.markdown("Transform your meeting recordings into structured summaries and actionable highlights")
	
	# Sidebar for settings
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
					status_text.text("🔄 Converting audio to required format...")
					progress_bar.progress(10)
					
					wav_path = convert_to_wav_mono_16k(str(input_path), temp_path)
					
					# Step 2: Transcribe
					status_text.text(f"🎤 Transcribing audio ({'Hindi' if language == 'hi' else 'English'})...")
					progress_bar.progress(30)
					
					transcript = transcribe_wav_streaming(
						wav_path,
						output_file=None,
						show_progress=False,  # We'll handle progress in UI
						include_timestamps=False,
						language=language,
					)
					
					progress_bar.progress(70)
					status_text.text("✅ Transcription complete!")
					
					# Step 3: Translate if needed
					if translate and language == "hi":
						status_text.text("🌐 Translating Hindi to English...")
						transcript = translate_hindi_to_english(transcript)
						progress_bar.progress(80)
					elif translate and language != "hi":
						st.warning("Translation only works with Hindi audio. Skipping translation.")
					
					# Step 4: Extract highlights
					status_text.text("✨ Extracting highlights...")
					progress_bar.progress(85)
					highlights_text = extract_highlights(transcript)
					
					# Step 5: Generate summary
					summary_text = ""
					if not skip_summary:
						status_text.text("📝 Generating summary...")
						progress_bar.progress(90)
						summary_text = summarize_text(transcript)
					
					progress_bar.progress(100)
					status_text.text("✅ Processing complete!")
					
					# Clean up temporary audio file
					if wav_path.exists():
						wav_path.unlink()
					
					# Store results in session state
					st.session_state['transcript'] = transcript
					st.session_state['summary'] = summary_text
					st.session_state['highlights'] = highlights_text
					st.session_state['filename'] = Path(uploaded_file.name).stem
					
				except Exception as e:
					st.error(f"❌ Error processing file: {str(e)}")
					st.exception(e)
					return
		
		# Display results if available
		if 'summary' in st.session_state and 'highlights' in st.session_state:
			st.markdown("---")
			st.header("📊 Results")
			
			# Create tabs for different views
			tab1, tab2 = st.tabs(["📝 Summary", "✨ Highlights"])
			
			with tab1:
				if st.session_state['summary']:
					st.text_area(
						"Meeting Summary",
						value=st.session_state['summary'],
						height=300,
						disabled=True,
						label_visibility="collapsed"
					)
					
					# Download button for summary
					st.download_button(
						label="📥 Download Summary",
						data=st.session_state['summary'],
						file_name=f"{st.session_state['filename']}_summary.txt",
						mime="text/plain"
					)
				else:
					st.info("Summary was skipped. Enable it in settings to generate summaries.")
			
			with tab2:
				if st.session_state['highlights']:
					st.text_area(
						"Meeting Highlights",
						value=st.session_state['highlights'],
						height=400,
						disabled=True,
						label_visibility="collapsed"
					)
					
					# Download button for highlights
					st.download_button(
						label="📥 Download Highlights",
						data=st.session_state['highlights'],
						file_name=f"{st.session_state['filename']}_highlights.txt",
						mime="text/plain"
					)
			
			# Clear results button
			if st.button("🗑️ Clear Results", use_container_width=True):
				for key in ['transcript', 'summary', 'highlights', 'filename']:
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
		col1, col2, col3 = st.columns(3)
		with col1:
			st.markdown("### 🎯 Features")
			st.markdown("- Offline processing")
			st.markdown("- Multi-language support")
			st.markdown("- Smart highlights")
		
		with col2:
			st.markdown("### 📋 Outputs")
			st.markdown("- Meeting summary")
			st.markdown("- Categorized highlights")
			st.markdown("- Downloadable files")
		
		with col3:
			st.markdown("### 🔒 Privacy")
			st.markdown("- No API calls")
			st.markdown("- Local processing")
			st.markdown("- Your data stays private")


if __name__ == "__main__":
	main()

