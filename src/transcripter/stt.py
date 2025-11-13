from __future__ import annotations

import json
import os
<<<<<<< HEAD
import sys
import tarfile
import time
from pathlib import Path
from typing import Iterable, Optional, TextIO
=======
import tarfile
from pathlib import Path
from typing import Iterable, Optional
>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6

import requests
from vosk import KaldiRecognizer, Model
import soundfile as sf

<<<<<<< HEAD
# Vosk model URLs for different languages
VOSK_MODELS = {
	"en": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
	"hi": "https://alphacephei.com/vosk/models/vosk-model-hi-0.22.zip",
}

# Default language
DEFAULT_LANGUAGE = "en"

VOSK_MODEL_URL = os.environ.get(
	"VOSK_MODEL_URL",
	VOSK_MODELS.get(DEFAULT_LANGUAGE, VOSK_MODELS["en"]),
)


def _download_and_extract_vosk_model(models_dir: Path, model_url: str) -> Path:
	"""
	Download and extract a Vosk model from URL.
	
	Args:
		models_dir: Directory to store models
		model_url: URL of the model zip file
		
	Returns:
		Path to the extracted model directory
	"""
	models_dir.mkdir(parents=True, exist_ok=True)
	# Determine target folder name from URL
	model_archive = models_dir / Path(model_url).name
	model_dir_name = model_archive.stem.replace(".zip", "")
	model_dir = models_dir / model_dir_name
	
	if model_dir.exists():
		return model_dir

	print(f"Downloading Vosk model from {model_url}...")
	# Stream download
	r = requests.get(model_url, stream=True, timeout=300)  # Longer timeout for large files
	r.raise_for_status()
	
	total_size = int(r.headers.get('content-length', 0))
	downloaded = 0
	
	with open(model_archive, "wb") as f:
		for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
			if chunk:
				f.write(chunk)
				downloaded += len(chunk)
				if total_size > 0:
					progress = (downloaded / total_size) * 100
					sys.stderr.write(f"\rDownloading model: {progress:.1f}% ({downloaded//1024//1024}MB/{total_size//1024//1024}MB)")
					sys.stderr.flush()
	
	if total_size > 0:
		sys.stderr.write("\n")
		sys.stderr.flush()
	
	print("Extracting model...")
=======
VOSK_MODEL_URL = os.environ.get(
	"VOSK_MODEL_URL",
	"https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
)


def _download_and_extract_vosk_model(models_dir: Path) -> Path:
	models_dir.mkdir(parents=True, exist_ok=True)
	# Determine target folder name from URL
	model_archive = models_dir / Path(VOSK_MODEL_URL).name
	model_dir_name = model_archive.stem.replace(".zip", "")
	model_dir = models_dir / model_dir_name
	if model_dir.exists():
		return model_dir

	# Stream download
	r = requests.get(VOSK_MODEL_URL, stream=True, timeout=60)
	r.raise_for_status()
	with open(model_archive, "wb") as f:
		for chunk in r.iter_content(chunk_size=1024 * 1024):
			if chunk:
				f.write(chunk)

>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6
	# Extract zip
	import zipfile
	with zipfile.ZipFile(model_archive, 'r') as zf:
		zf.extractall(models_dir)
<<<<<<< HEAD
	
	# Clean up archive to save space (optional)
	# model_archive.unlink()
	
	print(f"Model ready at: {model_dir}")
	return model_dir


def load_vosk_model(models_dir: str | Path = "models", language: str = "en") -> Model:
	"""
	Load a Vosk model for the specified language.
	
	Args:
		models_dir: Directory where models are stored
		language: Language code ('en' for English, 'hi' for Hindi)
		
	Returns:
		Loaded Vosk Model
	"""
	models_path = Path(models_dir)
	
	# Get model URL for the language
	if language not in VOSK_MODELS:
		raise ValueError(f"Unsupported language: {language}. Supported: {list(VOSK_MODELS.keys())}")
	
	model_url = VOSK_MODELS[language]
	model_dir = _download_and_extract_vosk_model(models_path, model_url)
	return Model(str(model_dir))


def transcribe_wav(path_wav: str | Path, model: Optional[Model] = None, language: str = "en") -> str:
	"""
	Transcribe a mono 16kHz WAV file using Vosk.
	Returns the transcript string.
	
	Args:
		path_wav: Path to WAV file
		model: Optional pre-loaded Vosk model
		language: Language code ('en' for English, 'hi' for Hindi)
	
	Note: For better efficiency with long files, use transcribe_wav_streaming() instead.
	"""
	if model is None:
		model = load_vosk_model(language=language)
=======

	return model_dir


def load_vosk_model(models_dir: str | Path = "models") -> Model:
	models_path = Path(models_dir)
	model_dir = _download_and_extract_vosk_model(models_path)
	return Model(str(model_dir))


def transcribe_wav(path_wav: str | Path, model: Optional[Model] = None) -> str:
	"""
	Transcribe a mono 16kHz WAV file using Vosk.
	Returns the transcript string.
	"""
	if model is None:
		model = load_vosk_model()
