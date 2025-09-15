from __future__ import annotations

import argparse
import re
from pathlib import Path

from .audio import convert_to_wav_mono_16k
from .stt import transcribe_wav

HIGHLIGHT_KEYWORDS = [
	# Finance / growth / metrics
	"revenue", "profit", "growth", "market", "sales", "cost", "margin", "roi", "funding",
	"budget", "forecast", "pipeline", "customers", "users", "churn", "retention", "mrr", "arr",
	"deal", "contract", "invoice", "pricing", "price", "expansion", "hiring", "headcount",
]


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


def _extract_important_sentences(transcript: str) -> list[str]:
	# Simple sentence split
	sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", transcript) if s.strip()]
	match_lower = [kw.lower() for kw in HIGHLIGHT_KEYWORDS]
	return [s for s in sentences if any(kw in s.lower() for kw in match_lower)]


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
		transcript = transcribe_wav(wav_path)
		basename = input_path.stem
		# Save transcript unless important-only is requested
		if not args.important_only:
			transcript_path = outdir / f"{basename}_transcript.txt"
			transcript_path.write_text(transcript, encoding="utf-8")
			print(f"Transcript written to: {transcript_path}")

	if args.important_only:
		important = _extract_important_sentences(transcript)
		(outdir / f"{basename}_important.txt").write_text("\n".join(important), encoding="utf-8")
		print(f"Important-only written to: {outdir / f'{basename}_important.txt'}")
		return

	# Highlights (line-based for transcripts that already contain line breaks)
	highlights = _extract_highlights(transcript)
	if highlights:
		(outdir / f"{basename}_highlights.txt").write_text("\n".join(highlights), encoding="utf-8")
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
