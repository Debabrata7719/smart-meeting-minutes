from __future__ import annotations

import json
import os
import tarfile
from pathlib import Path
from typing import Iterable, Optional

import requests
from vosk import KaldiRecognizer, Model
import soundfile as sf

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

	# Extract zip
	import zipfile
	with zipfile.ZipFile(model_archive, 'r') as zf:
		zf.extractall(models_dir)

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
