from __future__ import annotations

import argparse
import re
from pathlib import Path

from .audio import convert_to_wav_mono_16k
<<<<<<< HEAD
from .stt import transcribe_wav, transcribe_wav_streaming

# Organized keyword categories for better structure
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

# Flatten all keywords for pattern matching
HIGHLIGHT_KEYWORDS = [kw for keywords in HIGHLIGHT_CATEGORIES.values() for kw in keywords]
_HIGHLIGHT_PATTERN = re.compile(
	rf"(?i)\b(?:{'|'.join(re.escape(kw) for kw in HIGHLIGHT_KEYWORDS)})\b"
)
=======
from .stt import transcribe_wav

HIGHLIGHT_KEYWORDS = [
	# Finance / growth / metrics
	"revenue", "profit", "growth", "market", "sales", "cost", "margin", "roi", "funding",
	"budget", "forecast", "pipeline", "customers", "users", "churn", "retention", "mrr", "arr",
	"deal", "contract", "invoice", "pricing", "price", "expansion", "hiring", "headcount",
]
>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6


def build_parser() -> argparse.ArgumentParser:
	p = argparse.ArgumentParser(
		description="Transcribe an audio file offline (Vosk) and optionally summarize (Transformers).",
	)
	p.add_argument("input", help="Path to input audio file (.mp3/.wav/etc) or existing transcript when --reuse-transcript")
	p.add_argument(
		"--outdir",
		type=str,
		default="outputs",
		help="Directory to write transcript and summary",
	)
	p.add_argument(
		"--skip-summary",
		action="store_true",
		help="Only produce transcript, skip summarization",
	)
	p.add_argument(
		"--reuse-transcript",
		action="store_true",
		help="Treat input as an existing transcript .txt and skip STT",
	)
	p.add_argument(
		"--important-only",
		action="store_true",
		help="Only save sentences containing important keywords (money/growth/etc)",
	)
<<<<<<< HEAD
	p.add_argument(
		"--no-streaming",
		action="store_false",
		dest="streaming",
		default=True,
		help="Disable streaming transcription (use original method). Streaming is enabled by default.",
	)
	p.add_argument(
		"--no-progress",
		action="store_true",
		help="Disable progress updates during transcription",
	)
	p.add_argument(
		"--timestamps",
		action="store_true",
		help="Include timestamps in transcript output",
	)
	p.add_argument(
		"--language",
		type=str,
		choices=["en", "hi"],
		default="en",
		help="Language of the audio file (en=English, hi=Hindi). Default: en",
	)
	p.add_argument(
		"--translate",
		action="store_true",
		help="Translate Hindi transcript to English (only works with --language hi)",
	)
	return p


def _extract_highlights(transcript: str) -> str:
	"""
	Extract and structure highlights from transcript with full context.
	Captures important topics, decisions, and statements with surrounding context.
	"""
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
		r'\b\d+%|\$\d+|\d+\s*(?:million|billion|thousand|k|m|b)\b',  # Numbers, percentages, money
		r'\b(?:next week|next month|next quarter|by|before|after)\b',
	]
	
	# Combine all importance patterns
	importance_pattern = re.compile('|'.join(importance_indicators), re.IGNORECASE)
	
	# Extract important topics with context
	categorized: dict[str, list[str]] = {cat: [] for cat in HIGHLIGHT_CATEGORIES.keys()}
	seen_highlights = set()
	
	# Process sentences with context window
	for i, sentence in enumerate(sentences):
		if not sentence or len(sentence) < 10:  # Skip very short sentences
			continue
		
		sentence_lower = sentence.lower()
		
		# Check if sentence contains important keywords or indicators
		has_keyword = _HIGHLIGHT_PATTERN.search(sentence)
		has_importance = importance_pattern.search(sentence)
		
		if has_keyword or has_importance:
			# Build context: include previous and next sentence if available
			context_parts = []
			
			# Add previous sentence for context (if it exists and is relevant)
			if i > 0 and len(sentences[i-1]) > 15:
				prev_sentence = sentences[i-1].strip()
				# Only include if it seems related (shares keywords or is short)
				if (len(prev_sentence) < 100 or 
				    _HIGHLIGHT_PATTERN.search(prev_sentence) or
				    importance_pattern.search(prev_sentence)):
					context_parts.append(prev_sentence)
			
			# Add current sentence
			context_parts.append(sentence)
			
			# Add next sentence for context (if it exists and is relevant)
			if i < len(sentences) - 1 and len(sentences[i+1]) > 15:
				next_sentence = sentences[i+1].strip()
				# Only include if it seems related
				if (len(next_sentence) < 100 or 
				    _HIGHLIGHT_PATTERN.search(next_sentence) or
				    importance_pattern.search(next_sentence)):
					context_parts.append(next_sentence)
			
			# Combine context into a coherent highlight
			highlight_text = ' '.join(context_parts)
			highlight_text = re.sub(r'\s+', ' ', highlight_text).strip()
			
			# Skip if too long (probably not a focused highlight)
			if len(highlight_text) > 500:
				highlight_text = sentence  # Just use the main sentence
			
			# Skip duplicates
			highlight_key = highlight_text.lower()[:100]  # Use first 100 chars as key
			if highlight_key in seen_highlights:
				continue
			seen_highlights.add(highlight_key)
			
			# Categorize based on keywords
			category_found = False
			for category, keywords in HIGHLIGHT_CATEGORIES.items():
				if any(kw.lower() in sentence_lower for kw in keywords):
					# Ensure proper punctuation
					if not highlight_text[-1] in '.!?':
						highlight_text += '.'
					categorized[category].append(highlight_text)
					category_found = True
					break
			
			# If no specific category but has importance indicators, add to "Key Decisions & Actions"
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
	
	# Store key decisions count before deletion
	key_decisions_count = 0
	if "Key Decisions & Actions" in categorized:
		key_decisions_count = len(categorized["Key Decisions & Actions"])
	
	# Add "Key Decisions & Actions" first if it exists
	if key_decisions_count > 0:
		output_lines.append("KEY DECISIONS & ACTIONS")
		output_lines.append("-" * 70)
		for i, item in enumerate(categorized["Key Decisions & Actions"], 1):
			output_lines.append(f"  {i}. {item}")
		output_lines.append("")
		del categorized["Key Decisions & Actions"]
	
	# Add other categorized highlights
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
=======
	return p


