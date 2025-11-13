from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Dict, List, Any

from transformers import pipeline


DEFAULT_MODEL = "sshleifer/distilbart-cnn-12-6"
# Alternatives:
# - "t5-small" (even lighter, shorter summaries)
# - "philschmid/bart-large-cnn-samsum" (higher quality, heavier)


@dataclass
class SummarizationConfig:
	model_name: str = DEFAULT_MODEL
	max_length: int = 140
	min_length: int = 30
	no_repeat_ngram_size: int = 3
	do_sample: bool = False


def _load_pipeline(model_name: str):
	return pipeline(
		"summarization",
		model=model_name,
		tokenizer=model_name,
		device=-1,
	)


@lru_cache(maxsize=2)
def _get_pipeline(model_name: str):
	return _load_pipeline(model_name)


def summarize_text(text: str, config: Optional[SummarizationConfig] = None) -> str:
	"""
	Generate summary from text (original function for backward compatibility).
	
	Args:
		text: Input text to summarize
		config: Optional summarization configuration
		
	Returns:
		Summary text string
	"""
	if not text or not text.strip():
		return ""
	if config is None:
		config = SummarizationConfig()

	pipe = _get_pipeline(config.model_name)

	max_chars = 3000
	chunks: list[str] = []
	cur = 0
	while cur < len(text):
		chunks.append(text[cur:cur + max_chars])
		cur += max_chars

	summaries: list[str] = []
	for chunk in chunks:
		out = pipe(
			chunk,
			max_length=config.max_length,
			min_length=config.min_length,
			no_repeat_ngram_size=config.no_repeat_ngram_size,
			do_sample=config.do_sample,
		)
		if out and isinstance(out, list) and 'summary_text' in out[0]:
			summaries.append(out[0]['summary_text'])

	if len(summaries) > 1:
		joined = "\n".join(summaries)
		out2 = pipe(joined, max_length=160, min_length=40)
		if out2 and isinstance(out2, list) and 'summary_text' in out2[0]:
			return out2[0]['summary_text']

	return summaries[0] if summaries else ""


def process_transcript(transcript: str, config: Optional[SummarizationConfig] = None) -> Dict[str, Any]:
	"""
	Process transcript and return structured output with all features.
	
	This function generates:
	- Summary
	- Action Items
	- Highlights
	- Topics
	
	Args:
		transcript: The full transcript text
		config: Optional summarization configuration
		
	Returns:
		Dictionary with keys: summary, action_items, highlights, topics
	"""
	from .action_items import extract_action_items
	from .highlights import extract_highlights as extract_highlights_func
	from .topics import extract_topics
	
	# Generate summary
	summary = summarize_text(transcript, config)
	
	# Extract action items
	action_items = extract_action_items(transcript)
	
	# Extract highlights
	highlights = extract_highlights_func(transcript)
	
	# Extract topics
	topics = extract_topics(transcript)
	
	return {
		"summary": summary,
		"action_items": action_items,
		"highlights": highlights,
		"topics": topics
	}
