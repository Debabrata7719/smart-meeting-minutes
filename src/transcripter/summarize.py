from __future__ import annotations

from dataclasses import dataclass
<<<<<<< HEAD
from functools import lru_cache
from typing import Optional

from transformers import pipeline
=======
from typing import Optional

from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6


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
<<<<<<< HEAD
	return pipeline(
=======
	pipe = pipeline(
>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6
		"summarization",
		model=model_name,
		tokenizer=model_name,
		device=-1,
	)
<<<<<<< HEAD


@lru_cache(maxsize=2)
def _get_pipeline(model_name: str):
	return _load_pipeline(model_name)
=======
	return pipe
>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6


def summarize_text(text: str, config: Optional[SummarizationConfig] = None) -> str:
	if not text or not text.strip():
		return ""
	if config is None:
		config = SummarizationConfig()

<<<<<<< HEAD
	pipe = _get_pipeline(config.model_name)
=======
	pipe = _load_pipeline(config.model_name)
>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6

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