>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6

	# Read audio
	data, samplerate = sf.read(str(path_wav), dtype='int16')
	if samplerate != 16000:
		raise ValueError("WAV must be 16kHz. Use audio.convert_to_wav_mono_16k first.")

	rec = KaldiRecognizer(model, samplerate)
	rec.SetWords(True)

	# Vosk expects bytes
	byte_data = data.tobytes()
	chunk_size = 4000 * 2  # approx 0.25s per chunk for 16k mono s16le
	offset = 0
	results: list[str] = []
	while offset < len(byte_data):
		chunk = byte_data[offset:offset + chunk_size]
		offset += chunk_size
		if rec.AcceptWaveform(chunk):
			res = json.loads(rec.Result())
			if 'text' in res:
				results.append(res['text'])
	# Final bits
	final_res = json.loads(rec.FinalResult())
	if 'text' in final_res:
		results.append(final_res['text'])

	transcript = ' '.join(s.strip() for s in results if s.strip())
	return transcript.strip()
<<<<<<< HEAD


def transcribe_wav_streaming(
	path_wav: str | Path,
	output_file: Optional[Path | TextIO] = None,
	model: Optional[Model] = None,
	show_progress: bool = True,
	include_timestamps: bool = False,
	chunk_size_bytes: int = 8000,  # ~0.5s chunks for better throughput
	language: str = "en",
) -> str:
	"""
	Efficiently transcribe a WAV file with streaming output and progress tracking.
	
	This function writes transcript incrementally to avoid memory issues with long files.
	
	Args:
		path_wav: Path to mono 16kHz WAV file
		output_file: Optional file path or file handle to write transcript incrementally.
			If None, still returns full transcript but uses less memory.
		model: Optional pre-loaded Vosk model
		show_progress: Whether to display progress updates
		include_timestamps: Whether to include timestamps in output
		chunk_size_bytes: Audio chunk size in bytes (larger = faster but less frequent updates)
		language: Language code ('en' for English, 'hi' for Hindi)
	
	Returns:
		Full transcript string
	"""
	if model is None:
		model = load_vosk_model(language=language)

	# Read audio file info first to calculate duration
	info = sf.info(str(path_wav))
	samplerate = info.samplerate
	duration_seconds = info.frames / samplerate if info.frames > 0 else 0
	
	if samplerate != 16000:
		raise ValueError("WAV must be 16kHz. Use audio.convert_to_wav_mono_16k first.")

	rec = KaldiRecognizer(model, samplerate)
	rec.SetWords(True)

	# Open output file if path provided
	file_handle: Optional[TextIO] = None
	close_file = False
	if output_file is not None:
		if isinstance(output_file, (str, Path)):
			file_handle = open(output_file, 'w', encoding='utf-8', buffering=8192)  # 8KB buffer
			close_file = True
		else:
			file_handle = output_file

	# Read and process audio in chunks
	data, _ = sf.read(str(path_wav), dtype='int16')
	byte_data = data.tobytes()
	total_bytes = len(byte_data)
	offset = 0
	
	results: list[str] = []
	start_time = time.time()
	last_update_time = start_time
	
	try:
		while offset < total_bytes:
			chunk = byte_data[offset:offset + chunk_size_bytes]
			offset += chunk_size_bytes
			
			if rec.AcceptWaveform(chunk):
				res = json.loads(rec.Result())
				if 'text' in res and res['text'].strip():
					text = res['text'].strip()
					results.append(text)
					
					# Write immediately to file if streaming
					if file_handle is not None:
						if include_timestamps:
							# Vosk returns word-level timestamps in 'result' array when SetWords(True)
							words = res.get('result', [])
							if words and isinstance(words, list) and len(words) > 0:
								# Get start time of first word in this segment
								start = words[0].get('start', 0)
								file_handle.write(f"[{start:.2f}s] {text}\n")
							else:
								# Fallback: estimate based on audio position
								approx_time = (offset / total_bytes) * duration_seconds if duration_seconds > 0 else 0
								file_handle.write(f"[{approx_time:.2f}s] {text}\n")
						else:
							file_handle.write(f"{text}\n")
						file_handle.flush()  # Ensure data is written
					
					# Progress updates (every 2 seconds or at milestones)
					if show_progress:
						current_time = time.time()
						if current_time - last_update_time >= 2.0 or offset >= total_bytes:
							progress_pct = min(100, (offset / total_bytes) * 100)
							elapsed = current_time - start_time
							if progress_pct > 0:
								estimated_total = elapsed / (progress_pct / 100)
								remaining = estimated_total - elapsed
								sys.stderr.write(
									f"\rTranscribing: {progress_pct:.1f}% "
									f"({offset//1024//1024}MB/{total_bytes//1024//1024}MB) "
									f"ETA: {remaining:.0f}s    "
								)
								sys.stderr.flush()
							last_update_time = current_time
		
		# Final result
		final_res = json.loads(rec.FinalResult())
		if 'text' in final_res and final_res['text'].strip():
			text = final_res['text'].strip()
			results.append(text)
			if file_handle is not None:
				if include_timestamps:
					# Approximate final timestamp
					approx_time = duration_seconds
					file_handle.write(f"[{approx_time:.2f}s] {text}\n")
				else:
					file_handle.write(f"{text}\n")
				file_handle.flush()
		
		if show_progress:
			sys.stderr.write(f"\rTranscribing: 100% Complete! ({time.time() - start_time:.1f}s)    \n")
			sys.stderr.flush()
	
	finally:
		if close_file and file_handle is not None:
			file_handle.close()

	# Return full transcript
	transcript = ' '.join(s.strip() for s in results if s.strip())
	return transcript.strip()
=======
>>>>>>> 67535f896f9f9fbbe51cffa3b8a683a0dd025bc6
