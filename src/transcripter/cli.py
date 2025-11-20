from __future__ import annotations

import argparse
import re
from pathlib import Path

from .audio import convert_to_wav_mono_16k
from .stt import transcribe_wav, transcribe_wav_streaming

# Organized keyword categories for better structure
HIGHLIGHT_CATEGORIES: dict[str, list[str]] = {
	"Financial Metrics": [
		"revenue", "profit", "cost", "margin", "roi", "budget", "pricing", "price",
		"invoice", "mrr", "arr", "funding",
	],
	"Growth & Business": [
		"growth", "market", "sales", "expansion", "deal", "contract", "pipeline",
	],
	"Customer & Users": [
		"customers", "users", "churn", "retention",
	],
	"Planning & Forecasting": [
		"forecast",
	],
	"Operations & Team": [
		"hiring", "headcount",
	],
}

# Flatten all keywords for pattern matching
HIGHLIGHT_KEYWORDS = [kw for keywords in HIGHLIGHT_CATEGORIES.values() for kw in keywords]
_HIGHLIGHT_PATTERN = re.compile(
	rf"(?i)\b(?:{'|'.join(re.escape(kw) for kw in HIGHLIGHT_KEYWORDS)})\b"
)


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Transcribe an audio file offline (Vosk) and optionally summarize (Transformers).",
	)
	parser.add_argument(
		"input",
		help="Path to input audio file (.mp3/.wav/.mp4/etc) or existing transcript when --reuse-transcript",
	)
	parser.add_argument(
		"--outdir",
		type=str,
		default="outputs",
		help="Directory to write transcript and summary",
	)
	parser.add_argument(
		"--skip-summary",
		action="store_true",
		help="Only produce transcript, skip summarization",
	)
	parser.add_argument(
		"--reuse-transcript",
		action="store_true",
		help="Treat input as an existing transcript .txt and skip STT",
	)
	parser.add_argument(
		"--important-only",
		action="store_true",
		help="Only save sentences containing important keywords (money/growth/etc)",
	)
	parser.add_argument(
		"--no-streaming",
		action="store_false",
		dest="streaming",
		default=True,
		help="Disable streaming transcription (use original method). Streaming is enabled by default.",
	)
	parser.add_argument(
		"--no-progress",
		action="store_true",
		help="Disable progress updates during transcription",
	)
	parser.add_argument(
		"--timestamps",
		action="store_true",
		help="Include timestamps in transcript output when streaming writes to file",
	)
	parser.add_argument(
		"--language",
		type=str,
		choices=["en", "hi"],
		default="en",
		help="Language of the audio file (en=English, hi=Hindi). Default: en",
	)
	parser.add_argument(
		"--translate",
		action="store_true",
		help="Translate Hindi transcript to English (only works with --language hi)",
	)
	return parser