def _extract_highlights(transcript: str) -> list[str]:
	lines = [ln.strip() for ln in transcript.splitlines() if ln.strip()]
	match_lower = [kw.lower() for kw in HIGHLIGHT_KEYWORDS]
	hits: list[str] = []
	for ln in lines:
		l = ln.lower()
		if any(kw in l for kw in match_lower):
			hits.append(ln)
	return hits
>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6


def _extract_important_sentences(transcript: str) -> list[str]:
	# Simple sentence split
	sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", transcript) if s.strip()]
<<<<<<< HEAD
	return [s for s in sentences if _HIGHLIGHT_PATTERN.search(s)]
=======
	match_lower = [kw.lower() for kw in HIGHLIGHT_KEYWORDS]
	return [s for s in sentences if any(kw in s.lower() for kw in match_lower)]
>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6


def main() -> None:
	parser = build_parser()
	args = parser.parse_args()

	input_path = Path(args.input)
	outdir = Path(args.outdir)
	outdir.mkdir(parents=True, exist_ok=True)

	transcript: str

	if args.reuse_transcript:
		# Input is path to existing transcript
		transcript = Path(input_path).read_text(encoding="utf-8")
		stem = input_path.stem.replace("_transcript", "")
		basename = stem
	else:
		wav_path = convert_to_wav_mono_16k(str(input_path), outdir)
<<<<<<< HEAD
		basename = input_path.stem
		
		# Use efficient streaming transcription if enabled
		if args.streaming and not args.important_only:
			lang_name = "Hindi" if args.language == "hi" else "English"
			print(f"Starting efficient streaming transcription ({lang_name})...")
			transcript = transcribe_wav_streaming(
				wav_path,
				output_file=None,  # Don't save transcript file
				show_progress=not args.no_progress,
				include_timestamps=args.timestamps,
				language=args.language,
			)
		else:
			# Fallback to original method (needed for important-only mode)
			transcript = transcribe_wav(wav_path, language=args.language)
			# Don't save transcript file
		
		# Delete the temporary audio file after transcription
		if wav_path.exists():
			wav_path.unlink()

	# Translation (if requested and language is Hindi)
	if args.translate and args.language == "hi":
		print("Translating Hindi transcript to English...")
		from .translate import translate_hindi_to_english
		translated = translate_hindi_to_english(transcript)
		# Don't save translated file, just use it for processing
		transcript = translated
	elif args.translate and args.language != "hi":
		print("Warning: --translate only works with --language hi. Skipping translation.")
=======
		transcript = transcribe_wav(wav_path)
		basename = input_path.stem
		# Save transcript unless important-only is requested
		if not args.important_only:
			transcript_path = outdir / f"{basename}_transcript.txt"
			transcript_path.write_text(transcript, encoding="utf-8")
			print(f"Transcript written to: {transcript_path}")
>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6

	if args.important_only:
		important = _extract_important_sentences(transcript)
		(outdir / f"{basename}_important.txt").write_text("\n".join(important), encoding="utf-8")
		print(f"Important-only written to: {outdir / f'{basename}_important.txt'}")
		return

<<<<<<< HEAD
	# Highlights (well-structured and categorized)
	highlights_text = _extract_highlights(transcript)
	if highlights_text.strip():
		(outdir / f"{basename}_highlights.txt").write_text(highlights_text, encoding="utf-8")
=======
	# Highlights (line-based for transcripts that already contain line breaks)
	highlights = _extract_highlights(transcript)
	if highlights:
		(outdir / f"{basename}_highlights.txt").write_text("\n".join(highlights), encoding="utf-8")
>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6
		print(f"Highlights written to: {outdir / f'{basename}_highlights.txt'}")

	# Summary
	summary_text = ""
	if not args.skip_summary:
		from .summarize import summarize_text  # lazy import
		summary_text = summarize_text(transcript)
		(outdir / f"{basename}_summary.txt").write_text(summary_text, encoding="utf-8")
		print(f"Summary written to: {outdir / f'{basename}_summary.txt'}")


if __name__ == "__main__":
	main()
