from __future__ import annotations

import os
import wave
from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile

from pydub import AudioSegment
from vosk import KaldiRecognizer, Model


MODEL_PATH = Path(
	os.environ.get("VOSK_MODEL_PATH", "models/vosk-model-small-en-us-0.15")
)


class TranscriptionError(RuntimeError):
	"""Raised when audio transcription fails."""


def _ensure_model_path() -> Path:
	if not MODEL_PATH.exists():
		raise FileNotFoundError(
			f"Vosk model not found at '{MODEL_PATH}'. "
			"Download a model and update VOSK_MODEL_PATH if necessary."
		)
	return MODEL_PATH


@lru_cache(maxsize=1)
def _load_model() -> Model:
	model_path = _ensure_model_path()
	return Model(str(model_path))


def _convert_to_wav(source: Path) -> Path:
	try:
		audio = AudioSegment.from_file(str(source))
	except Exception as exc:  # pragma: no cover - pydub provides detailed errors
		raise TranscriptionError(f"Unsupported or corrupted audio file: {exc}") from exc

	audio = audio.set_frame_rate(16000).set_channels(1)

	temp_file = NamedTemporaryFile(suffix=".wav", delete=False)
	temp_path = Path(temp_file.name)
	temp_file.close()
	audio.export(temp_path, format="wav")
	return temp_path


def transcribe_audio(file_path: str | Path) -> str:
	"""
	Transcribe a local audio file (mp3 or wav) using a local Vosk model.

	Args:
		file_path: Path to the audio file.

	Returns:
		Transcript string.

	Raises:
		FileNotFoundError: If the audio file does not exist.
		TranscriptionError: For invalid formats or processing failures.
	"""
	source_path = Path(file_path)
	if not source_path.exists():
		raise FileNotFoundError(f"Audio file not found: {source_path}")

	if source_path.suffix.lower() not in {".mp3", ".wav"}:
		raise TranscriptionError("Only .mp3 and .wav files are supported.")

	model = _load_model()

	temp_wav: Path | None = None
	try:
		if source_path.suffix.lower() != ".wav":
			temp_wav = _convert_to_wav(source_path)
			wav_path = temp_wav
		else:
			wav_path = source_path

		with wave.open(str(wav_path), "rb") as wf:
			if (
				wf.getnchannels() == 1
				and wf.getframerate() == 16000
				and wf.getsampwidth() == 2
			):
				return _run_recognizer(model, wf)

		temp_wav = _convert_to_wav(source_path)
		with wave.open(str(temp_wav), "rb") as converted:
			return _run_recognizer(model, converted)
	finally:
		if temp_wav and temp_wav.exists():
			temp_wav.unlink(missing_ok=True)


def _run_recognizer(model: Model, wf: wave.Wave_read) -> str:
	if wf.getsampwidth() != 2:
		raise TranscriptionError("Audio sample width must be 16-bit PCM.")

	rec = KaldiRecognizer(model, wf.getframerate())
	rec.SetWords(True)

	transcript_parts: list[str] = []
	while True:
		data = wf.readframes(4000)
		if len(data) == 0:
			break
		if rec.AcceptWaveform(data):
			result = rec.Result()
			text = _extract_text(result)
			if text:
				transcript_parts.append(text)

	final_text = _extract_text(rec.FinalResult())
	if final_text:
		transcript_parts.append(final_text)

	return " ".join(part.strip() for part in transcript_parts if part.strip()).strip()


def _extract_text(result: str) -> str:
	import json

	try:
		data = json.loads(result)
		return data.get("text", "")
	except json.JSONDecodeError:
		return ""