def _extract_highlights(transcript: str) -> str:
	"""
	Extract and structure highlights from transcript with full context.
	Captures important topics, decisions, and statements with surrounding context.
	"""
	if not transcript:
		return ""

	transcript = re.sub(r'\s+', ' ', transcript).strip()
	sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", transcript) if s.strip()]

	importance_indicators = [
		r'\b(?:decided|decision|agreed|agreement|approved|approval|announced|announcement)\b',
		r'\b(?:will|going to|plan to|need to|must|should)\b',
		r'\b(?:important|critical|key|major|significant|priority)\b',
		r'\b(?:deadline|due date|target|goal|objective)\b',
		r'\b\d+%|\$\d+|\d+\s*(?:million|billion|thousand|k|m|b)\b',
		r'\b(?:next week|next month|next quarter|by|before|after)\b',
	]
	importance_pattern = re.compile('|'.join(importance_indicators), re.IGNORECASE)

	categorized: dict[str, list[str]] = {cat: [] for cat in HIGHLIGHT_CATEGORIES.keys()}
	seen_highlights = set()

	for i, sentence in enumerate(sentences):
		if len(sentence) < 10:
			continue

		sentence_lower = sentence.lower()
		has_keyword = _HIGHLIGHT_PATTERN.search(sentence)
		has_importance = importance_pattern.search(sentence)

		if not (has_keyword or has_importance):
			continue

		context_parts = []
		if i > 0 and len(sentences[i - 1]) > 15:
			prev_sentence = sentences[i - 1].strip()
			if (
				len(prev_sentence) < 100
				or _HIGHLIGHT_PATTERN.search(prev_sentence)
				or importance_pattern.search(prev_sentence)
			):
				context_parts.append(prev_sentence)

		context_parts.append(sentence)

		if i < len(sentences) - 1 and len(sentences[i + 1]) > 15:
			next_sentence = sentences[i + 1].strip()
			if (
				len(next_sentence) < 100
				or _HIGHLIGHT_PATTERN.search(next_sentence)
				or importance_pattern.search(next_sentence)
			):
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
				if not highlight_text.endswith(('.', '!', '?')):
					highlight_text += '.'
				categorized[category].append(highlight_text)
				category_found = True
				break

		if not category_found and has_importance:
			categorized.setdefault("Key Decisions & Actions", [])
			if not highlight_text.endswith(('.', '!', '?')):
				highlight_text += '.'
			categorized["Key Decisions & Actions"].append(highlight_text)

	output_lines = []
	output_lines.append("=" * 70)
	output_lines.append("MEETING HIGHLIGHTS")
	output_lines.append("=" * 70)
	output_lines.append("")

	key_decisions = categorized.pop("Key Decisions & Actions", [])
	if key_decisions:
		output_lines.append("KEY DECISIONS & ACTIONS")
		output_lines.append("-" * 70)
		for i, item in enumerate(key_decisions, 1):
			output_lines.append(f"  {i}. {item}")
		output_lines.append("")

	for category, items in categorized.items():
		if items:
			output_lines.append(category.upper())
			output_lines.append("-" * 70)
			for i, item in enumerate(items, 1):
				output_lines.append(f"  {i}. {item}")
			output_lines.append("")

	total_highlights = len(key_decisions) + sum(len(items) for items in categorized.values())
	if total_highlights == 0:
		output_lines.append("No highlights found matching key business metrics.")
	else:
		output_lines.append("=" * 70)
		output_lines.append(f"Total Highlights: {total_highlights}")
		output_lines.append("=" * 70)

	return "\n".join(output_lines)


def _extract_important_sentences(transcript: str) -> list[str]:
	sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", transcript) if s.strip()]
	return [s for s in sentences if _HIGHLIGHT_PATTERN.search(s)]


def _save_text(path: Path, content: str) -> None:
	path.write_text(content, encoding="utf-8")
	print(f"Wrote: {path}")


def main() -> None:
	parser = build_parser()
	args = parser.parse_args()

	input_path = Path(args.input)
	outdir = Path(args.outdir)
	outdir.mkdir(parents=True, exist_ok=True)

	if args.reuse_transcript:
		transcript = input_path.read_text(encoding="utf-8")
		basename = input_path.stem.replace("_transcript", "")
	else:
		wav_path = convert_to_wav_mono_16k(str(input_path), outdir)
		basename = input_path.stem

		transcript_output_path = outdir / f"{basename}_transcript.txt"

		if args.streaming:
			lang_name = "Hindi" if args.language == "hi" else "English"
			print(f"Starting efficient streaming transcription ({lang_name})...")
			output_target = None if args.important_only else transcript_output_path
			transcript = transcribe_wav_streaming(
				wav_path,
				output_file=output_target,
				show_progress=not args.no_progress,
				include_timestamps=args.timestamps,
				language=args.language,
			)
			if output_target is None and not args.important_only:
				_save_text(transcript_output_path, transcript)
		else:
			transcript = transcribe_wav(wav_path, language=args.language)
			if not args.important_only:
				_save_text(transcript_output_path, transcript)

		if wav_path.exists():
			wav_path.unlink()

	if args.translate:
		if args.language != "hi":
			print("Warning: --translate only works with --language hi. Skipping translation.")
		else:
			print("Translating Hindi transcript to English...")
			from .translate import translate_hindi_to_english

				녕하세요

