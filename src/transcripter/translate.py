from __future__ import annotations

from typing import Optional

try:
	from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
	TRANSFORMERS_AVAILABLE = True
except ImportError:
	TRANSFORMERS_AVAILABLE = False

# Open-source Hindi to English translation model
# Helsinki-NLP provides good quality offline translation models
DEFAULT_TRANSLATION_MODEL = "Helsinki-NLP/opus-mt-hi-en"

# Alternative models (if needed):
# - "ai4bharat/indictrans2-hi-en" (better for Indian context, but larger)
# - "facebook/mbart-large-50-many-to-many-mmt" (multilingual, very large)


def translate_hindi_to_english(
	text: str,
	model_name: Optional[str] = None,
	chunk_size: int = 500,
) -> str:
	"""
	Translate Hindi text to English using an offline open-source model.
	
	Args:
		text: Hindi text to translate
		model_name: Optional model name (defaults to Helsinki-NLP/opus-mt-hi-en)
		chunk_size: Maximum characters per chunk for translation (to avoid memory issues)
	
	Returns:
		Translated English text
	"""
	if not TRANSFORMERS_AVAILABLE:
		raise ImportError(
			"Transformers library is required for translation. "
			"Install it with: pip install transformers torch"
		)
	
	if not text or not text.strip():
		return ""
	
	if model_name is None:
		model_name = DEFAULT_TRANSLATION_MODEL
	
	print(f"Loading translation model: {model_name}...")
	print("(This may take a moment on first use)")
	
	# Load translation pipeline
	translator = pipeline(
		"translation",
		model=model_name,
		tokenizer=model_name,
		device=-1,  # Use CPU (-1), set to 0 for GPU if available
	)
	
	# Split long text into chunks to avoid memory issues
	chunks: list[str] = []
	current_chunk = ""
	
	# Simple sentence-based chunking
	sentences = text.split('. ')
	for sentence in sentences:
		if len(current_chunk) + len(sentence) < chunk_size:
			current_chunk += sentence + '. '
		else:
			if current_chunk:
				chunks.append(current_chunk.strip())
			current_chunk = sentence + '. '
	
	if current_chunk:
		chunks.append(current_chunk.strip())
	
	# Translate each chunk
	translated_chunks: list[str] = []
	print("Translating...")
	
	for i, chunk in enumerate(chunks):
		if not chunk.strip():
			continue
		
		try:
			result = translator(chunk, max_length=512)
			if result and isinstance(result, list) and len(result) > 0:
				translated_text = result[0].get('translation_text', '')
				if translated_text:
					translated_chunks.append(translated_text)
					print(f"Translated chunk {i+1}/{len(chunks)}")
		except Exception as e:
			print(f"Warning: Error translating chunk {i+1}: {e}")
			# Fallback: keep original text if translation fails
			translated_chunks.append(chunk)
	
	# Join translated chunks
	translated = ' '.join(translated_chunks)
	return translated.strip()


def is_hindi_text(text: str) -> bool:
	"""
	Simple heuristic to check if text contains Hindi characters.
	
	Args:
		text: Text to check
		
	Returns:
		True if text appears to contain Hindi characters
	"""
	# Hindi Unicode range: U+0900 to U+097F
	hindi_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
	total_chars = len([c for c in text if c.isalnum() or c.isspace()])
	
	if total_chars == 0:
		return False
	
	# If more than 30% of characters are Hindi, consider it Hindi text
	return (hindi_chars / total_chars) > 0.3 if total_chars > 0 else False

