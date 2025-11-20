from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from transformers import pipeline


DEFAULT_MODEL = "t5-small"


class SummarizationError(RuntimeError):
	"""Raised when summarization fails."""


@lru_cache(maxsize=1)
def _get_pipeline(model_name: str = DEFAULT_MODEL):
	return pipeline("summarization", model=model_name, tokenizer=model_name, device=-1)


def _chunk_text(text: str, max_chars: int = 1500) -> Iterable[str]:
	text = text.strip()
	if not text:
		return []
	for i in range(0, len(text), max_chars):
		yield text[i : i + max_chars]


def summarize_text(text: str, *, model_name: str = DEFAULT_MODEL) -> str:
	"""
	Generate a local summary for the provided text.

	Args:
		text: Input text to summarize.
		model_name: Optional transformers model identifier.

	Returns:
		Summary string (may fall back to truncated text if summarizer fails).
	"""
	if not text or len(text.strip()) < 80:
		return text.strip()

	try:
		pipe = _get_pipeline(model_name)
	except Exception as exc:  # pragma: no cover
		raise SummarizationError(f"Failed to load summarization model: {exc}") from exc

	summaries: list[str] = []
	for chunk in _chunk_text(text):
		try:
			result = pipe(chunk, max_length=150, min_length=40, do_sample=False)
			if result and isinstance(result, list):
				summaries.append(result[0]["summary_text"])
		except Exception as exc:  # pragma: no cover - transformers-specific errors
			raise SummarizationError(f"Summarization failed: {exc}") from exc

	return " ".join(summaries).strip() if summaries else text[:500].strip()

